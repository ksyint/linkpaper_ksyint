"""Actual tool traces, matched private controls and denominator safeguards."""
import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from linkpaper_eval.agent_bench.cli import main as agent_main, read_rows
from linkpaper_eval.agent_bench.contracts import Case, Evidence, Prediction
from linkpaper_eval.agent_bench.runner import run_demo
from linkpaper_eval.agent_lineage import TripletSpec, construct_triplets, main
from linkpaper_eval.lineage_metric import evaluate

FIXTURE = Path(__file__).resolve().parents[1] / 'fixtures' / 'agent_lineage'


@pytest.fixture
def experiment():
    corpus = read_rows(FIXTURE / 'corpus.jsonl', Evidence)
    cases = read_rows(FIXTURE / 'cases.jsonl', Case)
    specs = read_rows(FIXTURE / 'triplets.jsonl', TripletSpec)
    predictions = run_demo('lexical', corpus, cases)
    return corpus, cases, specs, predictions


def test_real_offline_tool_agent_enters_metric_without_gold_prompt_leak(experiment):
    corpus, cases, specs, predictions = experiment
    assert {c.gold.verdict for c in cases} == {'supported'}
    assert {len(c.visible_evidence_ids) for c in cases} == {4}
    assert all({e.action.tool for e in p.trace} == {'search', 'open', 'citations'} for p in predictions)
    before = [p.model_dump_json() for p in predictions]
    triplets, core = construct_triplets(corpus, cases, predictions, specs)
    report = evaluate(triplets)
    assert report['family_macro_GLRS'] == 1
    assert [report['triplets'][0]['episodes'][arm]['gold_k'] for arm in ('B', 'R', 'N')] == [2, 2, 3]
    assert report['coverage']['total_triplets'] == report['coverage']['eligible_triplets'] == 1
    assert core['aggregate']['scientific_semantic_accuracy'] is None
    assert before == [p.model_dump_json() for p in predictions]
    serialized_trace = json.dumps([e.model_dump() for p in predictions for e in p.trace])
    for private in ('private-A', 'private-B', 'private-C', 'gold_units', 'eligible_evidence_ids', 'study_unit_id'):
        assert private not in serialized_trace


@pytest.mark.parametrize('failure', ['missing', 'explicit_error', 'forged_opened', 'tampered_observation'])
def test_missing_or_invalid_new_episode_stays_scheduled_and_scores_zero(experiment, failure):
    corpus, cases, specs, predictions = experiment
    if failure == 'missing':
        predictions = predictions[:-1]
    else:
        raw = predictions[-1].model_dump()
        if failure == 'explicit_error':
            raw['error'] = 'agent failed after observing evidence'
        elif failure == 'forged_opened':
            raw['opened_ids'].append('forged-document')
        else:
            next(e for e in raw['trace'] if e['action']['tool'] == 'open')['observation']['text'] = 'tampered'
        predictions[-1] = Prediction.model_validate(raw)
    triplets, _ = construct_triplets(corpus, cases, predictions, specs)
    report = evaluate(triplets)
    assert report['family_macro_GLRS'] == 0
    assert report['coverage']['eligible_triplets'] == report['coverage']['total_triplets'] == 1
    assert report['coverage']['failed_agent_episodes'] == 1
    assert triplets[0].N.error
    assert 'forged-document' not in triplets[0].N.opened_ids


@pytest.mark.parametrize('repeat_witnesses', [
    ['bridge-source-01', 'bridge-source-02'],
    ['bridge-source-03', 'bridge-source-02'],
])
def test_explicit_alternative_eligible_witness_subsets_are_supported(experiment, repeat_witnesses):
    corpus, cases, specs, predictions = experiment
    eligible = {**specs[0].eligible_evidence_ids, 'R': repeat_witnesses}
    spec = specs[0].model_copy(update={'eligible_evidence_ids': eligible})
    triplets, _ = construct_triplets(corpus, cases, predictions, [spec])
    assert evaluate(triplets)['family_macro_GLRS'] == 1


