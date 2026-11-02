"""General QA contracts and public boundaries, not scientific model performance."""
from pathlib import Path
import json

import pytest
from pydantic import ValidationError

from linkpaper_eval.agent_bench.cli import main, read_rows
from linkpaper_eval.agent_bench.contracts import Action, Answer, Budget, Case, Claim, Evidence, Gold, Prediction, Review, answer_hash
from linkpaper_eval.agent_bench.environment import Environment, ToolError, validate_study
from linkpaper_eval.agent_bench.scoring import score_predictions
from linkpaper_eval.agent_lineage import TripletSpec, construct_triplets

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures' / 'scholarly_qa'
BUDGET = Budget(max_calls=24)


@pytest.fixture
def study():
    return read_rows(FIXTURE / 'corpus.jsonl', Evidence), read_rows(FIXTURE / 'cases.jsonl', Case)


def prediction(corpus, case, ids, *, text=None, verdict=None, conditions=None, groups=None):
    """Handwritten evaluator test prediction; never a claimed model result."""
    env = Environment(corpus, case, budget=BUDGET)
    for eid in ids:
        env.call(Action(tool='open', arguments={'document_id': env.public_id(eid)}))
    answer = Answer(answer=text if text is not None else case.gold.reference_answers[0],
                    verdict=verdict,
                    conditions=conditions or {},
                    study_groups={env.public_id(e): group for e, group in (groups or {}).items()},
                    claims=[Claim(text='수작업으로 구성한 계약 검사용 주장입니다.',
                                  citations=[env.public_id(e) for e in ids])])
    return Prediction(task_id=env.task.task_id, answer=answer, trace=env.trace,
                      opened_ids=sorted(env.opened), response_sha256=answer_hash(answer))


def row_score(corpus, case, pred):
    return score_predictions(corpus, [case], [pred], budget=BUDGET)['cases'][0]


def test_six_private_task_types_share_one_candidate_pool_and_do_not_disclose_support_counts(study):
    corpus, cases = study
    assert len(cases) == 7
    assert len({c.task_type for c in cases}) == 6
    assert len({tuple(c.visible_evidence_ids) for c in cases}) == 1
    report = validate_study(corpus, cases)
    assert report['private_support_profiles'][cases[0].case_id]['known_alternative_paper_counts'] == [1]
    assert report['private_support_profiles'][cases[0].case_id]['known_alternative_evidence_counts'] == [2]
    assert report['private_support_profiles'][cases[1].case_id]['known_alternative_paper_counts'] == [1, 2]
    assert report['private_support_profiles'][cases[-1].case_id]['known_alternative_paper_counts'] == []
    assert all(not p['global_minimum_certified'] and not p['disclosed_to_agent']
               for p in report['private_support_profiles'].values())
    env = Environment(corpus, cases[0], budget=BUDGET)
    public = env.call(Action(tool='search', arguments={'query': '실험', 'limit': 10}))
    payload = json.dumps({'task': env.task.model_dump(), 'observation': public}, ensure_ascii=False)
    assert set(env.task.model_dump()) == {'task_id', 'question', 'question_language'}
    for forbidden in ('task_type', 'answer_type', 'reference_answers', 'sufficient_sets',
                      'known_alternative_paper_counts', 'study_unit_id', 'private-sqa-RV1'):
        assert forbidden not in payload
    # Public citation/source metadata may identify discovered papers. This
    # reveals the candidate corpus, not the unknown number needed to answer.
    assert all('paper_id' in item for item in public['results'])


def test_private_task_annotation_changes_do_not_change_public_observations(study):
    corpus, cases = study
    case = cases[0]
    other = case.model_copy(update={'task_type': 'cross_paper_bridge',
        'gold': case.gold.model_copy(update={'sufficient_sets': [['sqa-record-05']],
                                           'reference_answers': ['different private answer']})})
    first, second = Environment(corpus, case), Environment(corpus, other)
    assert first.task == second.task
    action = Action(tool='search', arguments={'query': case.question})
    assert first.call(action) == second.call(action)


@pytest.mark.parametrize('available', [[], ['sqa-record-01']])
def test_acquisition_loss_does_not_drop_case_or_relabel_full_reference_gold(study, available):
    corpus, cases = study
    original = cases[0]
    case = original.model_copy(update={'available_evidence_ids': available})
    assert case.gold == original.gold
    report = validate_study(corpus, [case])
    profile = report['private_support_profiles'][case.case_id]
    assert profile['known_alternative_paper_counts'] == [1]
    assert profile['known_sufficient_set_available'] is False
    assert profile['available_evidence_count'] == len(available)
    env = Environment(corpus, case)
    result = env.call(Action(tool='search', arguments={'query': '실험', 'limit': 10}))
    assert len(result['results']) == len(available)
    with pytest.raises(ToolError, match='Unknown document'):
        env.call(Action(tool='open', arguments={'document_id': env.public_id('sqa-record-02')}))
    pred = prediction(corpus, case, available)
    score = score_predictions(corpus, [case], [pred], budget=BUDGET)
    assert score['scheduled_cases'] == 1 and score['missing_predictions'] == 0
    assert score['cases'][0]['sufficient_evidence_coverage'] == 0
    assert score['aggregate']['structural_pass'] == 0
    assert score['cases'][0]['answer_type'] == 'short'


