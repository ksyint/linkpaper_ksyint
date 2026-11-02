"""Live discovery occurs within the public policy loop; all tests are offline."""
import hashlib
import json
from pathlib import Path

import pytest

from linkpaper_eval.agent_bench.contracts import Action, Answer, Budget, Claim, Review
from linkpaper_eval.live_paper_bench import (DemoPolicy, DemoProvider, LiveEnvironment,
    demo_extractor, execute_live, main, replay_run, save_run)
from linkpaper_eval.paper_acquisition import AcquisitionBudget, AcquisitionEnvironment


def environment(root, provider=None, budget=None):
    root.mkdir()
    acq = AcquisitionEnvironment(provider or DemoProvider(), root / 'acquisition',
        '설정 C에서 방법 M의 측정 근거는 무엇인가?',
        budget=AcquisitionBudget(max_searches=2, max_fetches=2), extractor=demo_extractor)
    return LiveEnvironment(acq, budget or Budget(max_calls=8, max_observation_chars=60000))


def record(root, factory=DemoPolicy, provider=None):
    env = environment(root, provider)
    prediction, failure = execute_live(factory, env)
    scores = save_run(env, prediction, policy_metadata={'kind': 'test_fake_policy'}, failure_stage=failure)
    return env, prediction, scores


def test_empty_store_becomes_searchable_only_after_agent_search_fetch_read(tmp_path):
    class CountingProvider(DemoProvider):
        def __init__(self):
            self.calls = []

        def search(self, query, limit):
            self.calls.append('search')
            return super().search(query, limit)

        def fetch(self, paper):
            self.calls.append('fetch')
            return super().fetch(paper)

    provider = CountingProvider()
    env = environment(tmp_path / 'live', provider)
    assert provider.calls == [] and env.documents == {}
    prediction, failure = execute_live(DemoPolicy, env)
    assert failure is None and prediction.answer is not None
    assert provider.calls == ['search', 'fetch']
    assert [e.action.tool for e in prediction.trace] == [
        'tool_catalog', 'search_papers', 'fetch_paper', 'search_local', 'open', 'open']
    assert len(prediction.opened_ids) == 2
    assert all(e.synthetic and e.annotation_status == 'fixture' for e in env.acquisition.corpus)
    scores = save_run(env, prediction)
    assert scores['structural_pass'] == 1
    assert scores['scientific_semantic_accuracy'] is None
    assert replay_run(tmp_path / 'live')['structural_pass'] == 1


def test_public_policy_gets_question_tools_and_observations_without_gold_or_required_count(tmp_path):
    class PrivacyPolicy(DemoPolicy):
        def step(self, task, history):
            assert set(task.model_dump()) == {'task_id', 'question', 'question_language'}
            encoded = json.dumps([task.model_dump(), [e.model_dump() for e in history]])
            for forbidden in ('sufficient_sets', 'reference_answers', 'task_type',
                              'study_unit_id', 'known_alternative_paper_counts'):
                assert forbidden not in encoded
            assert list(history[0].observation['tools']) == ['search_papers', 'fetch_paper', 'search_local', 'open']
            return super().step(task, history)

    _, prediction, _ = record(tmp_path / 'private', PrivacyPolicy)
    assert prediction.error is None


def test_policy_can_search_again_after_opening_evidence_in_same_episode(tmp_path):
    class AdaptivePolicy(DemoPolicy):
        def step(self, task, history):
            opened = [e for e in history if e.action.tool == 'open' and not e.error]
            searches = [e for e in history if e.action.tool == 'search_papers']
            if opened and len(searches) == 1:
                return Action(tool='search_papers', arguments={'query': 'additional verification', 'limit': 1})
            return super().step(task, history)

    _, prediction, scores = record(tmp_path / 'adaptive', AdaptivePolicy)
    tools = [e.action.tool for e in prediction.trace]
    assert tools.count('search_papers') == 2 and tools.index('open') < len(tools) - 1
    assert scores['structural_pass'] == 1
    assert replay_run(tmp_path / 'adaptive')['replay_validated']


