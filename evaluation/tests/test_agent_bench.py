"""Boundary tests for original agent infrastructure, not model quality tests."""
import json
import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from linkpaper_eval.agent_bench.cli import main, read_rows
from linkpaper_eval.agent_bench.contracts import (
    Action, Answer, Budget, Case, Claim, Evidence, Prediction, Review, answer_hash,
)
from linkpaper_eval.agent_bench.environment import Environment, ToolError, validate_study
from linkpaper_eval.agent_bench.runner import LexicalPolicy, run_demo, run_policy
from linkpaper_eval.agent_bench.scoring import score_predictions

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'agent_bench'


@pytest.fixture
def study():
    return read_rows(FIXTURES / 'corpus.jsonl', Evidence), read_rows(FIXTURES / 'cases.jsonl', Case)


def test_original_fixture_is_counterbalanced_not_a_scientific_release(study):
    corpus, cases = study
    assert validate_study(corpus, cases)['cases'] == 16
    assert len(corpus) == 32
    assert {len(c.visible_evidence_ids) for c in cases} == {4}
    for tag in {'A', 'B'}:
        assert {c.gold.verdict for c in cases if c.control_tag == tag} == {
            'supported', 'refuted', 'mixed', 'insufficient'}
    assert sum(c.question_language == 'ko' for c in cases) == 8
    with pytest.raises(ValueError, match='Publication'):
        validate_study(corpus, cases, publication=True)


def test_provenance_hash_and_review_status_are_strict(study):
    corpus, _ = study
    value = corpus[0].model_dump()
    value['text'] += 'tamper'
    with pytest.raises(ValidationError, match='checksum'):
        Evidence.model_validate(value)
    value = corpus[0].model_dump()
    value['annotation_status'] = 'reviewed'
    with pytest.raises(ValidationError, match='reviewers'):
        Evidence.model_validate(value)
    value = corpus[0].model_dump()
    value['original_version'] = ' '
    with pytest.raises(ValidationError, match='provenance'):
        Evidence.model_validate(value)


@pytest.mark.parametrize('locator', [None, '  '])
def test_reviewed_real_evidence_requires_an_atomic_source_locator(study, locator):
    corpus, cases = study
    value = corpus[0].model_dump()
    value.update(annotation_status='reviewed', synthetic=False, reviewers=['r1', 'r2'], source_locator=locator)
    with pytest.raises(ValidationError, match='locator'):
        Evidence.model_validate(value)
    value['source_locator'] = 'page 2; Table 1; row M1'
    reviewed = Evidence.model_validate(value)
    env = Environment([reviewed] + corpus[1:], cases[0])
    observation = env.call(Action(tool='open', arguments={'document_id': env.public_id(reviewed.evidence_id)}))
    assert observation['source_locator'] == value['source_locator']
    assert 'study_unit_id' not in observation