def test_available_one_paper_alternative_succeeds_when_bridge_alternative_is_missing(study):
    corpus, cases = study
    case = cases[1].model_copy(update={'available_evidence_ids': ['sqa-record-05']})
    report = validate_study(corpus, [case])
    profile = report['private_support_profiles'][case.case_id]
    assert profile['known_sufficient_set_available'] is True
    assert profile['known_alternative_paper_counts'] == [1, 2]
    row = row_score(corpus, case, prediction(corpus, case, ['sqa-record-05']))
    assert row['structural_pass'] == 1
    env = Environment(corpus, case)
    identifier = env.public_id('sqa-record-05')
    env.call(Action(tool='open', arguments={'document_id': identifier}))
    assert env.call(Action(tool='citations', arguments={'document_id': identifier})) == {'results': []}
    payload = json.dumps(env.trace[0].model_dump(), ensure_ascii=False)
    for private in ('available_evidence_ids', 'known_sufficient_set_available', 'sufficient_sets'):
        assert private not in payload


@pytest.mark.parametrize('available', [['unknown-id'], ['sqa-record-01', 'sqa-record-01']])
def test_acquisition_mask_cannot_add_unknown_or_duplicate_records(study, available):
    corpus, cases = study
    with pytest.raises(ValueError, match='unique subset'):
        validate_study(corpus, [cases[0].model_copy(update={'available_evidence_ids': available})])


def test_single_paper_requires_both_evidence_passages_without_lineage_gold(study):
    corpus, cases = study
    case = cases[0]
    complete = row_score(corpus, case, prediction(corpus, case, ['sqa-record-01', 'sqa-record-02']))
    partial = row_score(corpus, case, prediction(corpus, case, ['sqa-record-01']))
    assert complete['structural_pass'] == complete['reference_answer_match'] == 1
    assert complete['verdict_agreement'] is None
    assert complete['lineage_pair_agreement'] is None and complete['lineage_pair_count'] == 0
    assert complete['known_support_profile']['known_alternative_paper_counts'] == [1]
    assert partial['sufficient_evidence_coverage'] == partial['structural_pass'] == 0
    assert partial['reference_answer_match'] == 1  # Matching an answer alone is not grounding.


@pytest.mark.parametrize('ids', [['sqa-record-03', 'sqa-record-04'], ['sqa-record-05']])
def test_valid_alternatives_can_require_different_numbers_of_papers(study, ids):
    corpus, cases = study
    case = cases[1]
    row = row_score(corpus, case, prediction(corpus, case, ids))
    assert row['structural_pass'] == 1
    assert row['known_support_profile']['known_alternative_paper_counts'] == [1, 2]
    partial = row_score(corpus, case, prediction(corpus, case, ['sqa-record-03']))
    assert partial['structural_pass'] == 0


def test_decision_verdicts_are_required_only_for_decision_questions(study):
    corpus, cases = study
    with pytest.raises(ValidationError, match='Decision gold requires'):
        Gold(answer_type='decision', sufficient_sets=[['e']])
    with pytest.raises(ValidationError, match='must not force'):
        Gold(answer_type='short', verdict='supported', reference_answers=['name'], sufficient_sets=[['e']])
    with pytest.raises(ValidationError, match='reference answer'):
        Gold(answer_type='short', sufficient_sets=[['e']])
    assert Answer(answer='일반 설명입니다.', claims=[Claim(text='서술 주장입니다.')]).verdict is None
    assert Answer(answer='4', claims=[Claim(text='계산한 값은 4입니다.')]).answer == '4'
    decision_case = cases[4]
    missing = row_score(corpus, decision_case, prediction(corpus, decision_case,
                                                        ['sqa-record-11', 'sqa-record-12']))
    assert missing['answer_contract_valid'] == missing['structural_pass'] == 0
    correct = row_score(corpus, decision_case, prediction(corpus, decision_case,
                         ['sqa-record-11', 'sqa-record-12'], verdict='mixed'))
    assert correct['verdict_agreement'] == correct['structural_pass'] == 1


