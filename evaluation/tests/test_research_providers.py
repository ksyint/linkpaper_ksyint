"""Native provider wire contracts; no credentials, paid calls or GPU required."""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace

import httpx
import pytest

from linkpaper_eval.research_bench.config import ModelSpec
from linkpaper_eval.research_bench.contracts import Context, TaskInput
from linkpaper_eval.research_bench.local import check_text_config, pin_gpu
from linkpaper_eval.research_bench.providers import APIBackend


def task():
    return TaskInput(
        task_id="HIDDEN_TASK_ID",
        question="Is this claim supported?",
        requested_conditions={"dataset": "Harbor"},
        contexts=[
            Context(
                citation_id="e-1",
                paper_id="paper",
                paper_version="v1",
                source_url="https://example.org/paper",
                text="Scientific text only.",
            )
        ],
    )


TEXT = json.dumps(
    {
        "verdict": "insufficient",
        "answer": "Missing comparison.",
        "conditions": {},
        "claims": [],
    }
)


@pytest.mark.parametrize(
    "provider,endpoint,reply",
    [
        (
            "openai",
            "/v1/responses",
            {
                "id": "response-id",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": TEXT}],
                    }
                ],
                "usage": {"input_tokens": 13, "output_tokens": 7},
            },
        ),
        (
            "anthropic",
            "/v1/messages",
            {
                "id": "message-id",
                "stop_reason": "end_turn",
                "content": [
                    {"type": "thinking", "thinking": "not the answer"},
                    {"type": "text", "text": TEXT},
                ],
                "usage": {"input_tokens": 13, "output_tokens": 7},
            },
        ),
        (
            "gemini",
            "/v1/models/model-id:generateContent",
            {
                "responseId": "gemini-id",
                "candidates": [
                    {
                        "finishReason": "STOP",
                        "content": {
                            "parts": [
                                {"thought": True, "text": "hidden reasoning"},
                                {"text": TEXT},
                            ]
                        },
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 13,
                    "candidatesTokenCount": 5,
                    "thoughtsTokenCount": 2,
                },
            },
        ),
        (
            "openai_compatible",
            "/v1/chat/completions",
            {
                "id": "chat-id",
                "choices": [{"finish_reason": "stop", "message": {"content": TEXT}}],
                "usage": {"prompt_tokens": 13, "completion_tokens": 7},
            },
        ),
    ],
)
def test_api_payloads_are_text_only_stateless_and_keep_native_usage(
    monkeypatch, provider, endpoint, reply
):
    monkeypatch.setenv("TEST_API_KEY", "test-secret")
    captured = []

    def handler(request):
        captured.append(request)
        return httpx.Response(200, json=reply)

    backend = APIBackend(
        ModelSpec(
            provider=provider,
            model="model-id",
            base_url="https://provider.test/v1",
            api_key_env="TEST_API_KEY",
        ),
        httpx.MockTransport(handler),
    )
    result = backend.generate(task())
    backend.close()
    assert result.error is None
    assert result.text == TEXT
    assert (result.input_tokens, result.output_tokens) == (13, 7)
    assert captured[0].url.path == endpoint
    body = json.loads(captured[0].content)
    assert "HIDDEN_TASK_ID" not in captured[0].content.decode()
    assert "test-secret" not in captured[0].content.decode()
    assert not (
        {"tools", "previous_response_id", "conversation", "files", "images"}
        & body.keys()
    )
    if provider == "openai":
        assert body["store"] is False
        assert isinstance(body["input"], str)
        assert "temperature" not in body
    if provider == "anthropic":
        assert captured[0].headers["anthropic-version"] == "2023-06-01"
        assert captured[0].headers["x-api-key"] == "test-secret"
    if provider == "gemini":
        assert captured[0].headers["x-goog-api-key"] == "test-secret"
        assert captured[0].url.query == b""
        assert set(body["contents"][0]["parts"][0]) == {"text"}


def test_http_failures_never_dump_credentials_or_provider_body(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-serialize")
    backend = APIBackend(
        ModelSpec(provider="openai", model="chosen", retries=0),
        httpx.MockTransport(
            lambda request: httpx.Response(401, text="do-not-serialize")
        ),
    )
    result = backend.generate(task())
    backend.close()
    assert result.error == "HTTP 401"
    assert "do-not-serialize" not in result.model_dump_json()


def test_transient_retry_is_bounded_and_does_not_repeat_success(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "linkpaper_eval.research_bench.providers.time.sleep", lambda delay: None
    )
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503)
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": TEXT}],
                    }
                ],
            },
        )

    backend = APIBackend(
        ModelSpec(provider="openai", model="chosen", retries=1),
        httpx.MockTransport(handler),
    )
    result = backend.generate(task())
    backend.close()
    assert result.error is None
    assert result.usage["attempts"] == len(calls) == 2


