"""Strict format diagnostics and evidence-gated, response-bound semantic review.

Private condition-key spellings do not substitute for human meaning judgments.
Failed/ungrounded outputs remain zero; valid unreviewed outputs remain pending.
"""
from __future__ import annotations

from itertools import combinations
from decimal import Decimal, DecimalException
from statistics import mean

from .contracts import Budget, Case, Evidence, Prediction, Review
from .environment import Environment, ToolError, validate_study


def _reference_match(answer, gold):
    """Strict reference-format diagnostic, never scientific semantic grading.

    Numeric answers are complete unitless numbers; the unit/protocol belongs
    in conditions. No substring number extraction or implicit unit conversion.
    Explanations require response-bound semantic review, not string matching.
    """
    if gold.answer_type == 'short':
        normalize = lambda value: ' '.join(value.casefold().split())
        return float(normalize(answer) in {normalize(v) for v in gold.reference_answers})
    if gold.answer_type == 'numeric':
        try:
            value = Decimal(answer.strip())
            if not value.is_finite():
                return 0.
            tolerance = Decimal(str(gold.numeric_tolerance))
            return float(any(abs(value - Decimal(reference)) <= tolerance
                             for reference in gold.reference_answers))
        except DecimalException:
            return 0.
    return None


def _mean_applicable(rows, key):
    values = [row[key] for row in rows if row[key] is not None]
    return mean(values) if values else None


def score_predictions(corpus: list[Evidence], cases: list[Case], predictions: list[Prediction],
                      reviews: list[Review] | None = None, seed=20261102,
                      budget: Budget | None = None, publication=False):
    validation = validate_study(corpus, cases, publication=publication)
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
               'task_type': case.task_type, 'answer_type': case.gold.answer_type,
               'known_support_profile': validation['private_support_profiles'][case.case_id],
               'verdict_agreement': 0. if case.gold.answer_type == 'decision' else None,
               'reference_answer_match': 0. if case.gold.answer_type in {'short', 'numeric'} else None,
               'answer_contract_valid': 0., 'citation_read_validity': 0.,
               'sufficient_evidence_coverage': 0., 'condition_recall': 0.,
               'semantic_evidence_gate': 0.,
               'structural_pass': 0., 'error': 1., 'semantic_pass': None}
        known = {environment.public_id(e): lookup[e].study_unit_id
                 for e in case.visible_evidence_ids if lookup[e].study_unit_id is not None}
        pairs = list(combinations(known, 2)) if case.task_type == 'result_provenance' else []
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
                decision = case.gold.answer_type == 'decision'
                contract = not decision or answer.verdict is not None
                verdict = answer.verdict == case.gold.verdict if decision else True
                sufficient = not case.gold.sufficient_sets or any(
                    {environment.public_id(e) for e in ids} <= cited
                    for ids in case.gold.sufficient_sets)
                conditions = all(' '.join(answer.conditions.get(k, '').casefold().split())
                                 == ' '.join(v.casefold().split())
                                 for k, v in case.gold.expected_conditions.items())
                row.update(error=0., verdict_agreement=float(verdict) if decision else None,
                           reference_answer_match=_reference_match(answer.answer, case.gold),
                           answer_contract_valid=float(contract), citation_read_validity=float(valid),
                           sufficient_evidence_coverage=float(sufficient), condition_recall=float(conditions),
                           semantic_evidence_gate=float(contract and valid and verdict and sufficient),
                           structural_pass=float(contract and valid and verdict and sufficient and conditions))
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
        # Exact conditions-dict keys/values are private canonical annotations,
        # not a public vocabulary every general-QA policy was told to emit.
        # Keep that strict-format diagnostic separate: response-bound human
        # review judges condition meaning in the actual answer and claims.
        # It cannot waive invalid traces/citations or invent an unregistered
        # sufficient witness set; a valid new alternative needs a gold revision.
        if not row['semantic_evidence_gate']:
            row['semantic_pass'] = 0.
        elif task_id in review_map:
            row['semantic_pass'] = float(review_map[task_id].semantic_pass)
        rows.append(row)
    synthetic = any(c.synthetic or c.annotation_status != 'reviewed' for c in cases)
    synthetic = synthetic or any(e.synthetic or e.annotation_status != 'reviewed' for e in corpus)
    keys = ('verdict_agreement', 'reference_answer_match', 'answer_contract_valid',
            'citation_read_validity', 'sufficient_evidence_coverage',
            'condition_recall', 'semantic_evidence_gate', 'structural_pass', 'error')
    aggregate = {key: _mean_applicable(rows, key) for key in keys}
    evaluable = [r for r in rows if r['lineage_pair_count']]
    aggregate.update(lineage_pair_agreement=mean(r['lineage_pair_agreement'] for r in evaluable) if evaluable else None,
                     lineage_pair_coverage=mean(r['lineage_pair_coverage'] for r in evaluable) if evaluable else None,
                     lineage_evaluable_cases=len(evaluable), review_coverage=len(review_map) / len(rows),
                     semantic_review_required_cases=sum(bool(r['semantic_evidence_gate']) for r in rows),
                     semantic_review_completed_cases=sum(bool(r['semantic_evidence_gate']) and r['task_id'] in review_map
                                                         for r in rows),
                     decision_evaluable_cases=sum(r['verdict_agreement'] is not None for r in rows),
                     reference_evaluable_cases=sum(r['reference_answer_match'] is not None for r in rows),
                     scientific_semantic_accuracy=(mean(r['semantic_pass'] for r in rows)
                       if not synthetic and not any(p.oracle for p in predictions)
                       and all(r['semantic_pass'] is not None for r in rows) else None))
    return {'scheduled_cases': len(rows), 'missing_predictions': len(rows) - len(predictions),
            'contains_fixtures_or_drafts': synthetic, 'contains_oracle': any(p.oracle for p in predictions),
            'interpretation': 'Structural/reference-format diagnostics are not scientific semantic accuracy; '
                              'exact condition-dictionary agreement is a strict format diagnostic, while response-bound review judges condition meaning; '
                              'invalid/missing/ungrounded answers stay zero and valid unreviewed answers remain pending; '
                              'N/A metrics are excluded, scheduled applicable failures stay zero; '
                              'known support counts are not certified global minima; study units are not statistical independence.',
            'report_visibility': 'Evaluator-only: task types, reference/gold diagnostics and support cardinalities must not enter policy inputs.',
            'by_task_type': {task_type: {'scheduled_cases': sum(r['task_type'] == task_type for r in rows),
                              **{key: _mean_applicable([r for r in rows if r['task_type'] == task_type], key)
                                 for key in keys}}
                             for task_type in sorted({r['task_type'] for r in rows})},
            'aggregate': aggregate, 'cases': rows}
