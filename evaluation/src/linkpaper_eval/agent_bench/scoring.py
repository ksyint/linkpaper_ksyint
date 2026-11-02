"""Structural diagnostics, provenance grouping and separately bound human reviews."""
from __future__ import annotations

from itertools import combinations
from statistics import mean

from .contracts import Budget, Case, Evidence, Prediction, Review
from .environment import Environment, ToolError, validate_study


def score_predictions(corpus: list[Evidence], cases: list[Case], predictions: list[Prediction],
                      reviews: list[Review] | None = None, seed=20261102,
                      budget: Budget | None = None, publication=False):
    validate_study(corpus, cases, publication=publication)
    lookup = {e.evidence_id: e for e in corpus}
    environments = {Environment(corpus, c, seed, budget).task.task_id:
                    (c, Environment(corpus, c, seed, budget)) for c in cases}
    by_id = {}
    for prediction in predictions:
        if prediction.task_id not in environments or prediction.task_id in by_id:
            raise ValueError('Unknown/duplicate prediction')
        if publication and prediction.oracle:
            raise ValueError('Oracle controls cannot be publication results')
        by_id[prediction.task_id] = prediction
    review_map = {}
    for review in reviews or []:
        prediction = by_id.get(review.task_id)
        if (review.task_id in review_map or prediction is None
                or review.response_sha256 != prediction.response_sha256):
            raise ValueError('Unknown/duplicate/response-hash-mismatched semantic review')
        review_map[review.task_id] = review
    rows = []
    for task_id, (case, environment) in environments.items():
        prediction = by_id.get(task_id)
        row = {'task_id': task_id, 'case_id': case.case_id,
               'question_language': case.question_language, 'control_tag': case.control_tag,
               'verdict_agreement': 0., 'citation_read_validity': 0.,
               'sufficient_evidence_coverage': 0., 'condition_recall': 0.,
               'structural_pass': 0., 'error': 1., 'semantic_pass': None}
        known = {environment.public_id(e): lookup[e].study_unit_id
                 for e in case.visible_evidence_ids if lookup[e].study_unit_id is not None}
        pairs = list(combinations(known, 2))
        row.update(lineage_pair_count=len(pairs), lineage_pair_agreement=0. if pairs else None,
                   lineage_pair_coverage=0. if pairs else None)
        if prediction is not None and not prediction.error and prediction.answer is not None:
            try:
                for event in prediction.trace:
                    try:
                        environment.call(event.action)
                    except ToolError:
                        pass
                    if environment.trace[-1] != event:
                        raise ValueError('Trace observation does not match frozen tools')
                    if event.error:
                        raise ValueError('Invalid action/budget failure in completed answer')
                if set(prediction.opened_ids) != environment.opened:
                    raise ValueError('Unverified opened IDs')
                answer = prediction.answer
                cited = {i for claim in answer.claims for i in claim.citations}
                valid = bool(cited) and all(claim.citations for claim in answer.claims)
                valid = valid and cited <= environment.opened and set(answer.study_groups) <= cited
                verdict = answer.verdict == case.gold.verdict
                sufficient = not case.gold.sufficient_sets or any(
                    {environment.public_id(e) for e in ids} <= cited
                    for ids in case.gold.sufficient_sets)
                conditions = all(' '.join(answer.conditions.get(k, '').casefold().split())
                                 == ' '.join(v.casefold().split())
                                 for k, v in case.gold.expected_conditions.items())
                row.update(error=0., verdict_agreement=float(verdict), citation_read_validity=float(valid),
                           sufficient_evidence_coverage=float(sufficient), condition_recall=float(conditions),
                           structural_pass=float(valid and verdict and sufficient and conditions))
                if pairs:
                    covered = [(a, b) for a, b in pairs if a in cited and b in cited
                               and a in environment.opened and b in environment.opened
                               and answer.study_groups.get(a) is not None
                               and answer.study_groups.get(b) is not None]
                    row['lineage_pair_coverage'] = len(covered) / len(pairs)
                    row['lineage_pair_agreement'] = sum(
                        (answer.study_groups[a] == answer.study_groups[b]) == (known[a] == known[b])
                        for a, b in covered) / len(pairs)
            except (ValueError, KeyError, TypeError):
                pass  # Invalid traces remain failures in the full scheduled denominator.
        if task_id in review_map and row['error'] == 0:
            row['semantic_pass'] = float(review_map[task_id].semantic_pass) * row['structural_pass']
        rows.append(row)
    synthetic = any(c.synthetic or c.annotation_status != 'reviewed' for c in cases)
    synthetic = synthetic or any(e.synthetic or e.annotation_status != 'reviewed' for e in corpus)
    keys = ('verdict_agreement', 'citation_read_validity', 'sufficient_evidence_coverage',
            'condition_recall', 'structural_pass', 'error')
    aggregate = {key: mean(r[key] for r in rows) for key in keys}
    evaluable = [r for r in rows if r['lineage_pair_count']]
    aggregate.update(lineage_pair_agreement=mean(r['lineage_pair_agreement'] for r in evaluable) if evaluable else None,
                     lineage_pair_coverage=mean(r['lineage_pair_coverage'] for r in evaluable) if evaluable else None,
                     lineage_evaluable_cases=len(evaluable), review_coverage=len(review_map) / len(rows),
                     scientific_semantic_accuracy=(mean(r['semantic_pass'] for r in rows)
                       if not synthetic and not any(p.oracle for p in predictions)
                       and all(r['semantic_pass'] is not None for r in rows) else None))
    return {'scheduled_cases': len(rows), 'missing_predictions': len(rows) - len(predictions),
            'contains_fixtures_or_drafts': synthetic, 'contains_oracle': any(p.oracle for p in predictions),
            'interpretation': 'Structural agreement is not scientific correctness; study units are not statistical independence.',
            'aggregate': aggregate, 'cases': rows}