@pytest.mark.parametrize('reference', ['NaN', 'Infinity', '15 particles/m²'])
def test_numeric_references_are_finite_explicit_numbers(reference):
    with pytest.raises(ValidationError, match='Numeric reference'):
        Gold(answer_type='numeric', reference_answers=[reference], sufficient_sets=[['e']])


def test_numeric_reference_matching_is_strict_and_not_semantic_accuracy(study):
    corpus, cases = study
    case = cases[3]
    for text, match in [('15.0', 1), ('16', 0), ('15 particles/m²', 0), ('NaN', 0), ('1e9999999999', 0)]:
        row = row_score(corpus, case, prediction(corpus, case, ['sqa-record-08', 'sqa-record-09'],
                          text=text, conditions={'unit': 'particles/m²'}))
        assert row['reference_answer_match'] == match
        assert row['structural_pass'] == 1  # Structural support is not arithmetic truth.
    wrong_unit = row_score(corpus, case, prediction(corpus, case, ['sqa-record-10'], text='15',
                                                   conditions={'unit': 'particles/km²'}))
    assert wrong_unit['structural_pass'] == 0
    report = score_predictions(corpus, [case], [prediction(corpus, case, ['sqa-record-10'], text='16',
                         conditions={'unit': 'particles/m²'})], budget=BUDGET)
    assert report['aggregate']['scientific_semantic_accuracy'] is None
    tolerant = case.model_copy(update={'gold': case.gold.model_copy(update={'numeric_tolerance': .1})})
    assert row_score(corpus, tolerant, prediction(corpus, tolerant, ['sqa-record-10'], text='15.05',
                           conditions={'unit': 'particles/m²'}))['reference_answer_match'] == 1


def test_explanations_require_response_bound_review_not_exact_string_matching(study):
    corpus, cases = study
    case = cases[2]
    pred = prediction(corpus, case, ['sqa-record-06', 'sqa-record-07'])
    review = Review(task_id=pred.task_id, response_sha256=pred.response_sha256,
                    semantic_pass=True, annotator='test-only reviewer metadata')
    report = score_predictions(corpus, [case], [pred], [review], budget=BUDGET)
    assert report['aggregate']['reference_answer_match'] is None
    assert report['aggregate']['reference_evaluable_cases'] == 0
    assert report['cases'][0]['semantic_pass'] == 1
    assert report['aggregate']['scientific_semantic_accuracy'] is None


def test_missing_cases_stay_in_applicable_denominators_and_na_is_not_zero(study):
    corpus, cases = study
    scores = score_predictions(corpus, cases, [], budget=BUDGET)
    assert scores['scheduled_cases'] == scores['missing_predictions'] == 7
    assert scores['aggregate']['error'] == 1
    assert scores['aggregate']['decision_evaluable_cases'] == 3
    assert scores['aggregate']['reference_evaluable_cases'] == 3
    assert scores['aggregate']['lineage_evaluable_cases'] == 1
    assert scores['aggregate']['verdict_agreement'] == scores['aggregate']['reference_answer_match'] == 0
    assert scores['by_task_type']['condition_comparison']['verdict_agreement'] is None
    assert scores['by_task_type']['conflict_and_sufficiency']['scheduled_cases'] == 2


def test_glrs_rejects_general_qa_even_when_old_data_has_result_unit_ids():
    old = FIXTURE.parent / 'agent_lineage'
    corpus = read_rows(old / 'corpus.jsonl', Evidence)
    cases = read_rows(old / 'cases.jsonl', Case)
    specs = read_rows(old / 'triplets.jsonl', TripletSpec)
    cases = [c.model_copy(update={'task_type': 'within_paper_composition'}) for c in cases]
    with pytest.raises(ValueError, match='only to the result_provenance subtrack'):
        construct_triplets(corpus, cases, [], specs)


def test_general_qa_cli_oracle_is_only_a_synthetic_control(study, tmp_path, capsys):
    out = tmp_path / 'qa-oracle'
    assert main(['run-demo', '--agent', 'oracle', '--corpus', str(FIXTURE / 'corpus.jsonl'),
                 '--cases', str(FIXTURE / 'cases.jsonl'), '--max-calls', '24', '--out', str(out)]) == 0
    score = json.loads((out / 'scores.json').read_text())
    assert score['aggregate']['structural_pass'] == score['aggregate']['reference_answer_match'] == 1
    assert score['aggregate']['lineage_evaluable_cases'] == 1
    assert score['contains_oracle'] and score['aggregate']['scientific_semantic_accuracy'] is None
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['schema_version'] == 2
    assert manifest['required_source_count_disclosed'] is False