@pytest.mark.parametrize('invalid', ['unknown_case', 'unknown_witness', 'unequal_docs', 'question', 'conditions', 'language', 'new_not_added', 'repeat_loses_unit'])
def test_invalid_private_control_construction_is_rejected(experiment, invalid):
    corpus, cases, specs, _ = experiment
    spec = specs[0]
    if invalid == 'unknown_case':
        spec = spec.model_copy(update={'N': 'does-not-exist'})
    elif invalid == 'unknown_witness':
        spec = spec.model_copy(update={'eligible_evidence_ids': {**spec.eligible_evidence_ids, 'N': ['does-not-exist']}})
    elif invalid == 'new_not_added':
        spec = spec.model_copy(update={'eligible_evidence_ids': {**spec.eligible_evidence_ids, 'N': spec.eligible_evidence_ids['B']}})
    elif invalid == 'repeat_loses_unit':
        spec = spec.model_copy(update={'eligible_evidence_ids': {**spec.eligible_evidence_ids, 'R': ['bridge-source-01']}})
    else:
        if invalid == 'unequal_docs':
            replacement = cases[-1].model_copy(update={'visible_evidence_ids': cases[-1].visible_evidence_ids[:-1]})
        elif invalid == 'question':
            replacement = cases[-1].model_copy(update={'question': '다른 질문이며 과학적 비교 조건이 다릅니다.'})
        elif invalid == 'language':
            replacement = cases[-1].model_copy(update={'question_language': 'en'})
        else:
            gold = cases[-1].gold.model_copy(update={'expected_conditions': {'dataset': 'D2'}})
            replacement = cases[-1].model_copy(update={'gold': gold})
        cases = cases[:-1] + [replacement]
    predictions = run_demo('lexical', corpus, cases)
    with pytest.raises(ValueError):
        construct_triplets(corpus, cases, predictions, [spec])


def test_duplicate_case_or_scheduled_triplet_ids_are_rejected(experiment):
    corpus, cases, specs, predictions = experiment
    raw = specs[0].model_dump()
    raw['R'] = raw['B']
    with pytest.raises(ValidationError, match='distinct'):
        TripletSpec.model_validate(raw)
    with pytest.raises(ValueError, match='unique scheduled'):
        construct_triplets(corpus, cases, predictions, specs + specs)


def test_equal_record_count_does_not_hide_unequal_source_paper_counts(experiment):
    corpus, cases, specs, _ = experiment
    # New result C may legitimately be another atomic record from A's paper,
    # but that changes the matched control's distinct source-paper count.
    corpus[3] = corpus[3].model_copy(update={'paper_id': corpus[0].paper_id})
    predictions = run_demo('lexical', corpus, cases)
    with pytest.raises(ValueError, match='source-paper counts'):
        construct_triplets(corpus, cases, predictions, specs)


def test_cli_bridges_core_predictions_and_writes_private_checksums(tmp_path, capsys):
    agent_out, evaluator_out = tmp_path / 'agent', tmp_path / 'evaluator'
    assert agent_main(['run-demo', '--corpus', str(FIXTURE / 'corpus.jsonl'),
                       '--cases', str(FIXTURE / 'cases.jsonl'), '--agent', 'lexical', '--out', str(agent_out)]) == 0
    assert main(['--corpus', str(FIXTURE / 'corpus.jsonl'), '--cases', str(FIXTURE / 'cases.jsonl'),
                 '--predictions', str(agent_out / 'predictions.jsonl'), '--triplets', str(FIXTURE / 'triplets.jsonl'),
                 '--out', str(evaluator_out)]) == 0
    report = json.loads((evaluator_out / 'glrs.json').read_text())
    assert report['family_macro_GLRS'] == 1
    manifest = json.loads((evaluator_out / 'manifest.private.json').read_text())
    assert manifest['contains_fixtures_or_drafts'] and not manifest['contains_oracle']
    assert manifest['source_sha256']['predictions'] == hashlib.sha256((agent_out / 'predictions.jsonl').read_bytes()).hexdigest()
    assert 'EVALUATOR ONLY' in manifest['scope']
    assert manifest['matched_counts']['bridge-triplet-01'] == {
        arm: {'record_count': 4, 'source_paper_count': 4} for arm in ('B', 'R', 'N')}
    private = json.loads((evaluator_out / 'triplets.private.json').read_text())
    assert set(private[0]['B']['gold_units'].values()) == {'private-A', 'private-B', None}
