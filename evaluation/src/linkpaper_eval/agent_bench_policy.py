"""Explicit JSON subprocess bridge for a trusted, separately configured agent.

This transports public observations, not private corpus/gold objects. It is not
an OS sandbox. Real held-out evaluation must isolate the agent process from the
private evaluator filesystem as described in the protocol.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile

from .agent_bench.contracts import Action, Answer, PublicTask, ToolEvent


class JsonCommandPolicy:
    def __init__(self, command: list[str], timeout: float = 120,
                 use_gpu: bool = False, gpu_index: int | None = None):
        if (not isinstance(command, list) or not command
                or any(not isinstance(arg, str) or not arg for arg in command)):
            raise ValueError('Policy command must be an explicit nonempty JSON argv array')
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Policy timeout must be finite and positive')
        self.command, self.timeout = tuple(command), timeout
        self.child_environment = os.environ.copy()
        self.child_environment['CUDA_VISIBLE_DEVICES'] = ''
        if use_gpu:
            if type(gpu_index) is not int or gpu_index < 0:
                raise ValueError('GPU policy needs an explicit allocated physical GPU index')
            from .research_bench.local import pin_gpu
            self.child_environment['CUDA_VISIBLE_DEVICES'] = pin_gpu(gpu_index)

    def step(self, task: PublicTask, history: list[ToolEvent]) -> Action | Answer:
        # Serialize only validated public DTOs. No environment, corpus path,
        # case, world label, split, result-unit IDs or gold are in this payload.
        public_task = PublicTask.model_validate(task.model_dump(mode='json'))
        public_history = [ToolEvent.model_validate(event.model_dump(mode='json')) for event in history]
        payload = json.dumps({'schema_version': 1,
                              'task': public_task.model_dump(mode='json'),
                              'history': [event.model_dump(mode='json') for event in public_history]},
                             ensure_ascii=False)
        if len(payload.encode('utf-8')) > 2_000_000:
            raise ValueError('Policy input limit exceeded; observations were not truncated')
        try:
            # An empty cwd reduces accidental dataset access; this is explicitly
            # NOT a filesystem isolation guarantee for a trusted plugin.
            with tempfile.TemporaryDirectory(prefix='linkpaper-public-policy-') as cwd:
                result = subprocess.run(self.command, input=payload, text=True,
                                        capture_output=True, timeout=self.timeout,
                                        cwd=cwd, env=self.child_environment,
                                        check=False, shell=False)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Policy decision timeout') from None
        except OSError:
            raise RuntimeError('Policy executable unavailable') from None
        if result.returncode:
            # Child stderr/command/env may contain credentials; never include
            # them in a benchmark Prediction.error or public report.
            raise RuntimeError(f'Policy exited with status {result.returncode}')
        if len(result.stdout.encode('utf-8')) > 1_000_000:
            raise ValueError('Policy output exceeds decision limit')
        try:
            value = json.loads(result.stdout)
        except (json.JSONDecodeError, UnicodeError):
            raise ValueError('Policy must return exactly one JSON decision') from None
        if not isinstance(value, dict):
            raise ValueError('Policy decision must be a JSON object')
        return Action.model_validate(value) if 'tool' in value else Answer.model_validate(value)


def factory():
    """Use with --policy linkpaper_eval.agent_bench_policy:factory.

    Command paths should be absolute because each decision uses an empty cwd.
    Model/provider credentials stay in the trusted child environment, never in
    public task objects or command output. Configure physical CUDA3 separately
    before a remote GPU-backed server is used. A local child defaults to CPU;
    LINKPAPER_POLICY_USES_GPU=1 plus LINKPAPER_POLICY_GPU_INDEX selects one
    explicitly allocated physical GPU by UUID before spawning.
    """
    raw = os.environ.get('LINKPAPER_POLICY_COMMAND_JSON')
    if not raw:
        raise ValueError('LINKPAPER_POLICY_COMMAND_JSON is required')
    try:
        command = json.loads(raw)
        timeout = float(os.environ.get('LINKPAPER_POLICY_TIMEOUT_SECONDS', '120'))
    except (json.JSONDecodeError, ValueError):
        raise ValueError('Invalid policy command/timeout configuration') from None
    gpu_flag = os.environ.get('LINKPAPER_POLICY_USES_GPU', '0')
    if gpu_flag not in {'0', '1'}:
        raise ValueError('LINKPAPER_POLICY_USES_GPU must be 0 or 1')
    index = None
    if gpu_flag == '1':
        raw_index = os.environ.get('LINKPAPER_POLICY_GPU_INDEX', '')
        if not raw_index.isdecimal():
            raise ValueError('Set LINKPAPER_POLICY_GPU_INDEX to an allocated physical GPU index')
        index = int(raw_index)
    return JsonCommandPolicy(command, timeout, use_gpu=gpu_flag == '1', gpu_index=index)
