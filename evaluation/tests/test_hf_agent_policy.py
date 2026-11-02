"""CPU fake-worker tests for model boundary integrity, not model performance."""
import json
from pathlib import Path
import sys

import pytest

from linkpaper_eval.agent_bench.cli import read_rows
from linkpaper_eval.agent_bench.contracts import Action, Answer, Budget, Case, Evidence, PublicTask
from linkpaper_eval.agent_bench.environment import Environment
from linkpaper_eval.agent_bench.runner import execute, run_policy
from linkpaper_eval.hf_agent_policy import HFPolicy, ModelPolicyError, WorkerClient, parse_decision

FIXTURE = Path(__file__).parents[1] / 'fixtures/agent_lineage'


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def request(self, payload):
        self.requests.append(payload)
        return self.response(payload) if callable(self.response) else self.response


def generation(value, **updates):
    return {'raw_text': json.dumps(value), 'finish_reason': 'stop', 'error': None, **updates}


def task():
    return PublicTask(task_id='public-only', question='공개 질문입니다.', question_language='ko')


def test_action_and_answer_strict_parsing():
    assert isinstance(parse_decision('{"kind":"action","tool":"search","arguments":{"query":"q"}}'), Action)
    answer = {'kind': 'answer', 'verdict': 'insufficient', 'answer': '확인 불가입니다.',
              'claims': [{'text': '현재 근거가 부족합니다.', 'citations': []}]}
    assert isinstance(parse_decision(json.dumps(answer)), Answer)


@pytest.mark.parametrize('raw', [
    '```json\n{"kind":"action","tool":"search","arguments":{}}\n```',
    'Explanation: {"kind":"action","tool":"search","arguments":{}}',
    '{"kind":"action","kind":"answer","tool":"search","arguments":{}}',
    '{"kind":"action","tool":"search","arguments":{"query":NaN}}',
    '{"kind":"action","tool":"search","arguments":{},"hidden":"gold"}',
    '{"kind":"answer","verdict":"supported","answer":"missing claims"}',
])
def test_no_json_repair_or_schema_fallback(raw):
    with pytest.raises(ModelPolicyError):
        parse_decision(raw)


@pytest.mark.parametrize('response', [
    {'raw_text': '{"kind":"action","tool":"search","arguments":{"query":"q"}}',
     'finish_reason': 'length', 'error': None},
    {'raw_text': None, 'finish_reason': 'error', 'error': 'context exceeds cap'},
    {'raw_text': 'invalid JSON', 'finish_reason': 'stop', 'error': None},
])
def test_failed_or_truncated_generation_is_logged_and_propagated(response, tmp_path):
    path = tmp_path / 'raw.jsonl'
    policy = HFPolicy(FakeTransport(response), raw_log_path=path)
    with pytest.raises(ModelPolicyError):
        policy.step(task(), [])
    record = json.loads(path.read_text())
    assert record['worker_response'] == response
    assert record['parse_status'] == 'failed'


def test_real_public_tool_observations_pass_through_policy_without_gold():
    corpus, cases = read_rows(FIXTURE / 'corpus.jsonl', Evidence), read_rows(FIXTURE / 'cases.jsonl', Case)
    def responder(public):
        history = public['history']
        if not history:
            return generation({'kind': 'action', 'tool': 'search', 'arguments': {'query': 'D1', 'limit': 4}})
        if len(history) == 1:
            identifier = history[0]['observation']['results'][0]['document_id']
            return generation({'kind': 'action', 'tool': 'open', 'arguments': {'document_id': identifier}})
        opened = history[-1]['observation']['document_id']
        return generation({'kind': 'answer', 'verdict': 'insufficient', 'answer': '부분 근거만 확인했습니다.',
                           'claims': [{'text': '확인한 문헌의 보고만 인용합니다.', 'citations': [opened]}],
                           'study_groups': {opened: 'opaque-agent-label'}})
    transport = FakeTransport(responder)
    environment = Environment(corpus, cases[0], budget=Budget(max_calls=6))
    prediction = execute(HFPolicy(transport), environment)
    assert prediction.error is None and prediction.answer is not None
    assert len(prediction.trace) == 2 and len(prediction.opened_ids) == 1
    assert set(transport.requests[0]) == {'task', 'history'}
    assert set(transport.requests[0]['task']) == {'task_id', 'question', 'question_language'}
    public_json = json.dumps(transport.requests)
    assert 'study_unit_id' not in public_json and 'sufficient_sets' not in public_json


def test_invalid_output_remains_in_all_scheduled_episode_denominators():
    corpus, cases = read_rows(FIXTURE / 'corpus.jsonl', Evidence), read_rows(FIXTURE / 'cases.jsonl', Case)
    transport = FakeTransport({'raw_text': 'not JSON', 'finish_reason': 'stop', 'error': None})
    predictions = run_policy(lambda: HFPolicy(transport), corpus, cases, Budget(max_calls=6))
    assert len(predictions) == len(cases) == 3
    assert all(p.answer is None and p.error is not None for p in predictions)
    assert len(transport.requests) == 3
    assert all(r['history'] == [] for r in transport.requests)


def test_persistent_worker_transport_fresh_episode_payload_and_clean_close(tmp_path):
    worker = tmp_path / 'fake_worker.py'
    worker.write_text('''import json,sys,os
print(json.dumps({"type":"ready","metadata":{"model_id":"CPU fake","pid":os.getpid()}}),flush=True)
for line in sys.stdin:
 r=json.loads(line)
 if r.get("command")=="shutdown":break
 decision={"kind":"action","tool":"search","arguments":{"query":r["task"]["question"],"limit":1}}
 print(json.dumps({"type":"response","request_id":r["request_id"],"raw_text":json.dumps(decision),"error":None,"finish_reason":"stop"}),flush=True)
''')
    log = tmp_path / 'raw.jsonl'
    with WorkerClient([sys.executable, '-u', str(worker)], stderr_path=tmp_path / 'stderr.log', timeout=5) as client:
        one = HFPolicy(client, raw_log_path=log).step(task(), [])
        fresh = PublicTask(task_id='fresh-task', question='새 episode 질문', question_language='ko')
        two = HFPolicy(client, raw_log_path=log).step(fresh, [])
        assert one.arguments['query'] == task().question
        assert two.arguments['query'] == fresh.question
    assert client.process.returncode == 0
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert records[1]['public_request']['history'] == []
    assert task().question not in json.dumps(records[1]['public_request'], ensure_ascii=False)