def test_network_failure_is_retained_without_a_scientific_score(tmp_path):
    class FailureProvider(DemoProvider):
        def search(self, query, limit):
            raise TimeoutError('sensitive connection internals')

    _, prediction, scores = record(tmp_path / 'failed', provider=FailureProvider())
    assert scores['scheduled_episodes'] == 1 and scores['failed_episodes'] == 1
    assert scores['tool_failures_by_stage'] == {'discovery': 1}
    assert scores['scientific_semantic_accuracy'] is None
    assert 'sensitive connection internals' not in prediction.model_dump_json()
    replay = replay_run(tmp_path / 'failed')
    assert replay['failed_episodes'] == 1 and replay['network_calls_during_replay'] == 0


def test_fetch_parse_failure_is_separate_from_policy_failure(tmp_path):
    class FetchFailure(DemoProvider):
        def fetch(self, paper):
            raise ValueError('fixture fetch failed')

    _, _, scores = record(tmp_path / 'fetch_failed', provider=FetchFailure())
    assert scores['failed_episodes'] == 1 and not scores['model_or_policy_error']
    assert scores['tool_failures_by_stage'] == {'fetch_parse': 1}
    assert replay_run(tmp_path / 'fetch_failed')['structural_pass'] == 0


def test_policy_initialization_failure_is_one_scheduled_episode(tmp_path):
    def unavailable():
        raise RuntimeError('a secret command should not be printed')

    _, prediction, scores = record(tmp_path / 'policy_failed', unavailable)
    assert prediction.answer is None and 'secret' not in prediction.error
    assert scores['failed_episodes'] == 1 and scores['failure_stage'] == 'policy_initialization'
    assert replay_run(tmp_path / 'policy_failed')['failed_episodes'] == 1


@pytest.mark.parametrize('unknown', [False, True])
def test_citation_requires_known_fetched_and_opened_passage(tmp_path, unknown):
    class CiteWithoutReading(DemoPolicy):
        def step(self, task, history):
            fetch = [e for e in history if e.action.tool == 'fetch_paper' and not e.error]
            if fetch:
                identifier = 'fabricated-id' if unknown else fetch[0].observation['documents'][0]['document_id']
                return Answer(answer='근거 없는 예시 답입니다.',
                    claims=[Claim(text='열지 않은 문헌을 인용한 음성 대조입니다.', citations=[identifier])])
            return super().step(task, history)

    _, _, scores = record(tmp_path / ('unknown' if unknown else 'unopened'), CiteWithoutReading)
    assert scores['citation_read_validity'] == scores['structural_pass'] == 0
    assert scores['failed_episodes'] == 1


def test_agent_cannot_fetch_an_undiscovered_paper(tmp_path):
    env = environment(tmp_path / 'undiscovered')
    observation = env.call(Action(tool='fetch_paper', arguments={'paper_id': '0000.00001v1'}))
    assert 'error' in observation and 'Discover' in observation['error']
    assert not env.documents and env.trace[-1].error


def test_artifact_tampering_is_rejected_before_replay(tmp_path):
    root = tmp_path / 'tamper'
    record(root)
    with (root / 'trace.jsonl').open('a') as f:
        f.write('\n')
    with pytest.raises(ValueError, match='checksum mismatch'):
        replay_run(root)


def refresh_hashes(root, names):
    path = root / 'manifest.json'
    manifest = json.loads(path.read_text())
    for name in names:
        manifest['artifact_sha256'][name] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    path.write_text(json.dumps(manifest))