@pytest.mark.parametrize(
    "provider,reply",
    [
        (
            "openai",
            {
                "status": "incomplete",
                "output": [],
                "usage": {"input_tokens": 11, "output_tokens": 19},
            },
        ),
        (
            "anthropic",
            {
                "stop_reason": "max_tokens",
                "content": [{"type": "text", "text": TEXT}],
                "usage": {"input_tokens": 11, "output_tokens": 19},
            },
        ),
        (
            "gemini",
            {
                "candidates": [
                    {
                        "finishReason": "MAX_TOKENS",
                        "content": {"parts": [{"text": TEXT}]},
                    }
                ],
                "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 19},
            },
        ),
        (
            "openai_compatible",
            {
                "choices": [{"finish_reason": "length", "message": {"content": TEXT}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 19},
            },
        ),
    ],
)
def test_truncated_output_is_a_failure_even_if_partial_json_is_parseable(
    monkeypatch, provider, reply
):
    monkeypatch.setenv("TEST_KEY", "test-key")
    backend = APIBackend(
        ModelSpec(
            provider=provider,
            model="chosen",
            base_url="https://provider.test/v1",
            api_key_env="TEST_KEY",
        ),
        httpx.MockTransport(lambda request: httpx.Response(200, json=reply)),
    )
    result = backend.generate(task())
    backend.close()
    assert result.error is not None
    assert (result.input_tokens, result.output_tokens) == (11, 19)


@pytest.mark.parametrize(
    "configuration",
    [
        {"architectures": ["Qwen3VLForConditionalGeneration"], "vision_config": {}},
        {"architectures": ["FakeForCausalLM"], "vision_config": {}},
        {"architectures": ["FakeForCausalLM"], "audio_config": {}},
    ],
)
def test_local_multimodal_checkpoints_are_rejected(configuration):
    with pytest.raises(ValueError, match="Multimodal"):
        check_text_config(configuration)


def test_text_only_config_is_accepted():
    check_text_config({"architectures": ["Qwen3ForCausalLM"], "model_type": "qwen3"})


def test_physical_gpu_6_uuid_is_pinned_before_cuda_import(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0,1,2,3,4,5,6,7")
    monkeypatch.setattr("linkpaper_eval.research_bench.local._PINNED_UUID", None)
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda: False)),
    )
    calls = []

    def query(argv, **kwargs):
        calls.append(argv)
        return "GPU-authorized-six\n"

    monkeypatch.setattr(
        "linkpaper_eval.research_bench.local.subprocess.check_output", query
    )
    assert pin_gpu() == "GPU-authorized-six"
    import os

    assert os.environ["CUDA_VISIBLE_DEVICES"] == "GPU-authorized-six"
    assert calls[0][calls[0].index("-i") + 1] == "6"
    with pytest.raises(ValueError, match="Only physical GPU 6"):
        pin_gpu(5)


def test_preinitialized_cuda_cannot_be_reassigned_to_another_gpu(monkeypatch):
    monkeypatch.setattr("linkpaper_eval.research_bench.local._PINNED_UUID", None)
    monkeypatch.setitem(
        sys.modules,
        "torch",
        SimpleNamespace(cuda=SimpleNamespace(is_initialized=lambda: True)),
    )
    monkeypatch.setattr(
        "linkpaper_eval.research_bench.local.subprocess.check_output",
        lambda *a, **k: "GPU-six",
    )
    with pytest.raises(RuntimeError, match="fresh process"):
        pin_gpu()


def test_local_model_weights_load_automatically_on_only_the_pinned_device(monkeypatch):
    from linkpaper_eval.research_bench.local import TransformersBackend

    calls = []
    model = SimpleNamespace(eval=lambda: model)
    fake_config = SimpleNamespace(
        to_dict=lambda: {"architectures": ["TextForCausalLM"]},
        to_json_string=lambda: "{}",
    )
    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(
            is_initialized=lambda: False,
            is_available=lambda: True,
            device_count=lambda: 1,
            empty_cache=lambda: None,
        ),
        manual_seed=lambda seed: None,
        bfloat16="bf16",
    )

    def load_model(name, **kwargs):
        calls.append((name, kwargs))
        return model

    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(
            snapshot_download=lambda *a, **k: "/fake/snapshots/fixed-revision"
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoConfig=SimpleNamespace(from_pretrained=lambda *a, **k: fake_config),
            AutoTokenizer=SimpleNamespace(
                from_pretrained=lambda *a, **k: SimpleNamespace(
                    chat_template="template"
                )
            ),
            AutoModelForCausalLM=SimpleNamespace(from_pretrained=load_model),
        ),
    )
    monkeypatch.setattr("linkpaper_eval.research_bench.local._PINNED_UUID", None)
    monkeypatch.setattr(
        "linkpaper_eval.research_bench.local.subprocess.check_output",
        lambda *a, **k: "GPU-six",
    )
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "unused")
    backend = TransformersBackend(
        ModelSpec(provider="transformers", model="text-checkpoint", revision="pinned")
    )
    assert calls[0][0] == "text-checkpoint"
    assert calls[0][1]["device_map"] == {"": 0}
    assert calls[0][1]["trust_remote_code"] is False
    assert calls[0][1]["revision"] == "fixed-revision"
    assert backend.metadata["resolved_revision"] == "fixed-revision"
    assert backend.metadata["physical_gpu_index"] == 6
    assert backend.metadata["cuda_visible_devices"] == "GPU-six"
    backend.close()
    assert backend.model is None
