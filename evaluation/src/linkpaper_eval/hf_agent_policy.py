"""Strict public-only policy bridge to a separately allocated local HF worker.

This Python 3.12 module imports no torch and never repairs model decisions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import selectors
import subprocess
import threading

from .agent_bench.contracts import Action, Answer, PublicTask, ToolEvent


class ModelPolicyError(ValueError):
    pass


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ModelPolicyError('Duplicate JSON key in model decision')
        result[key] = value
    return result


def parse_decision(raw: str) -> Action | Answer:
    """One exact JSON object, strict schema; no fence/XML/substring recovery."""
    def invalid_constant(value):
        raise ModelPolicyError('Nonstandard JSON constant: ' + value)
    try:
        value = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=invalid_constant)
        if not isinstance(value, dict):
            raise ModelPolicyError('Model decision must be one JSON object')
        kind = value.pop('kind', None)
        if kind == 'action':
            return Action.model_validate(value, strict=True)
        if kind == 'answer':
            return Answer.model_validate(value, strict=True)
        raise ModelPolicyError('Model decision needs kind=action or kind=answer')
    except (ValueError, TypeError) as error:
        raise ModelPolicyError('Invalid model JSON/schema: ' + type(error).__name__) from error


class WorkerClient:
    """Owns exactly its explicit child process; no GPU inference in this process."""
    def __init__(self, command: list[str], *, stderr_path: Path, timeout=60.0):
        self.timeout = timeout
        self._sequence = 0
        self._lock = threading.Lock()
        self._closed = False
        stderr_path.parent.mkdir(parents=True, exist_ok=True)
        self._stderr = stderr_path.open('w', encoding='utf-8')
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self._stderr, text=True, encoding='utf-8', bufsize=1)
        try:
            ready = self._read()
            if ready.get('type') != 'ready' or not isinstance(ready.get('metadata'), dict):
                raise ModelPolicyError('Worker did not return a metadata handshake')
            self.metadata = ready['metadata']
        except Exception:
            self.close()
            raise

    def _read(self):
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            if not selector.select(self.timeout):
                raise ModelPolicyError('Local model worker timed out')
        line = self.process.stdout.readline()
        if not line:
            raise ModelPolicyError('Local model worker exited before its response')
        try:
            value = json.loads(line)
        except ValueError as error:
            raise ModelPolicyError('Invalid worker JSONL protocol') from error
        if not isinstance(value, dict):
            raise ModelPolicyError('Invalid worker envelope')
        return value

    def request(self, public_payload: dict) -> dict:
        with self._lock:
            self._sequence += 1
            request_id = f'r{self._sequence:06d}'
            request = {'request_id': request_id, **public_payload}
            self.process.stdin.write(json.dumps(request, ensure_ascii=False, allow_nan=False) + '\n')
            self.process.stdin.flush()
            value = self._read()
            if value.get('type') != 'response' or value.get('request_id') != request_id:
                raise ModelPolicyError('Worker response/request mismatch')
            return value

    def close(self):
        if self._closed:
            return
        self._closed = True
        if self.process.poll() is None:
            try:
                self.process.stdin.write('{"command":"shutdown"}\n')
                self.process.stdin.flush()
                self.process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout, self._stderr):
            stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class HFPolicy:
    """Fresh episode policy; shared worker retains weights, not conversation state."""
    def __init__(self, client, *, raw_log_path: Path | None = None):
        self.client = client
        self.raw_log_path = raw_log_path

    def step(self, task: PublicTask, history: list[ToolEvent]) -> Action | Answer:
        # Copy/validate ONLY the exact public contract; no Case, corpus, gold or
        # triplet specifications are accepted by this interface.
        public = {'task': PublicTask.model_validate(task).model_dump(mode='json'),
                  'history': [ToolEvent.model_validate(e).model_dump(mode='json') for e in history]}
        record = {'public_request': public}
        try:
            response = self.client.request(public)
            record['worker_response'] = response
            if not isinstance(response, dict):
                raise ModelPolicyError('Invalid worker response')
            if response.get('error') is not None:
                raise ModelPolicyError('Model worker error: ' + str(response['error']))
            if response.get('finish_reason') != 'stop':
                raise ModelPolicyError('Incomplete model output: ' + str(response.get('finish_reason')))
            raw = response.get('raw_text')
            if not isinstance(raw, str):
                raise ModelPolicyError('Missing raw model generation')
            record['raw_generation_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
            decision = parse_decision(raw)
            record['parse_status'] = 'valid_' + ('action' if isinstance(decision, Action) else 'answer')
            return decision
        except Exception as error:
            record.update(parse_status='failed', error=type(error).__name__ + ': ' + str(error))
            raise
        finally:
            if self.raw_log_path is not None:
                self.raw_log_path.parent.mkdir(parents=True, exist_ok=True)
                with self.raw_log_path.open('a', encoding='utf-8') as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n')
