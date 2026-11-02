"""Load one text-only HF model on one explicitly selected allocated GPU."""

from __future__ import annotations

import gc
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .config import ModelSpec
from .contracts import Generation, TaskInput, digest
from .prompts import SYSTEM, user_prompt

_PINNED_UUID: str | None = None


def pin_gpu(index: int = 0) -> str:
    global _PINNED_UUID
    if type(index) is not int or index < 0:
        raise ValueError("GPU index must be a nonnegative integer")
    uuid = subprocess.check_output(
        [
            "nvidia-smi",
            "-i",
            str(index),
            "--query-gpu=uuid",
            "--format=csv,noheader",
        ],
        text=True,
        timeout=10,
    ).strip()
    if not uuid.startswith("GPU-") or "\n" in uuid:
        raise ValueError(f"Could not uniquely resolve physical GPU {index}")
    torch = sys.modules.get("torch")
    if torch is not None and torch.cuda.is_initialized() and _PINNED_UUID != uuid:
        raise RuntimeError(
            "CUDA was initialized before GPU isolation; start a fresh process"
        )
    inherited = os.environ.get("CUDA_VISIBLE_DEVICES")
    if inherited is not None:
        permitted = False
        for selector in inherited.split(','):
            selector = selector.strip()
            if selector.isdecimal():
                permitted = permitted or int(selector) == index
            elif selector.startswith('GPU-'):
                permitted = permitted or uuid.startswith(selector)
            else:
                break  # Empty/invalid/-1/MIG masks do not authorize a full GPU.
        if not permitted:
            raise RuntimeError("Requested GPU is outside inherited CUDA_VISIBLE_DEVICES allocation")
    os.environ["CUDA_VISIBLE_DEVICES"] = uuid
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    _PINNED_UUID = uuid
    return uuid


def check_text_config(config: dict) -> None:
    forbidden = (
        "vision_config",
        "audio_config",
        "visual",
        "vision_tower",
        "audio_encoder",
        "image_token_id",
        "video_token_id",
        "audio_token_id",
        "multimodal_config",
    )
    if any(config.get(key) is not None for key in forbidden):
        raise ValueError("Multimodal/VLM checkpoint rejected: use a text-only CausalLM")
    architectures = config.get("architectures") or []
    if not architectures or not all(
        name.endswith("ForCausalLM") for name in architectures
    ):
        raise ValueError("Checkpoint must declare a text-only ForCausalLM architecture")


class TransformersBackend:
    def __init__(self, spec: ModelSpec):
        started = time.perf_counter()
        uuid = pin_gpu(spec.gpu_index)
        try:
            import torch
            from huggingface_hub import snapshot_download
            from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Install evaluation[local] in a CUDA-enabled environment"
            ) from exc
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError(f"Selected physical GPU {spec.gpu_index} must be the only visible CUDA device")
        torch.manual_seed(spec.seed)
        self.torch, self.spec = torch, spec
        resolved_revision = None
        if not Path(spec.model).is_dir():
            # Resolve moving refs before config/tokenizer/weights can diverge.
            snapshot = snapshot_download(
                spec.model,
                revision=spec.revision,
                allow_patterns=["config.json"],
                local_files_only=spec.local_files_only,
            )
            resolved_revision = Path(snapshot).name
        options = {
            "revision": resolved_revision or spec.revision,
            "local_files_only": spec.local_files_only,
            "trust_remote_code": False,
        }
        config = AutoConfig.from_pretrained(spec.model, **options)
        check_text_config(config.to_dict())
        self.tokenizer = AutoTokenizer.from_pretrained(spec.model, **options)
        self.model = AutoModelForCausalLM.from_pretrained(
            spec.model,
            config=config,
            dtype=getattr(torch, spec.dtype),
            device_map={"": 0},
            **options,
        ).eval()
        self.metadata = {
            "provider": "transformers",
            "model": spec.model,
            "resolved_revision": resolved_revision,
            "config_sha256": digest(config.to_json_string()),
            "physical_gpu_index": spec.gpu_index,
            "gpu_uuid": uuid,
            "logical_device": "cuda:0",
            "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
            "dtype": spec.dtype,
            "tensor_parallel_size": 1,
            "torch_version": getattr(torch, "__version__", None),
            "transformers_version": getattr(sys.modules.get("transformers"), "__version__", None),
            "gpu_memory_total_bytes": (
                torch.cuda.get_device_properties(0).total_memory
                if hasattr(torch.cuda, "get_device_properties") else None
            ),
            "load_seconds": time.perf_counter() - started,
            "chat_template_sha256": digest(
                json.dumps(self.tokenizer.chat_template, sort_keys=True)
            ),
        }

    def set_seed(self, seed: int) -> None:
        self.torch.manual_seed(seed)

    def generate(self, task: TaskInput) -> Generation:
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt(task)},
        ]
        if self.tokenizer.chat_template:
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=self.spec.enable_thinking,
            )
        else:
            text = SYSTEM + "\n\n" + user_prompt(task) + "\n\nJSON answer:\n"
        inputs = self.tokenizer(
            text, return_tensors="pt", add_special_tokens=False, truncation=False
        ).to("cuda:0")
        input_tokens = inputs["input_ids"].shape[-1]
        limit = min(
            self.spec.max_context_tokens,
            getattr(
                self.model.config,
                "max_position_embeddings",
                self.spec.max_context_tokens,
            ),
        )
        if input_tokens + self.spec.max_output_tokens > limit:
            return Generation(
                input_tokens=input_tokens,
                error=(
                    f"Context budget exceeded: {input_tokens} input + "
                    f"{self.spec.max_output_tokens} output > {limit}; evidence was not truncated"
                ),
            )
        options = {
            "max_new_tokens": self.spec.max_output_tokens,
            "do_sample": bool(self.spec.temperature and self.spec.temperature > 0),
            "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
        }
        if options["do_sample"]:
            options["temperature"] = self.spec.temperature
        with self.torch.inference_mode():
            generated = self.model.generate(**inputs, **options)
        ids = generated[0, input_tokens:]
        text = self.tokenizer.decode(ids, skip_special_tokens=True)
        eos = self.model.generation_config.eos_token_id
        eos_ids = set(eos if isinstance(eos, list) else [eos])
        truncated = (
            len(ids) >= self.spec.max_output_tokens and int(ids[-1]) not in eos_ids
        )
        return Generation(
            text=text,
            input_tokens=input_tokens,
            output_tokens=len(ids),
            resolved_model=self.spec.model,
            finish_reason="length" if truncated else "stop",
            error="Local output token limit reached" if truncated else None,
        )

    def close(self) -> None:
        self.model = None
        self.tokenizer = None
        gc.collect()
        self.torch.cuda.empty_cache()