def test_two_atomic_results_in_one_paper_are_allowed_with_distinct_locators(study):
    corpus, cases = study
    first = corpus[0].model_copy(update={'source_locator': 'Table 1 row 1'})
    text = first.text.replace('Study R1-A', 'Study R1-Z')
    second = first.model_copy(update={'evidence_id': 'second-atomic-record', 'text': text,
        'content_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'source_locator': 'Table 1 row 2', 'study_unit_id': 'private-other-result-unit'})
    corpus = [first] + corpus[1:] + [second]
    gold = cases[0].gold.model_copy(update={'sufficient_sets': [[first.evidence_id], [second.evidence_id]]})
    case = cases[0].model_copy(update={'visible_evidence_ids': [first.evidence_id, second.evidence_id], 'gold': gold})
    result = validate_study(corpus, [case])
    assert result['papers'] == 1
    assert first.paper_id == second.paper_id and first.study_unit_id != second.study_unit_id


def test_gold_and_study_units_never_enter_policy_inputs(study):
    corpus, cases = study
    seen = []
    class Spy(LexicalPolicy):
        def step(self, task, history):
            seen.append({'task': task.model_dump(), 'history': [e.model_dump() for e in history]})
            return super().step(task, history)
    prediction = run_policy(Spy, corpus, cases[:1])[0]
    assert prediction.error is None
    text = json.dumps(seen, ensure_ascii=False)
    for forbidden in ('"gold"', 'study_unit_id', 'private-fixture-study', 'family_id',
                      'control_tag', 'annotation_status', 'visible_evidence_ids', 'pair_id', '"split"'):
        assert forbidden not in text
    assert {event.action.tool for event in prediction.trace} == {'search', 'open', 'citations'}


def test_identifiers_are_reproducible_and_case_isolated(study):
    corpus, cases = study
    first = Environment(corpus, cases[0], seed=7)
    again = Environment(corpus, cases[0], seed=7)
    paired = Environment(corpus, cases[1], seed=7)
    assert first.task == again.task
    assert first._aliases == again._aliases
    assert set(first._aliases.values()).isdisjoint(paired._aliases.values())
    assert first.task.task_id != Environment(corpus, cases[0], seed=8).task.task_id


def test_unknown_tool_is_recorded_as_agent_failure(study):
    corpus, cases = study
    class Invalid:
        def step(self, task, history):
            return Action(tool='shell', arguments={'command': 'anything'})
    predictions = run_policy(Invalid, corpus, cases[:1])
    assert 'Unknown tool' in predictions[0].error
    assert predictions[0].trace[0].error
    score = score_predictions(corpus, cases[:1], predictions)
    assert score['aggregate']['error'] == 1
    assert score['aggregate']['structural_pass'] == 0


def test_call_budget_failure_stays_in_denominator(study):
    corpus, cases = study
    budget = Budget(max_calls=1)
    predictions = run_policy(LexicalPolicy, corpus, cases[:1], budget)
    assert 'budget exceeded' in predictions[0].error
    assert len(predictions[0].trace) == 2
    assert score_predictions(corpus, cases[:1], predictions, budget=budget)['aggregate']['error'] == 1


def test_observation_budget_does_not_truncate_or_mark_document_open(study):
    corpus, cases = study
    env = Environment(corpus, cases[0], budget=Budget(max_observation_chars=1))
    identifier = env.public_id(cases[0].visible_evidence_ids[0])
    with pytest.raises(ToolError, match='not truncated'):
        env.call(Action(tool='open', arguments={'document_id': identifier}))
    assert env.observation_chars == 0 and not env.opened
    assert env.trace[-1].observation == {}


def test_citation_traversal_requires_open_and_hides_unavailable_edges(study):
    corpus, cases = study
    case = cases[0]
    env = Environment(corpus, case)
    review = env.public_id(case.visible_evidence_ids[1])
    with pytest.raises(ToolError, match='Open the source'):
        env.call(Action(tool='citations', arguments={'document_id': review}))
    env.call(Action(tool='open', arguments={'document_id': review}))
    result = env.call(Action(tool='citations', arguments={'document_id': review}))
    assert result['results'][0]['document_id'] == env.public_id(case.visible_evidence_ids[0])
    hidden = case.model_copy(update={'visible_evidence_ids': case.visible_evidence_ids[1:]})
    second = Environment(corpus, hidden)
    review = second.public_id(case.visible_evidence_ids[1])
    second.call(Action(tool='open', arguments={'document_id': review}))
    assert second.call(Action(tool='citations', arguments={'document_id': review})) == {'results': []}


def test_search_does_not_authorize_unopened_citations(study):
    corpus, cases = study
    env = Environment(corpus, cases[0])
    result = env.call(Action(tool='search', arguments={'query': 'M1'}))
    identifier = result['results'][0]['document_id']
    answer = Answer(verdict='supported', answer='검색 결과만 인용했습니다.',
                    claims=[Claim(text='원문을 열지 않은 주장입니다.', citations=[identifier])])
    prediction = Prediction(task_id=env.task.task_id, answer=answer, trace=env.trace,
                            response_sha256=answer_hash(answer))
    score = score_predictions(corpus, cases[:1], [prediction])['aggregate']
    assert score['citation_read_validity'] == score['structural_pass'] == 0
    forged = prediction.model_copy(update={'opened_ids': [identifier]})
    assert score_predictions(corpus, cases[:1], [forged])['aggregate']['error'] == 1


def test_trace_observation_tamper_is_rejected(study):
    corpus, cases = study
    prediction = run_demo('lexical', corpus, cases[:1])[0]
    raw = prediction.model_dump()
    for event in raw['trace']:
        if event['action']['tool'] == 'open':
            event['observation']['text'] = 'fabricated result'
            break
    tampered = Prediction.model_validate(raw)
    assert score_predictions(corpus, cases[:1], [tampered])['aggregate']['error'] == 1


@pytest.mark.parametrize('new_version', [False, True])
def test_all_papers_including_background_and_versions_are_split_isolated(study, new_version):
    corpus, cases = study
    background = corpus[3]
    other_id = background.evidence_id
    if new_version:
        second = background.model_copy(update={'evidence_id': 'second-version', 'paper_version': 'v2', 'original_version': 'v2'})
        corpus = corpus + [second]
        other_id = second.evidence_id
    other = cases[2].model_copy(update={
        'split': 'test', 'visible_evidence_ids': [other_id],
        'gold': cases[6].gold})
    with pytest.raises(ValueError, match='paper/version leakage'):
        validate_study(corpus, [cases[0], other])


def test_language_pair_cannot_cross_family_or_split(study):
    corpus, cases = study
    # Isolate the language-pair guard from the stronger shared-study guard.
    corpus = [e.model_copy(update={'study_unit_id': None}) for e in corpus]
    other = cases[1].model_copy(update={'family_id': 'other-family'})
    with pytest.raises(ValueError, match='Language pair'):
        validate_study(corpus, [cases[0], other])
    duplicate = cases[1].model_copy(update={'case_id': 'duplicate-language'})
    with pytest.raises(ValueError, match='Duplicate language'):
        validate_study(corpus, [cases[0], cases[1], duplicate])


@pytest.mark.parametrize('other_split', ['dev', 'test'])
def test_shared_study_unit_across_distinct_papers_cannot_cross_family_or_split(study, other_split):
    corpus, cases = study
    shared = corpus[4].model_copy(update={'study_unit_id': corpus[0].study_unit_id})
    corpus = corpus[:4] + [shared] + corpus[5:]
    other = cases[2].model_copy(update={'split': other_split})
    with pytest.raises(ValueError, match='study.unit'):
        validate_study(corpus, [cases[0], other])
    if other_split == 'dev':
        same_family = other.model_copy(update={'family_id': cases[0].family_id})
        assert validate_study(corpus, [cases[0], same_family])['cases'] == 2


def test_publication_requires_two_reviewers_other_than_case_author(study):
    corpus, cases = study
    corpus = [e.model_copy(update={'annotation_status': 'reviewed', 'synthetic': False,
                                  'reviewers': ['reviewer-1', 'reviewer-2'],
                                  'source_locator': 'test-only reviewed metadata: page 1 span 1'}) for e in corpus]
    case = cases[0].model_copy(update={'annotation_status': 'reviewed', 'synthetic': False,
                                     'author': ' Writer ', 'reviewers': ['writer', 'Reviewer-2']})
    with pytest.raises(ValueError, match='independently reviewed cases'):
        validate_study(corpus, [case], publication=True)
    case = case.model_copy(update={'reviewers': ['writer', 'Reviewer-2', 'Reviewer-3']})
    result = validate_study(corpus, [case], publication=True)
    assert result['publication_schema_validated'] is True
    assert 'publication_ready' not in result
    assert 'not independent certification' in result['validation_scope']


def test_empty_claims_and_whitespace_claims_are_rejected():
    with pytest.raises(ValidationError):
        Answer(verdict='supported', answer='응답', claims=[])
    with pytest.raises(ValidationError):
        Claim(text='  ')
    with pytest.raises(ValidationError):
        Claim(text='...')
    with pytest.raises(ValidationError):
        Answer(verdict='supported', answer='  ', claims=[Claim(text='의미 있는 주장')])


def test_missing_predictions_and_initialization_failure_remain_failures(study):
    corpus, cases = study
    score = score_predictions(corpus, cases, [])
    assert score['scheduled_cases'] == score['missing_predictions'] == 16
    assert score['aggregate']['error'] == 1
    def failed():
        raise RuntimeError('could not initialize')
    predictions = run_policy(failed, corpus, cases)
    score = score_predictions(corpus, cases, predictions)
    assert score['missing_predictions'] == 0 and score['aggregate']['error'] == 1


def test_oracle_and_blind_are_explicit_diagnostic_controls(study):
    corpus, cases = study
    oracle = run_demo('oracle', corpus, cases)
    scores = score_predictions(corpus, cases, oracle)
    assert scores['contains_oracle']
    assert scores['aggregate']['structural_pass'] == 1
    assert scores['aggregate']['lineage_pair_agreement'] == 1
    assert scores['aggregate']['scientific_semantic_accuracy'] is None
    blind = score_predictions(corpus, cases, run_demo('blind', corpus, cases))
    assert blind['aggregate']['structural_pass'] == 0
    assert blind['aggregate']['verdict_agreement'] == .25


def test_fixture_heuristic_handles_korean_particles_in_paired_identifiers(study):
    corpus, cases = study
    scores = score_predictions(corpus, cases, run_demo('lexical', corpus, cases))
    assert scores['aggregate']['condition_recall'] == 1
    assert scores['aggregate']['lineage_pair_agreement'] == 1
    assert scores['aggregate']['structural_pass'] == 1
    assert scores['aggregate']['scientific_semantic_accuracy'] is None


def test_semantic_review_is_response_hash_bound_and_fixtures_stay_non_scientific(study):
    corpus, cases = study
    predictions = run_demo('oracle', corpus, cases[:1])
    review = Review(task_id=predictions[0].task_id, response_sha256='0' * 64,
                    semantic_pass=True, annotator='reviewer')
    with pytest.raises(ValueError, match='response-hash'):
        score_predictions(corpus, cases[:1], predictions, [review])
    bound = review.model_copy(update={'response_sha256': predictions[0].response_sha256})
    scores = score_predictions(corpus, cases[:1], predictions, [bound])
    assert scores['aggregate']['review_coverage'] == 1
    assert scores['aggregate']['scientific_semantic_accuracy'] is None


def test_oracle_never_becomes_a_scientific_score_even_with_review_metadata(study):
    corpus, cases = study
    # Deliberately modified metadata tests the control guard, not actual review.
    corpus = [e.model_copy(update={'annotation_status': 'reviewed', 'synthetic': False,
                                  'reviewers': ['r1', 'r2'],
                                  'source_locator': 'test-only reviewed metadata: page 1 span 1'}) for e in corpus]
    cases = [c.model_copy(update={'annotation_status': 'reviewed', 'synthetic': False,
                                  'reviewers': ['r1', 'r2']}) for c in cases[:1]]
    predictions = run_demo('oracle', corpus, cases)
    reviews = [Review(task_id=p.task_id, response_sha256=p.response_sha256,
                      semantic_pass=True, annotator='r1') for p in predictions]
    scores = score_predictions(corpus, cases, predictions, reviews)
    assert scores['aggregate']['scientific_semantic_accuracy'] is None
    with pytest.raises(ValueError, match='Oracle'):
        score_predictions(corpus, cases, predictions, reviews, publication=True)


def test_offline_cli_writes_complete_traces_and_manifest(tmp_path, capsys):
    assert main(['validate']) == 0
    out = tmp_path / 'demo'
    assert main(['run-demo', '--agent', 'lexical', '--out', str(out)]) == 0
    predictions = read_rows(out / 'predictions.jsonl', Prediction)
    assert len(predictions) == 16 and all(not p.error for p in predictions)
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['publication_validation'] is False
    assert json.loads((out / 'scores.json').read_text())['aggregate']['scientific_semantic_accuracy'] is None


def test_plugin_manifest_hashes_loaded_factory_source_and_marks_model_provenance_pending(tmp_path, capsys):
    from linkpaper_eval.agent_bench import runner
    out = tmp_path / 'plugin'
    assert main(['run', '--policy', 'linkpaper_eval.agent_bench.runner:BlindPolicy', '--out', str(out)]) == 0
    manifest = json.loads((out / 'manifest.json').read_text())
    expected = hashlib.sha256(Path(runner.__file__).read_bytes()).hexdigest()
    assert manifest['policy_source']['sha256'] == expected
    assert manifest['policy_source']['status'] == 'source_hashed'
    assert manifest['model_provenance']['status'] == 'externally_supplied_or_pending'
    assert manifest['model_provenance']['model_revision'] is None
