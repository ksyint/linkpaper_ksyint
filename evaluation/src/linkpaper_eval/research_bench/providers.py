"""Stateless text generation over native APIs or a compatible local endpoint.

Only an explicit, fixed set of text request fields is sent. No image/file/audio
inputs, tools, previous conversation IDs or arbitrary request overrides exist.
"""

from __future__ import annotations

import json
import os
import time
from typing import Protocol
from urllib.parse import quote

import httpx

from .config import ModelSpec, key_env
from .contracts import Generation, TaskInput
from .prompts import SYSTEM, user_prompt


class TextBackend(Protocol):
    metadata: dict

    def generate(self, task: TaskInput) -> Generation: ...

    def close(self) -> None: ...


class AbstainBackend:
    def __init__(self):
        self.metadata = {
            "provider": "abstain",
            "purpose": "degenerate diagnostic baseline",
        }

    def generate(self, task: TaskInput) -> Generation:
        return Generation(
            text=json.dumps(
                {
                    "verdict": "insufficient",
                    "answer": "Insufficient evidence.",
                    "conditions": {},
                    "claims": [],
                }
            ),
            input_tokens=0,
            output_tokens=0,
        )

    def close(self) -> None:
        pass


class APIBackend:
    def __init__(self, spec: ModelSpec, transport: httpx.BaseTransport | None = None):
        self.spec = spec
        provider = spec.provider
        defaults = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com/v1",
            "gemini": "https://generativelanguage.googleapis.com/v1beta",
        }
        base = spec.base_url or defaults.get(provider)
        if not base:
            raise ValueError("API endpoint required")
        env = key_env(spec)
        token = os.environ.get(env, "")
        if not token and provider != "openai_compatible":
            raise ValueError(f"{env} is not set")
        headers = {}
        if provider == "anthropic":
            headers = {"x-api-key": token, "anthropic-version": spec.api_version}
        elif provider == "gemini":
            headers = {"x-goog-api-key": token}
        elif token:
            headers = {"Authorization": f"Bearer {token}"}
        self.client = httpx.Client(
            base_url=base.rstrip("/") + "/",
            headers=headers,
            timeout=spec.timeout_s,
            transport=transport,
        )
        self.metadata = {
            "provider": provider,
            "model": spec.model,
            "base_url": base,
            "api_version": spec.api_version if provider == "anthropic" else None,
        }

    def _request(self, task: TaskInput) -> tuple[str, dict]:
        spec, text = self.spec, user_prompt(task)
        if spec.provider == "openai":
            body = {
                "model": spec.model,
                "instructions": SYSTEM,
                "input": text,
                "max_output_tokens": spec.max_output_tokens,
                "store": False,
            }
            if spec.temperature is not None:
                body["temperature"] = spec.temperature
            if spec.reasoning_effort is not None:
                body["reasoning"] = {"effort": spec.reasoning_effort}
            return "responses", body
        if spec.provider == "anthropic":
            body = {
                "model": spec.model,
                "system": SYSTEM,
                "max_tokens": spec.max_output_tokens,
                "messages": [{"role": "user", "content": text}],
            }
            if spec.temperature is not None:
                body["temperature"] = spec.temperature
            return "messages", body
        if spec.provider == "gemini":
            generation = {"maxOutputTokens": spec.max_output_tokens}
            if spec.temperature is not None:
                generation["temperature"] = spec.temperature
            return (
                f"models/{quote(spec.model.removeprefix('models/'), safe='')}:generateContent",
                {
                    "systemInstruction": {"parts": [{"text": SYSTEM}]},
                    "contents": [{"role": "user", "parts": [{"text": text}]}],
                    "generationConfig": generation,
                },
            )
        body = {
            "model": spec.model,
            "max_tokens": spec.max_output_tokens,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text},
            ],
        }
        if spec.temperature is not None:
            body["temperature"] = spec.temperature
        return "chat/completions", body

    def generate(self, task: TaskInput) -> Generation:
        path, body = self._request(task)
        attempts = 0
        for attempt in range(self.spec.retries + 1):
            attempts += 1
            try:
                response = self.client.post(path, json=body)
            except httpx.TransportError as exc:
                if attempt < self.spec.retries:
                    time.sleep(min(2**attempt, 4))
                    continue
                return Generation(
                    error=f"Transport error: {type(exc).__name__}",
                    usage={"attempts": attempts},
                )
            if (
                response.status_code in {429, 500, 502, 503, 504}
                and attempt < self.spec.retries
            ):
                time.sleep(min(2**attempt, 4))
                continue
            if response.is_error:
                # Do not serialize exception URLs, credentials or response bodies.
                return Generation(
                    error=f"HTTP {response.status_code}",
                    usage={"attempts": attempts},
                    request_id=response.headers.get("request-id")
                    or response.headers.get("x-request-id"),
                )
            try:
                result = self._decode(response.json())
                return result.model_copy(
                    update={
                        "request_id": result.request_id
                        or response.headers.get("request-id")
                        or response.headers.get("x-request-id"),
                        "usage": {**result.usage, "attempts": attempts},
                    }
                )
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                return Generation(
                    error=f"Invalid provider response: {type(exc).__name__}",
                    usage={"attempts": attempts},
                )
        raise AssertionError("unreachable")

    def _decode(self, data: dict) -> Generation:
        provider = self.spec.provider
        if provider == "openai":
            usage = data.get("usage") or {}
            text = "".join(
                part["text"]
                for item in data.get("output", [])
                if item.get("type") == "message"
                for part in item.get("content", [])
                if part.get("type") == "output_text"
            )
            finish = data.get("status", "completed")
            return Generation(
                text=text,
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                usage=usage,
                request_id=data.get("id"),
                finish_reason=finish,
                resolved_model=data.get("model"),
                error=None
                if finish == "completed" and text
                else f"OpenAI status: {finish}; empty/incomplete output",
            )
        if provider == "anthropic":
            usage = data.get("usage") or {}
            text = "".join(
                p["text"] for p in data["content"] if p.get("type") == "text"
            )
            finish = data.get("stop_reason")
            return Generation(
                text=text,
                input_tokens=usage.get("input_tokens"),
                output_tokens=usage.get("output_tokens"),
                usage=usage,
                request_id=data.get("id"),
                finish_reason=finish,
                resolved_model=data.get("model"),
                error=None
                if finish in {"end_turn", "stop_sequence"} and text
                else f"Claude stop: {finish}",
            )
        if provider == "gemini":
            usage = data.get("usageMetadata") or {}
            candidate = (data.get("candidates") or [{}])[0]
            text = "".join(
                p["text"]
                for p in candidate.get("content", {}).get("parts", [])
                if "text" in p and not p.get("thought", False)
            )
            finish = candidate.get("finishReason")
            # Output total includes reasoning tokens where the API reports them.
            output = usage.get("candidatesTokenCount")
            if output is not None:
                output += usage.get("thoughtsTokenCount", 0)
            return Generation(
                text=text,
                input_tokens=usage.get("promptTokenCount"),
                output_tokens=output,
                usage=usage,
                finish_reason=finish,
                request_id=data.get("responseId"),
                resolved_model=data.get("modelVersion"),
                error=None if finish == "STOP" and text else f"Gemini finish: {finish}",
            )
        choice = data["choices"][0]
        usage = data.get("usage") or {}
        text, finish = (
            choice["message"].get("content") or "",
            choice.get("finish_reason"),
        )
        return Generation(
            text=text,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            usage=usage,
            finish_reason=finish,
            request_id=data.get("id"),
            resolved_model=data.get("model"),
            error=None if finish == "stop" and text else f"Chat finish: {finish}",
        )

    def close(self) -> None:
        self.client.close()


def build_backend(spec: ModelSpec) -> TextBackend:
    if spec.provider == "abstain":
        return AbstainBackend()
    if spec.provider == "transformers":
        from .local import TransformersBackend

        return TransformersBackend(spec)
    return APIBackend(spec)
