"""The external-agent boundary carries only public observations and fails closed."""
import json
import sys

import pytest

from linkpaper_eval.agent_bench.contracts import Action, PublicTask, ToolEvent
from linkpaper_eval.agent_bench_policy import JsonCommandPolicy, factory


def task():
    return PublicTask(task_id='opaque', question='어떤 근거인가?', question_language='ko')


def test_command_receives_only_public_dtos(tmp_path):
    child = tmp_path / 'policy.py'
    child.write_text('''import json,sys
p=json.load(sys.stdin)
assert set(p)=={'schema_version','task','history'}
assert set(p['task'])=={'task_id','question','question_language'}
assert 'gold' not in p
print(json.dumps({'tool':'search','arguments':{'query':p['task']['question']}}))
''')
    policy = JsonCommandPolicy([sys.executable, str(child)])
    assert policy.child_environment['CUDA_VISIBLE_DEVICES'] == ''
    decision = policy.step(task(), [ToolEvent(action=Action(tool='search'), error='Unknown tool')])
    assert decision.tool == 'search' and decision.arguments['query'] == task().question


def test_child_stderr_and_command_values_are_not_exposed():
    policy = JsonCommandPolicy([sys.executable, '-c', "import sys;sys.stderr.write('secret');sys.exit(7)"])
    with pytest.raises(RuntimeError, match='Policy exited with status 7') as error:
        policy.step(task(), [])
    assert 'secret' not in str(error.value)


def test_timeout_and_malformed_decisions_fail():
    with pytest.raises(RuntimeError, match='timeout'):
        JsonCommandPolicy([sys.executable, '-c', 'import time;time.sleep(2)'], .05).step(task(), [])
    with pytest.raises(ValueError):
        JsonCommandPolicy([sys.executable, '-c', "print('{not json')"]).step(task(), [])
    with pytest.raises(ValueError):
        JsonCommandPolicy([sys.executable, '-c', "print('{\"tool\":\"search\",\"gold\":1}')"]).step(task(), [])


def test_explicit_argv_factory_and_no_shell(monkeypatch):
    monkeypatch.setenv('LINKPAPER_POLICY_COMMAND_JSON', json.dumps([sys.executable, '-c', 'print(1)']))
    assert factory().command[0] == sys.executable
    monkeypatch.setenv('LINKPAPER_POLICY_COMMAND_JSON', 'python policy.py')
    with pytest.raises(ValueError):
        factory()
    with pytest.raises(ValueError):
        JsonCommandPolicy('python policy.py')


@pytest.mark.parametrize('selected', [0, 3, 7])
def test_gpu_child_uses_explicit_selected_uuid(monkeypatch, selected):
    calls = []
    def pin(index):
        calls.append(index)
        return f'GPU-physical-{index}'
    monkeypatch.setattr('linkpaper_eval.research_bench.local.pin_gpu', pin)
    policy = JsonCommandPolicy([sys.executable], use_gpu=True, gpu_index=selected)
    assert calls == [selected]
    assert policy.child_environment['CUDA_VISIBLE_DEVICES'] == f'GPU-physical-{selected}'


def test_gpu_policy_needs_explicit_allocation(monkeypatch):
    with pytest.raises(ValueError, match='explicit allocated'):
        JsonCommandPolicy([sys.executable], use_gpu=True)
    monkeypatch.setenv('LINKPAPER_POLICY_COMMAND_JSON', json.dumps([sys.executable]))
    monkeypatch.setenv('LINKPAPER_POLICY_USES_GPU', '1')
    monkeypatch.delenv('LINKPAPER_POLICY_GPU_INDEX', raising=False)
    with pytest.raises(ValueError, match='allocated physical'):
        factory()


def test_top_level_agent_and_metric_commands(tmp_path):
    from pathlib import Path
    from linkpaper_eval.cli import main
    assert main(['agent', 'validate']) == 0
    fixture = Path(__file__).resolve().parents[1] / 'fixtures/lineage_metric/synthetic_triplets.json'
    output = tmp_path / 'score.json'
    assert main(['lineage-metric', '--input', str(fixture), '--output', str(output)]) == 0
    assert json.loads(output.read_text())['family_macro_GLRS'] == .5
    with pytest.raises(SystemExit) as error:
        main(['agent-lineage', '--help'])
    assert error.value.code == 0
