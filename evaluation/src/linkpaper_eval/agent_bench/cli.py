"""Offline-only validate, run-demo, plugin-policy run and structural scoring."""
from __future__ import annotations

import argparse
import importlib
import hashlib
import inspect
import json
import platform
import subprocess
from pathlib import Path

from .contracts import Budget, Case, Evidence, Prediction, Review, digest
from .environment import validate_study
from .runner import run_demo, run_policy
from .scoring import score_predictions

FIXTURES = Path(__file__).resolve().parents[3] / 'fixtures' / 'agent_bench'


def read_rows(path, model):
    return [model.model_validate_json(line) for line in Path(path).read_text(encoding='utf-8').splitlines()
            if line.strip()]


def main(argv=None):
    parser = argparse.ArgumentParser(description='Korean agent fixture/curated-corpus harness; no network or GPU')
    parser.add_argument('command', choices=['validate', 'run-demo', 'run', 'score'])
    parser.add_argument('--corpus', type=Path, default=FIXTURES / 'corpus.jsonl')
    parser.add_argument('--cases', type=Path, default=FIXTURES / 'cases.jsonl')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--agent', choices=['lexical', 'blind', 'oracle'], default='lexical')
    parser.add_argument('--policy', help='Explicit module:factory, returning a fresh Policy per case')
    parser.add_argument('--predictions', type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--publication', action='store_true', help='Reject fixture/draft/unreviewed sources and oracle controls')
    parser.add_argument('--seed', type=int, default=20261102)
    parser.add_argument('--max-calls', type=int, default=12)
    parser.add_argument('--max-observation-chars', type=int, default=30000)
    args = parser.parse_args(argv)
    corpus, cases = read_rows(args.corpus, Evidence), read_rows(args.cases, Case)
    validation = validate_study(corpus, cases, publication=args.publication)
    if args.command == 'validate':
        # Cardinalities are private evaluator diagnostics, not public task
        # instructions. Avoid dumping a per-case gold-support registry to logs.
        print(json.dumps({key: value for key, value in validation.items()
                          if key != 'private_support_profiles'}, ensure_ascii=False, indent=2))
        return 0
    if args.out is None:
        parser.error('--out is required')
    budget = Budget(max_calls=args.max_calls, max_observation_chars=args.max_observation_chars)
    policy_source = {'status': 'not_loaded_during_scoring' if args.command == 'score' else 'built_in_demo',
                     'module': None, 'factory': None, 'sha256': None}
    if args.command == 'score':
        if args.predictions is None:
            parser.error('--predictions is required for score')
        predictions = read_rows(args.predictions, Prediction)
    elif args.command == 'run':
        if not args.policy or args.policy.count(':') != 1:
            parser.error('run requires an explicit --policy module:factory')
        module, name = args.policy.split(':')
        factory = getattr(importlib.import_module(module), name)
        if not callable(factory):
            parser.error('Policy factory must be callable')
        policy_source.update(status='source_unavailable', module=module, factory=name)
        try:
            source_file = inspect.getsourcefile(factory)
            if source_file:
                policy_source.update(status='source_hashed', file_name=Path(source_file).name,
                                     sha256=hashlib.sha256(Path(source_file).read_bytes()).hexdigest())
        except (OSError, TypeError):
            pass
        predictions = run_policy(factory, corpus, cases, budget, args.seed)
    else:
        if args.publication and args.agent == 'oracle':
            parser.error('Oracle controls are not publication results')
        predictions = run_demo(args.agent, corpus, cases, budget, args.seed)
    reviews = read_rows(args.reviews, Review) if args.reviews else []
    scores = score_predictions(corpus, cases, predictions, reviews, args.seed, budget, args.publication)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'predictions.jsonl').write_text(''.join(p.model_dump_json() + '\n' for p in predictions), encoding='utf-8')
    (args.out / 'scores.json').write_text(json.dumps(scores, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    manifest = {'schema_version': 2, 'seed': args.seed, 'budget': budget.model_dump(),
                'public_task_fields': ['task_id', 'question', 'question_language'],
                'required_source_count_disclosed': False,
                'supported_answer_types': ['decision', 'short', 'numeric', 'explanation'],
                'cases_sha256': digest(args.cases.read_text(encoding='utf-8')),
                'corpus_sha256': digest(args.corpus.read_text(encoding='utf-8')),
                'agent': args.agent if args.command == 'run-demo' else args.policy,
                'policy_source': policy_source,
                'model_provenance': {'status': 'not_applicable_offline_demo' if args.command == 'run-demo'
                                     else 'externally_supplied_or_pending',
                                     'model_id': None, 'model_revision': None,
                                     'note': 'Policy source hash is not model/weight provenance; external adapters must supply resolved model metadata.'},
                'publication_validation': args.publication,
                'scope': 'Structural tool/evidence diagnostics; fixture scores are not paper results.',
                'python': platform.python_version(),
                'harness_sha256': digest(''.join(p.name + '\n' + p.read_text(encoding='utf-8')
                                              for p in sorted(Path(__file__).parent.glob('*.py'))))}
    try:
        manifest['git_sha'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, timeout=5).strip()
        manifest['git_dirty'] = bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True, timeout=5).strip())
    except (OSError, subprocess.SubprocessError):
        manifest['git_sha'] = None
        manifest['git_dirty'] = None
    (args.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(scores['aggregate'], ensure_ascii=False, indent=2))
    return 0
