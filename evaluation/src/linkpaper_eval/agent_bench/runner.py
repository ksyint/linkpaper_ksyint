"""CPU-only offline interaction loop and explicitly synthetic demo policies."""
from __future__ import annotations

import re
from typing import Callable, Protocol

from .contracts import Action, Answer, Budget, Case, Claim, Evidence, Prediction, PublicTask, ToolEvent, answer_hash
from .environment import Environment, validate_study


class Policy(Protocol):
    def step(self, task: PublicTask, history: list[ToolEvent]) -> Action | Answer: ...


def execute(policy: Policy, environment: Environment, oracle=False) -> Prediction:
    try:
        # An answer must arrive after at most max_calls observations. An extra
        # attempted action fails explicitly instead of silently ending a trace.
        for _ in range(environment.budget.max_calls + 1):
            public_history = [ToolEvent.model_validate(e.model_dump(mode='json'))
                              for e in environment.trace]
            decision = policy.step(environment.task, public_history)
            if isinstance(decision, Answer):
                return Prediction(task_id=environment.task.task_id, answer=decision,
                                  response_sha256=answer_hash(decision), trace=environment.trace,
                                  opened_ids=sorted(environment.opened), oracle=oracle)
            if not isinstance(decision, Action):
                raise ValueError('Policy must return a strict Action or Answer')
            environment.call(decision)
        raise ValueError('Agent did not finish within the action budget')
    except Exception as exc:
        return Prediction(task_id=environment.task.task_id, trace=environment.trace,
                          opened_ids=sorted(environment.opened), oracle=oracle,
                          error=type(exc).__name__ + ': ' + str(exc))


def run_policy(policy_factory: Callable[[], Policy], corpus: list[Evidence], cases: list[Case],
               budget: Budget | None = None, seed=20261102) -> list[Prediction]:
    validate_study(corpus, cases)
    predictions = []
    for case in cases:
        environment = Environment(corpus, case, seed, budget)
        try:
            policy = policy_factory()  # Fresh policy/chat state for every case.
        except Exception as exc:
            predictions.append(Prediction(task_id=environment.task.task_id,
                               error='Policy initialization failed: ' + type(exc).__name__))
        else:
            predictions.append(execute(policy, environment))
    return predictions


class BlindPolicy:
    """Prior-only negative control: no evidence access, no performance claim."""
    def step(self, task, history):
        return Answer(verdict='supported', answer='근거 미열람 사전확률 대조군입니다.',
                      claims=[Claim(text='문헌을 열람하지 않았습니다.')])


class LexicalPolicy:
    """Simple ORIGINAL fixture heuristic, not a scientific semantic baseline."""
    def step(self, task, history):
        if not history:
            return Action(tool='search', arguments={'query': task.question, 'limit': 10})
        identifiers = [r['document_id'] for r in history[0].observation['results']]
        opened = [e for e in history if e.action.tool == 'open' and not e.error]
        if opened and not any(e.action.tool == 'citations' for e in history):
            return Action(tool='citations', arguments={'document_id': opened[0].observation['document_id']})
        already = {e.observation['document_id'] for e in opened}
        for identifier in identifiers:
            if identifier not in already:
                return Action(tool='open', arguments={'document_id': identifier})
        # Korean particles (e.g. D1에서) are Unicode word characters; ASCII
        # identifier boundaries keep the paired Korean fixture parse equivalent.
        dataset_match = re.search(r'(?<![A-Za-z0-9])D\d+(?![A-Za-z0-9])', task.question)
        dataset = dataset_match.group() if dataset_match else ''
        relevant = [e.observation['text'] for e in opened
                    if re.search(r'(?:데이터셋|dataset)\s+' + re.escape(dataset) + r'\b',
                                 e.observation['text'], re.I)]
        positive = any('결과: 개선' in t or 'result: improvement' in t.casefold() for t in relevant)
        negative = any('결과: 저하' in t or 'result: degradation' in t.casefold() for t in relevant)
        verdict = 'mixed' if positive and negative else 'supported' if positive else 'refuted' if negative else 'insufficient'
        groups = {}
        for event in opened:
            match = re.search(r'(?:실험|study)\s+(R[A-Za-z0-9-]+)', event.observation['text'], re.I)
            groups[event.observation['document_id']] = match.group(1) if match else None
        return Answer(verdict=verdict, answer='열람한 가상 문헌의 조건과 결과를 대조한 데모 응답입니다.',
                      conditions={'dataset': dataset}, study_groups=groups,
                      claims=[Claim(text=e.observation['text'], citations=[e.observation['document_id']])
                              for e in opened])


class OraclePolicy:
    """Privileged diagnostic upper control; evaluator supplies gold deliberately."""
    def __init__(self, environment, case):
        self.identifiers = [environment.public_id(e) for e in case.visible_evidence_ids]
        self.gold = case.gold
        self.units = {i: environment._documents[i].study_unit_id for i in self.identifiers}

    def step(self, task, history):
        opened = {e.observation['document_id'] for e in history if e.action.tool == 'open' and not e.error}
        for identifier in self.identifiers:
            if identifier not in opened:
                return Action(tool='open', arguments={'document_id': identifier})
        names = {unit: f'group-{n}' for n, unit in enumerate(sorted({u for u in self.units.values() if u}))}
        return Answer(verdict=self.gold.verdict, answer='정답에 접근하는 특권적 oracle 대조군입니다.',
                      conditions=self.gold.expected_conditions,
                      study_groups={i: names[u] if u else None for i, u in self.units.items()},
                      claims=[Claim(text=e.observation['text'], citations=[e.observation['document_id']])
                              for e in history if e.action.tool == 'open' and not e.error])


def run_demo(name, corpus, cases, budget=None, seed=20261102):
    validate_study(corpus, cases)
    if name != 'oracle':
        factory = {'lexical': LexicalPolicy, 'blind': BlindPolicy}[name]
        return run_policy(factory, corpus, cases, budget, seed)
    return [execute(OraclePolicy(env, case), env, oracle=True)
            for case in cases for env in [Environment(corpus, case, seed, budget)]]
