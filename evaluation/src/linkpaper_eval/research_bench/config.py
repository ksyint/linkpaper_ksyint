"""Text-only model registry, with no credentials or arbitrary request overrides."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

import yaml
from pydantic import Field, model_validator

from .contracts import StrictModel


class ModelSpec(StrictModel):
    provider: Literal[
        "openai", "anthropic", "gemini", "openai_compatible", "transformers", "abstain"
    ]
    model: str = ""
    modality: Literal["text"] = "text"
    base_url: str | None = None
    api_key_env: str | None = None
    api_version: str = "2023-06-01"
    max_output_tokens: int = Field(default=1024, ge=16)
    temperature: float | None = Field(default=None, ge=0, le=2)
    reasoning_effort: str | None = None
    timeout_s: float = Field(default=120, gt=0)
    retries: int = Field(default=2, ge=0, le=5)
    # Physical ordinal only. Local execution never uses device_map='auto'.
    gpu_index: Literal[6] = 6
    revision: str | None = None
    local_files_only: bool = False
    dtype: Literal["bfloat16", "float16", "float32"] = "bfloat16"
    max_context_tokens: int = Field(default=8192, ge=256)
    enable_thinking: bool = False
    seed: int = 20261022
    input_usd_per_million: float | None = Field(default=None, ge=0)
    output_usd_per_million: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_url(self) -> Self:
        if self.base_url:
            parsed = urlsplit(self.base_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("base_url must be an HTTP(S) endpoint")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError(
                    "base_url must not contain credentials, query parameters or fragments"
                )
        return self


class ExperimentConfig(StrictModel):
    schema_version: Literal[1] = 1
    modality: Literal["text"] = "text"
    models: dict[str, ModelSpec]
    seed: int = 20261022
    repeats: int = Field(default=1, ge=1)
    max_prompt_chars: int = Field(default=80000, gt=0)
    bootstrap_samples: int = Field(default=1000, ge=0)


def load_config(path: Path) -> ExperimentConfig:
    raw = path.read_text(encoding="utf-8")
    pattern = r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}"

    # Substitute scalar values after YAML parsing, never inject YAML syntax.
    def expand(value):
        if isinstance(value, str):
            return re.sub(pattern, lambda m: os.environ.get(m[1], m[2] or ""), value)
        if isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        if isinstance(value, list):
            return [expand(v) for v in value]
        return value

    return ExperimentConfig.model_validate(expand(yaml.safe_load(raw)))


def key_env(spec: ModelSpec) -> str:
    return (
        spec.api_key_env
        or {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "openai_compatible": "OPENAI_COMPATIBLE_API_KEY",
        }[spec.provider]
    )


def preflight(config: ExperimentConfig, names: list[str]) -> None:
    if not names or len(set(names)) != len(names):
        raise ValueError("Select at least one unique model alias with --models")
    for name in names:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            raise ValueError(f"Unsafe model alias: {name}")
        if name not in config.models:
            raise ValueError(f"Unknown model alias: {name}")
        spec = config.models[name]
        if spec.provider != "abstain" and not spec.model.strip():
            raise ValueError(
                f"{name}: set an explicit model ID in the config/environment"
            )
        if spec.provider not in {"transformers", "abstain"}:
            env = key_env(spec)
            if spec.provider != "openai_compatible" and not os.environ.get(env):
                raise ValueError(f"{name}: {env} is not set")
            if spec.provider == "openai_compatible" and not spec.base_url:
                raise ValueError(f"{name}: openai_compatible requires base_url")
