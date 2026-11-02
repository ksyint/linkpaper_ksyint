"""Evaluator-only bridge from real frozen agent traces to candidate GLRS inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pydantic import Field, model_validator

from .agent_bench.cli import read_rows
from .agent_bench.contracts import Budget, Case, Evidence, Prediction, StrictModel
from .agent_bench.environment import Environment, ToolError
from .agent_bench.scoring import score_predictions
from .lineage_metric import Episode, Triplet, evaluate
from . import lineage_metric

ARMS = ('B', 'R', 'N')


class TripletSpec(StrictModel):
    """Private curator mapping; never put this record in a policy/tool prompt."""
    triplet_id: str = Field(min_length=1)
    group_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    B: str = Field(min_length=1)
    R: str = Field(min_length=1)
    N: str = Field(min_length=1)
    eligible_evidence_ids: dict[str, list[str]]

    @model_validator(mode='after')
    def check_arms(self):
        if any(not getattr(self, name).strip() for name in ('triplet_id', 'group_id', 'family_id', *ARMS)):
            raise ValueError('Blank private triplet identifier')
        if len({self.B, self.R, self.N}) != 3:
            raise ValueError('A triplet requires three distinct case IDs')
        if set(self.eligible_evidence_ids) != set(ARMS):
            raise ValueError('Explicit eligible witnesses are required for B/R/N')
        if any(len(ids) != len(set(ids)) for ids in self.eligible_evidence_ids.values()):
            raise ValueError('Duplicate eligible witness ID')
        return self


def _opened_from_frozen_trace(environment, prediction):
    """Derive acquisitions from accepted tool observations, not a submitted list."""
    if prediction is None:
        return [], 'missing_prediction'
    for event in prediction.trace:
        previous_opened = sorted(environment.opened)
        try:
            environment.call(event.action)
        except ToolError:
            return sorted(environment.opened), 'invalid_tool_or_budget'
        if environment.trace[-1] != event:
            return previous_opened, 'trace_observation_mismatch'
    if set(prediction.opened_ids) != environment.opened:
        return sorted(environment.opened), 'forged_opened_ids'
    return sorted(environment.opened), None


def construct_triplets(corpus: list[Evidence], cases: list[Case], predictions: list[Prediction],
                       specs: list[TripletSpec], *, seed=20261102, budget=None):
    """Join evaluator records only after the core's full trace-integrity scoring."""
    if not specs or len({s.triplet_id for s in specs}) != len(specs):
        raise ValueError('Nonempty unique scheduled triplet IDs are required')
    core = score_predictions(corpus, cases, predictions, seed=seed, budget=budget)
    diagnostics = {row['case_id']: row for row in core['cases']}
    case_lookup = {case.case_id: case for case in cases}
    evidence_lookup = {e.evidence_id: e for e in corpus}
    by_task = {p.task_id: p for p in predictions}
    triplets = []
    for spec in specs:
        try:
            selected = {arm: case_lookup[getattr(spec, arm)] for arm in ARMS}
        except KeyError as exc:
            raise ValueError('Triplet references an unknown case ID') from exc
        base = selected['B']
        for case in selected.values():
            if (case.family_id, case.split, case.question, case.question_language,
                case.gold.expected_conditions, len(case.visible_evidence_ids),
                len({evidence_lookup[e].paper_id for e in case.visible_evidence_ids})) != (
                spec.family_id, base.split, base.question, base.question_language,
                base.gold.expected_conditions, len(base.visible_evidence_ids),
                len({evidence_lookup[e].paper_id for e in base.visible_evidence_ids})
            ):
                raise ValueError('Matched cases require one family/split/question/language/conditions and equal record/source-paper counts')
        episodes = {}
        for arm, case in selected.items():
            eligible = spec.eligible_evidence_ids[arm]
            if not set(eligible) <= set(case.visible_evidence_ids):
                raise ValueError('Eligible witness is not visible in its case')
            environment = Environment(corpus, case, seed, budget)
            prediction = by_task.get(environment.task.task_id)
            opened, error = _opened_from_frozen_trace(environment, prediction)
            if prediction is not None:
                error = error or ('agent_error' if prediction.error else None)
            if diagnostics[case.case_id]['error']:
                error = error or 'core_integrity_failure'
            elif not diagnostics[case.case_id]['citation_read_validity']:
                error = error or 'invalid_claim_or_unopened_citation'
            answer = prediction.answer if prediction else None
            episodes[arm] = Episode(
                question=case.question, language=case.question_language,
                conditions=case.gold.expected_conditions,
                gold_units={environment.public_id(e): evidence_lookup[e].study_unit_id
                            for e in case.visible_evidence_ids},
                eligible_ids=[environment.public_id(e) for e in eligible],
                study_groups=answer.study_groups if answer else {}, opened_ids=opened,
                cited_ids=sorted({citation for claim in answer.claims for citation in claim.citations}) if answer else [],
                error=error,
            )
        # The metric verifies the known repeat/new unit-set constraints, including
        # base retention. Unknown provenance remains a declared exclusion.
        triplets.append(Triplet(triplet_id=spec.triplet_id, group_id=spec.group_id,
                                family_id=spec.family_id, **episodes))
    return triplets, core


