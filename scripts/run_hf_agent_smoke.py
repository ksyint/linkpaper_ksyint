#!/usr/bin/env python3
"""At most three REAL-model episodes on ORIGINAL SYNTHETIC fixtures, not paper eval."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from linkpaper_eval.agent_bench.cli import read_rows
from linkpaper_eval.agent_bench.contracts import Budget, Case, Evidence, Prediction
from linkpaper_eval.agent_bench.environment import Environment
from linkpaper_eval.agent_bench.runner import run_policy
from linkpaper_eval.agent_lineage import TripletSpec, construct_triplets
from linkpaper_eval.hf_agent_policy import HFPolicy, WorkerClient
from linkpaper_eval.lineage_metric import evaluate
from linkpaper_eval import hf_agent_policy

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker-python', required=True)
    parser.add_argument('--model-path', required=True, type=Path)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--gpu', required=True, help='Explicit allocated physical GPU index or UUID')
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    fixture = ROOT / 'evaluation/fixtures/agent_lineage'
    corpus = read_rows(fixture / 'corpus.jsonl', Evidence)
    cases = read_rows(fixture / 'cases.jsonl', Case)
    specs = read_rows(fixture / 'triplets.jsonl', TripletSpec)
    if len(cases) > 3 or any(c.question_language != 'ko' for c in cases):
        parser.error('This smoke is limited to at most three Korean fixture episodes')
    args.out.mkdir(parents=True, exist_ok=False)
    budget, seed = Budget(max_calls=6, max_observation_chars=30000), 20261102
    worker = ROOT / 'scripts/hf_agent_worker.py'
    command = [args.worker_python, '-u', str(worker), '--model-path', str(args.model_path),
               '--revision', args.revision, '--gpu', args.gpu, '--memory-gb', '8',
               '--max-new-tokens', '384', '--max-context-tokens', '8192', '--seed', str(seed)]
    metadata, setup_error, worker_pid, worker_exit, predictions = None, None, None, None, None
    try:
        with WorkerClient(command, stderr_path=args.out / 'worker.stderr.log', timeout=60) as client:
            worker_pid = client.process.pid
            metadata = client.metadata
            write_json(args.out / 'model_metadata.json', metadata)
            predictions = run_policy(lambda: HFPolicy(client, raw_log_path=args.out / 'raw_public_responses.jsonl'),
                                     corpus, cases, budget, seed)
        worker_exit = client.process.returncode
    except Exception as error:
        setup_error = type(error).__name__ + ': ' + str(error)
        if predictions is None:
            predictions = [Prediction(task_id=Environment(corpus, case, seed, budget).task.task_id,
                                      error='Worker setup/run failure: ' + setup_error) for case in cases]
    (args.out / 'predictions.jsonl').write_text(''.join(p.model_dump_json() + '\n' for p in predictions), encoding='utf-8')
    triplets, core = construct_triplets(corpus, cases, predictions, specs, seed=seed, budget=budget)
    glrs = evaluate(triplets, bootstrap_samples=0, seed=seed)
    write_json(args.out / 'triplets.private.json', [t.model_dump(mode='json') for t in triplets])
    write_json(args.out / 'core_diagnostics.json', core)
    write_json(args.out / 'glrs.json', glrs)
    calls = []
    raw_path = args.out / 'raw_public_responses.jsonl'
    if raw_path.exists():
        calls = [json.loads(line) for line in raw_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    shutdown = {'worker_pid': worker_pid, 'exit_code': worker_exit, 'own_process_exited': worker_exit is not None}
    if worker_pid is not None:
        process_check = subprocess.run(['nvidia-smi', '-i', args.gpu, '--query-compute-apps=pid',
                                       '--format=csv,noheader,nounits'], capture_output=True, text=True)
        shutdown.update(nvidia_smi_check_returncode=process_check.returncode,
                        worker_pid_present_after_close=str(worker_pid) in process_check.stdout.split())
    manifest = {'scope': 'REAL tiny-model policy integration smoke on ORIGINAL SYNTHETIC fixtures; NOT paper performance or metric validation.',
        'started_or_recorded_at_utc': datetime.now(timezone.utc).isoformat(), 'model_id': 'Qwen/Qwen3-0.6B',
        'model_revision': args.revision, 'allocated_gpu': args.gpu, 'command': command,
        'budget': budget.model_dump(), 'seed': seed, 'scheduled_episodes': len(cases),
        'successful_final_answers': sum(p.answer is not None and p.error is None for p in predictions),
        'failed_episodes': sum(p.error is not None for p in predictions), 'model_calls': len(calls),
        'invalid_or_failed_model_calls': sum(c.get('parse_status') == 'failed' for c in calls),
        'completion_tokens': sum(c.get('worker_response', {}).get('completion_tokens', 0) for c in calls),
        'model_generation_seconds': sum(c.get('worker_response', {}).get('latency_seconds', 0) for c in calls),
        'setup_error': setup_error, 'shutdown': shutdown,
        'source_sha256': {name: hashlib.sha256((fixture / name).read_bytes()).hexdigest()
                          for name in ('corpus.jsonl', 'cases.jsonl', 'triplets.jsonl')},
        'policy_sha256': hashlib.sha256(Path(hf_agent_policy.__file__).read_bytes()).hexdigest(),
        'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write_json(args.out / 'manifest.json', manifest)
    print(json.dumps({'scheduled': len(cases), 'answers': manifest['successful_final_answers'],
                      'failures': manifest['failed_episodes'], 'model_calls': len(calls),
                      'family_macro_GLRS': glrs['family_macro_GLRS'], 'shutdown': shutdown}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