def reviewed_metadata_for_contract_test(corpus, cases):
    """Simulate frozen review metadata to test score gates, not real human gold."""
    corpus = [record.model_copy(update={'synthetic': False, 'annotation_status': 'reviewed',
                                       'reviewers': ['contract-test-r1', 'contract-test-r2']})
              for record in corpus]
    cases = [case.model_copy(update={'synthetic': False, 'annotation_status': 'reviewed',
                                     'reviewers': ['contract-test-r1', 'contract-test-r2']})
             for case in cases]
    return corpus, cases


def test_semantic_review_can_accept_condition_aliases_without_hidden_format_penalty(study):
    corpus, cases = study
    corpus, cases = reviewed_metadata_for_contract_test(corpus, [cases[2]])
    case = cases[0].model_copy(update={'gold': cases[0].gold.model_copy(update={
        'expected_conditions': {'temperature': '80 C', 'flow': '1 mL/min'}})})
    # The natural question provides the physical conditions, not these private
    # dictionary key names or the evaluator's whitespace/unit spellings.
    assert 'temperature' not in case.question and 'flow' not in case.question
    pred = prediction(corpus, case, ['sqa-record-06', 'sqa-record-07'],
                      conditions={'온도': '80°C', '유량': '1mL/min'})
    review = Review(task_id=pred.task_id, response_sha256=pred.response_sha256,
                    semantic_pass=True, annotator='contract-test-adjudicator')
    scored = score_predictions(corpus, [case], [pred], [review], budget=BUDGET)
    row = scored['cases'][0]
    assert row['condition_recall'] == row['structural_pass'] == 0
    assert row['semantic_evidence_gate'] == row['semantic_pass'] == 1
    assert scored['aggregate']['scientific_semantic_accuracy'] == 1
    assert scored['aggregate']['semantic_review_required_cases'] == 1
    assert scored['aggregate']['semantic_review_completed_cases'] == 1
    # Without a bound review, an evidence-valid answer remains pending rather
    # than being declared semantically correct by loose format matching.
    pending = score_predictions(corpus, [case], [pred], budget=BUDGET)
    assert pending['cases'][0]['semantic_pass'] is None
    assert pending['aggregate']['scientific_semantic_accuracy'] is None


@pytest.mark.parametrize('failure', ['missing_witness', 'forged_opened'])
def test_positive_review_cannot_waive_known_witness_or_trace_integrity(study, failure):
    corpus, cases = study
    corpus, cases = reviewed_metadata_for_contract_test(corpus, [cases[2]])
    case = cases[0]
    ids = ['sqa-record-06'] if failure == 'missing_witness' else ['sqa-record-06', 'sqa-record-07']
    pred = prediction(corpus, case, ids)
    if failure == 'forged_opened':
        pred = pred.model_copy(update={'opened_ids': pred.opened_ids + ['forged-id']})
    review = Review(task_id=pred.task_id, response_sha256=pred.response_sha256,
                    semantic_pass=True, annotator='contract-test-adjudicator')
    scored = score_predictions(corpus, [case], [pred], [review], budget=BUDGET)
    assert scored['cases'][0]['semantic_evidence_gate'] == 0
    assert scored['cases'][0]['semantic_pass'] == 0
    assert scored['aggregate']['scientific_semantic_accuracy'] == 0
    if failure == 'missing_witness':
        assert scored['cases'][0]['sufficient_evidence_coverage'] == 0
    else:
        assert scored['cases'][0]['error'] == 1


def test_missing_prediction_keeps_zero_in_reviewed_semantic_denominator(study):
    corpus, cases = study
    corpus, cases = reviewed_metadata_for_contract_test(corpus, cases[:2])
    pred = prediction(corpus, cases[0], ['sqa-record-01', 'sqa-record-02'])
    review = Review(task_id=pred.task_id, response_sha256=pred.response_sha256,
                    semantic_pass=True, annotator='contract-test-adjudicator')
    scored = score_predictions(corpus, cases, [pred], [review], budget=BUDGET)
    assert scored['scheduled_cases'] == 2 and scored['missing_predictions'] == 1
    assert [r['semantic_pass'] for r in scored['cases']] == [1, 0]
    assert scored['aggregate']['scientific_semantic_accuracy'] == .5
    assert scored['aggregate']['semantic_review_required_cases'] == 1
    assert scored['aggregate']['semantic_review_completed_cases'] == 1
    assert scored['aggregate']['review_coverage'] == .5
    second = prediction(corpus, cases[1], ['sqa-record-05'])
    pending = score_predictions(corpus, cases, [pred, second], [review], budget=BUDGET)
    assert [r['semantic_pass'] for r in pending['cases']] == [1, None]
    assert pending['aggregate']['scientific_semantic_accuracy'] is None
    assert pending['aggregate']['semantic_review_required_cases'] == 2
    assert pending['aggregate']['semantic_review_completed_cases'] == 1