def test_frozen_replay_recomputes_open_even_when_trace_and_prediction_hashes_are_refreshed(tmp_path):
    root = tmp_path / 'forged_observation'
    record(root)
    prediction = json.loads((root / 'prediction.json').read_text())
    for event in prediction['trace']:
        if event['action']['tool'] == 'open':
            event['observation']['text'] = 'This invented observation was never in the captured PDF corpus.'
            break
    (root / 'prediction.json').write_text(json.dumps(prediction))
    (root / 'trace.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in prediction['trace']))
    refresh_hashes(root, ['prediction.json', 'trace.jsonl'])
    with pytest.raises(ValueError, match='observation mismatch'):
        replay_run(root)


def test_modified_initial_catalog_is_not_trusted(tmp_path):
    root = tmp_path / 'forged_catalog'
    record(root)
    prediction = json.loads((root / 'prediction.json').read_text())
    prediction['trace'][0]['observation']['tools']['read_gold'] = {'arguments': {}}
    (root / 'prediction.json').write_text(json.dumps(prediction))
    (root / 'trace.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in prediction['trace']))
    refresh_hashes(root, ['prediction.json', 'trace.jsonl'])
    with pytest.raises(ValueError, match='initial live tool catalog'):
        replay_run(root)


def test_hash_bound_response_review_does_not_automatically_become_benchmark_gold(tmp_path):
    root = tmp_path / 'reviews'
    _, prediction, _ = record(root)
    review = Review(task_id=prediction.task_id, response_sha256=prediction.response_sha256,
                    semantic_pass=True, annotator='test-only fictional reviewer')
    report = replay_run(root, [review])
    assert report['human_response_review'] is True
    assert report['scientific_semantic_accuracy'] is None and not report['gold_available']
    stale = review.model_copy(update={'response_sha256': '0' * 64})
    with pytest.raises(ValueError, match='Review task/response checksum'):
        replay_run(root, [stale])


def test_unknown_result_group_reference_cannot_receive_structural_credit(tmp_path):
    class ForgedGroup(DemoPolicy):
        def step(self, task, history):
            decision = super().step(task, history)
            if isinstance(decision, Answer):
                return decision.model_copy(update={'study_groups': {'never-discovered': 'invented-group'}})
            return decision

    _, _, scores = record(tmp_path / 'forged_group', ForgedGroup)
    assert scores['citation_read_validity'] == 1
    assert scores['group_reference_validity'] == scores['structural_pass'] == 0
    assert replay_run(tmp_path / 'forged_group')['failed_episodes'] == 1


def test_original_response_review_is_snapshotted_and_replayed_with_its_hash(tmp_path):
    root = tmp_path / 'saved_review'
    env = environment(root)
    prediction, _ = execute_live(DemoPolicy, env)
    review = Review(task_id=prediction.task_id, response_sha256=prediction.response_sha256,
                    semantic_pass=False, annotator='fictional test-only reviewer')
    save_run(env, prediction, reviews=[review])
    assert replay_run(root)['human_response_review'] is False
    assert 'response_reviews.jsonl' in json.loads((root / 'manifest.json').read_text())['artifact_sha256']


def test_budget_exhaustion_is_a_failed_scheduled_episode(tmp_path):
    class NeverFinish:
        def step(self, task, history):
            return Action(tool='search_local', arguments={'query': 'anything'})

    env = environment(tmp_path / 'budget', budget=Budget(max_calls=2))
    prediction, failure = execute_live(NeverFinish, env)
    scores = save_run(env, prediction, failure_stage=failure)
    assert scores['failed_episodes'] == 1 and scores['failure_stage'] == 'budget'
    assert replay_run(tmp_path / 'budget')['failed_episodes'] == 1


def test_cpu_cli_demo_then_network_free_replay(tmp_path, capsys):
    root = tmp_path / 'cli'
    assert main(['run-demo', '--question', '방법과 측정 근거를 찾아 설명하라.', '--out', str(root)]) == 0
    assert main(['replay', '--run-dir', str(root)]) == 0
    assert '"network_calls_during_replay": 0' in capsys.readouterr().out
    with pytest.raises(FileExistsError):
        main(['run-demo', '--question', '기존 결과를 덮어쓰지 않는다.', '--out', str(root)])