def main(argv=None):
    parser = argparse.ArgumentParser(description='Evaluator-only agent-trace to GLRS bridge; CPU/offline')
    for name in ('corpus', 'cases', 'predictions', 'triplets', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--seed', type=int, default=20261102)
    parser.add_argument('--max-calls', type=int, default=12)
    parser.add_argument('--max-observation-chars', type=int, default=30000)
    parser.add_argument('--bootstrap-samples', type=int, default=0)
    args = parser.parse_args(argv)
    corpus, cases = read_rows(args.corpus, Evidence), read_rows(args.cases, Case)
    predictions = read_rows(args.predictions, Prediction)
    specs = read_rows(args.triplets, TripletSpec)
    budget = Budget(max_calls=args.max_calls, max_observation_chars=args.max_observation_chars)
    triplets, core = construct_triplets(corpus, cases, predictions, specs, seed=args.seed, budget=budget)
    report = evaluate(triplets, bootstrap_samples=args.bootstrap_samples, seed=args.seed)
    args.out.mkdir(parents=True, exist_ok=False)
    outputs = {'triplets.private.json': [t.model_dump(mode='json') for t in triplets],
               'glrs.json': report, 'core_diagnostics.json': core}
    for name, value in outputs.items():
        (args.out / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    manifest = {'scope': 'EVALUATOR ONLY: these artifacts contain private gold and must not enter agent inputs.',
                'interpretation': 'Candidate metric/tool integration; synthetic fixture results are not scientific validation.',
                'contains_fixtures_or_drafts': core['contains_fixtures_or_drafts'],
                'contains_oracle': core['contains_oracle'], 'scheduled_triplets': len(specs),
                'seed': args.seed, 'budget': budget.model_dump(),
                'matched_counts': {s.triplet_id: {arm: {
                    'record_count': len(next(c for c in cases if c.case_id == getattr(s, arm)).visible_evidence_ids),
                    'source_paper_count': len({e.paper_id for e in corpus if e.evidence_id in
                        next(c for c in cases if c.case_id == getattr(s, arm)).visible_evidence_ids})
                    } for arm in ARMS} for s in specs},
                'source_sha256': {name: hashlib.sha256(getattr(args, name).read_bytes()).hexdigest()
                                  for name in ('corpus', 'cases', 'predictions', 'triplets')},
                'bridge_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'metric_sha256': hashlib.sha256(Path(lineage_metric.__file__).read_bytes()).hexdigest()}
    (args.out / 'manifest.private.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'scheduled_triplets': len(specs), 'family_macro_GLRS': report['family_macro_GLRS'],
                      'evaluator_only': True}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
