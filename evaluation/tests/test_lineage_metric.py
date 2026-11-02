"""Hand-derived reported-number safeguards for the proposed GLRS metric."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from linkpaper_eval.lineage_metric import Episode, evaluate, episode_components, score_triplet

FIXTURE = Path(__file__).parents[1] / 'fixtures/lineage_metric/synthetic_triplets.json'


def trio():
    return copy.deepcopy(json.loads(FIXTURE.read_text(encoding='utf-8'))[0])


def test_perfect_has_all_components_one():
    result = score_triplet(trio())
    assert result['GLRS'] == result['I'] == result['S'] == 1
    assert [result['episodes'][w]['gold_k'] for w in ('B', 'R', 'N')] == [2, 2, 3]
    assert all(result['episodes'][w]['G'] == 1 for w in ('B', 'R', 'N'))


@pytest.mark.parametrize('policy', ['always_merge', 'always_separate'])
def test_constant_unit_count_policies_fail_new_unit_control(policy):
    row = trio()
    for w in ('B', 'R', 'N'):
        row[w]['study_groups'] = {d: ('one' if policy == 'always_merge' else d) for d in row[w]['gold_units']}
    result = score_triplet(row)
    assert result['GLRS'] == result['S'] == 0
    # Ordinary document B³ can be positive despite no intervention response.
    assert all(result['episodes'][w]['document_bcubed_diagnostic']['F1'] > 0 for w in ('B', 'R', 'N'))


def test_repeat_overcount_is_penalized():
    row = trio()
    row['R']['study_groups']['synthetic-a3'] = 'false-new-unit'
    result = score_triplet(row)
    assert result['predicted_repeat_delta'] == 1
    assert result['I'] == result['GLRS'] == 0


def test_no_new_unit_response_is_penalized():
    row = trio()
    row['N']['study_groups']['synthetic-c1'] = row['N']['study_groups']['synthetic-b1']
    result = score_triplet(row)
    assert result['predicted_new_delta'] == 0
    assert result['S'] == result['GLRS'] == 0


def test_opaque_cluster_renaming_is_invariant_even_between_worlds():
    row = trio()
    for w in ('B', 'R', 'N'):
        row[w]['study_groups'] = {d: f'{w}/renamed/{label}' for d, label in row[w]['study_groups'].items()}
    assert score_triplet(row)['GLRS'] == 1


def test_consistent_gold_unit_renaming_is_invariant():
    row = trio()
    for w in ('B', 'R', 'N'):
        row[w]['gold_units'] = {d: 'different-gold-id/' + label for d, label in row[w]['gold_units'].items()}
    assert score_triplet(row)['GLRS'] == 1


@pytest.mark.parametrize('missing', ['opened_ids', 'study_groups', 'cited_ids'])
def test_missing_acquisition_or_assertion_keeps_zero_in_denominator(missing):
    row = trio()
    row['R'].pop(missing)
    report = evaluate([row])
    assert report['family_macro_GLRS'] == 0
    assert report['coverage']['eligible_triplets'] == 1
    assert report['triplets'][0]['episodes']['R']['G'] == 0


def test_malformed_agent_output_is_a_failure_not_a_dropped_triplet():
    row = trio()
    row['N']['study_groups'] = ['invalid', 'partition']
    report = evaluate([row])
    assert report['family_macro_GLRS'] == 0
    assert report['coverage']['eligible_triplets_with_agent_failure'] == 1


def test_unopened_episode_and_explicit_error_score_zero():
    row = trio()
    row['R']['opened_ids'] = ['unrelated-id']
    assert score_triplet(row)['GLRS'] == 0
    row = trio()
    row['N']['error'] = 'synthetic-provider-failure'
    assert score_triplet(row)['GLRS'] == 0


def test_wrong_citation_and_omission_have_hand_computed_penalties():
    episode = Episode(question='synthetic', language='ko', conditions={},
                      gold_units={'a': 'u', 'b': 'v', 'x': None}, eligible_ids=['a', 'b'],
                      study_groups={'a': 'A', 'b': 'B', 'x': 'X'},
                      cited_ids=['a', 'b', 'x'], opened_ids=['a', 'b', 'x'])
    result = episode_components(episode)
    assert result['precision'] == pytest.approx(2 / 3)
    assert result['recall'] == 1
    assert result['G'] == pytest.approx(.8)
    omitted = episode.model_copy(update={'cited_ids': ['a'], 'study_groups': {'a': 'A'}})
    assert episode_components(omitted)['G'] == pytest.approx(2 / 3)


def test_any_adequate_duplicate_witness_and_repeated_support_are_invariant():
    episode = Episode(question='synthetic', language='ko', conditions={},
                      gold_units={'a': 'u', 'b': 'u'}, eligible_ids=['a', 'b'],
                      study_groups={'a': 'one'}, opened_ids=['a'], cited_ids=['a'])
    assert episode_components(episode)['G'] == 1
    assert episode_components(episode)['document_bcubed_diagnostic']['F1'] == pytest.approx(.4)
    repeated = episode.model_copy(update={'study_groups': {'a': 'one', 'b': 'one'},
                                          'opened_ids': ['a', 'b'], 'cited_ids': ['a', 'b', 'a']})
    assert episode_components(repeated)['G'] == 1


def test_complete_triplet_only_needs_one_admissible_witness_per_unit():
    row = trio()
    for w in ('B', 'R', 'N'):
        witnesses = {}
        for document, unit in row[w]['gold_units'].items():
            witnesses.setdefault(unit, document)
        row[w]['study_groups'] = {document: 'opaque-' + unit for unit, document in witnesses.items()}
        row[w]['cited_ids'] = row[w]['opened_ids'] = list(witnesses.values())
    assert score_triplet(row)['GLRS'] == 1


def retain(row, world, documents):
    row[world]['study_groups'] = {d: row[world]['study_groups'][d] for d in documents}
    row[world]['opened_ids'] = list(documents)
    row[world]['cited_ids'] = list(documents)


def test_fake_new_cluster_cannot_rescue_missing_new_witness():
    row = trio()
    retain(row, 'N', ['synthetic-a1', 'synthetic-b1'])
    assert score_triplet(row)['GLRS'] == 0
    row['N']['study_groups']['synthetic-c1'] = 'unopened-fake-new'
    result = score_triplet(row)
    assert result['S'] == 1 and result['episodes']['N']['G'] == pytest.approx(2 / 3)
    assert result['C'] == result['A'] == result['GLRS'] == 0
    assert result['certificate_failure_reasons'] == ['N:invalid_claimed_clusters']


def test_fake_old_cluster_cannot_rescue_new_count_delta():
    row = trio()
    retain(row, 'N', ['synthetic-a1', 'synthetic-c1'])
    row['N']['study_groups']['synthetic-b1'] = 'unopened-fake-old'
    result = score_triplet(row)
    assert result['S'] == result['A'] == 1
    assert result['C'] == result['GLRS'] == 0


def test_acquiring_only_previously_missed_old_unit_is_not_new_response():
    row = trio()
    retain(row, 'B', ['synthetic-a1'])
    retain(row, 'R', ['synthetic-a1'])
    retain(row, 'N', ['synthetic-a1', 'synthetic-b1'])
    result = score_triplet(row)
    assert result['C'] == result['I'] == result['S'] == 1
    assert result['A'] == result['GLRS'] == 0


def test_duplicate_supported_cluster_breaks_certificate():
    row = trio()
    row['R']['study_groups']['synthetic-a3'] = 'extra-same-unit'
    result = score_triplet(row)
    assert result['C'] == result['GLRS'] == 0
    assert result['certificate_failure_reasons'] == ['R:duplicate_supported_clusters']


def test_null_background_does_not_break_certificate():
    row = trio()
    for world in ('B', 'R', 'N'):
        row[world]['gold_units']['synthetic-background'] = None
        row[world]['study_groups']['synthetic-background'] = None
        row[world]['opened_ids'].append('synthetic-background')
        row[world]['cited_ids'].append('synthetic-background')
    result = score_triplet(row)
    assert result['C'] == result['A'] == result['GLRS'] == 1


def test_coherent_partial_coverage_can_score_positive():
    row = trio()
    retain(row, 'B', ['synthetic-a1'])
    retain(row, 'R', ['synthetic-a1'])
    retain(row, 'N', ['synthetic-a1', 'synthetic-c1'])
    result = score_triplet(row)
    assert result['C'] == result['A'] == result['I'] == result['S'] == 1
    assert result['GLRS'] == pytest.approx(2 / 3)
    row['N']['study_groups']['synthetic-b1'] = 'unopened-extra'
    assert score_triplet(row)['GLRS'] == 0


def test_splitting_one_result_into_two_claims_matches_it_once():
    episode = Episode(question='synthetic', language='ko', conditions={},
                      gold_units={'a': 'u', 'b': 'u'}, eligible_ids=['a', 'b'],
                      study_groups={'a': 'one', 'b': 'two'}, opened_ids=['a', 'b'], cited_ids=['a', 'b'])
    result = episode_components(episode)
    assert result['matched_units'] == 1 and result['predicted_k'] == 2
    assert result['G'] == pytest.approx(2 / 3)


def test_merging_different_units_has_no_certified_match():
    episode = Episode(question='synthetic', language='ko', conditions={},
                      gold_units={'a': 'u', 'b': 'v'}, eligible_ids=['a', 'b'],
                      study_groups={'a': 'one', 'b': 'one'}, opened_ids=['a', 'b'], cited_ids=['a', 'b'])
    assert episode_components(episode)['G'] == 0


def test_background_citation_is_not_a_false_unit_assertion():
    episode = Episode(question='synthetic', language='ko', conditions={},
                      gold_units={'a': 'u', 'x': None}, eligible_ids=['a'],
                      study_groups={'a': 'one', 'x': None}, opened_ids=['a', 'x'], cited_ids=['a', 'x'])
    result = episode_components(episode)
    assert result['G'] == 1 and result['background_citations'] == 1


@pytest.mark.parametrize('invalid', ['unopened_member', 'uncited_member', 'ineligible_only'])
def test_unsupported_claims_still_count_in_predicted_units(invalid):
    episode = Episode(question='synthetic', language='ko', conditions={},
                      gold_units={'a': 'u', 'b': 'u'}, eligible_ids=['a'],
                      study_groups={'a': 'good', 'b': 'unsupported'},
                      opened_ids=['a', 'b'], cited_ids=['a', 'b'])
    if invalid == 'unopened_member':
        episode = episode.model_copy(update={'opened_ids': ['a']})
    elif invalid == 'uncited_member':
        episode = episode.model_copy(update={'cited_ids': ['a']})
    result = episode_components(episode)
    assert result['predicted_k'] == 2 and result['matched_units'] == 1
    assert result['G'] == pytest.approx(2 / 3)


def test_unknown_gold_is_reported_without_inventing_independence():
    unknown = trio()
    unknown['triplet_id'] = 'unknown'
    unknown['R']['gold_units']['synthetic-a3'] = None
    known_failure = trio()
    known_failure['N']['error'] = 'failure'
    report = evaluate([unknown, known_failure])
    assert report['triplets'][0]['GLRS'] is None
    assert report['triplets'][0]['exclusion_reasons'] == ['R:unknown_gold_lineage']
    assert report['coverage']['eligible_fraction'] == .5
    assert report['family_macro_GLRS'] == 0
    assert report['coverage']['eligible_triplets_with_agent_failure'] == 1


def test_unknown_world_cannot_mask_an_invalid_other_known_control():
    row = trio()
    row['R']['gold_units']['synthetic-a3'] = None
    row['N']['gold_units']['synthetic-c1'] = 'unit-b'
    with pytest.raises(ValueError):
        score_triplet(row)


@pytest.mark.parametrize('change', ['question', 'language', 'conditions', 'document_count', 'repeat_count', 'repeat_swapped_unit', 'new_not_increased', 'new_drops_base_unit'])
def test_invalid_control_construction_raises(change):
    row = trio()
    if change == 'question':
        row['R']['question'] = 'different'
    elif change == 'language':
        row['N']['language'] = 'en'
    elif change == 'conditions':
        row['N']['conditions']['condition'] = 'different'
    elif change == 'document_count':
        row['N']['gold_units']['padding'] = None
    elif change == 'repeat_count':
        row['R']['gold_units']['synthetic-a3'] = 'new-unit'
    elif change == 'repeat_swapped_unit':
        row['R']['gold_units']['synthetic-b1'] = 'new-unit'
    elif change == 'new_not_increased':
        row['N']['gold_units']['synthetic-c1'] = 'unit-b'
    else:
        row['N']['gold_units']['synthetic-b1'] = 'new-d'
    with pytest.raises(ValueError):
        score_triplet(row)


def test_group_and_family_macro_do_not_treat_repeats_as_new_groups():
    first, repeated, second = trio(), trio(), trio()
    repeated['triplet_id'] = 'same-group-repeat'
    repeated['R']['error'] = 'failure'
    second.update(triplet_id='second', group_id='second-group', family_id='second-family')
    report = evaluate([first, repeated, second], bootstrap_samples=200, seed=7)
    assert report['triplet_macro_GLRS'] == pytest.approx(2 / 3)
    assert report['group_macro_GLRS'] == report['family_macro_GLRS'] == .75
    assert report['coverage']['total_groups'] == 2
    assert report['family_bootstrap_95'] is not None
    assert evaluate([first], bootstrap_samples=200)['family_bootstrap_95'] is None


def test_duplicate_triplets_or_inconsistent_group_family_raise():
    with pytest.raises(ValueError):
        evaluate([trio(), trio()])
    second = trio()
    second.update(triplet_id='another-id', family_id='another-family')
    with pytest.raises(ValueError):
        evaluate([trio(), second])


def test_cli_roundtrip_is_offline_and_retains_missing_response(tmp_path):
    output = tmp_path / 'scores.json'
    env = {**os.environ, 'PYTHONPATH': str(Path(__file__).parents[1] / 'src')}
    subprocess.run([sys.executable, '-m', 'linkpaper_eval.lineage_metric', '--input', str(FIXTURE),
                    '--output', str(output), '--bootstrap-samples', '100', '--seed', '3'],
                   env=env, check=True, capture_output=True, text=True)
    report = json.loads(output.read_text(encoding='utf-8'))
    assert report['family_macro_GLRS'] == .5
    assert report['coverage']['eligible_triplets'] == 2
    assert report['coverage']['missing_agent_episodes'] == 1
