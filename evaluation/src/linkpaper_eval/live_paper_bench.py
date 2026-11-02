"""Paper discovery and reading INSIDE an agent episode, with frozen replay.

The live provider supplies scholarly metadata/PDFs, not a GUI browser. Public
policy decisions interleave discovery, acquisition, local search and reading.
Downloaded draft sources have no automatic scientific gold or lineage labels.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import re
import time

from .agent_bench.contracts import (Action, Answer, Budget, Claim, Evidence,
                                    Prediction, PublicTask, Review, ToolEvent,
                                    answer_hash, digest)
from .paper_acquisition import (AcquisitionBudget, AcquisitionEnvironment,
                                ArxivProvider, Paper, SearchResult,
                                contained_file, extract_pdf)


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def _file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _metadata(identifier, evidence):
    return {'document_id': identifier, 'paper_id': evidence.paper_id,
            'paper_version': evidence.paper_version, 'title': evidence.title,
            'source_url': evidence.source_url, 'source_locator': evidence.source_locator,
            'source_language': evidence.source_language,
            'content_sha256': evidence.content_sha256}


def tool_catalog(budget, acquisition_budget):
    return ToolEvent(action=Action(tool='tool_catalog'), observation={
        'tools': {
            'search_papers': {'description': 'Search the external scholarly metadata provider.',
                              'arguments': {'query': 'nonempty string', 'limit': 'integer 1..20'}},
            'fetch_paper': {'description': 'Download and index a previously discovered paper PDF.',
                            'arguments': {'paper_id': 'exact discovered provider ID'}},
            'search_local': {'description': 'Search passages in papers fetched during this episode.',
                             'arguments': {'query': 'nonempty string', 'limit': 'integer 1..10',
                                           'paper_id': 'optional discovered parent paper ID'}},
            'open': {'description': 'Read an indexed passage before citing its document_id.',
                     'arguments': {'document_id': 'ID returned by fetch_paper or search_local'}}},
        'citation_contract': 'Cite document_id values from successful open observations. '
                             'Search metadata does not certify full-paper evidence.',
        'budget': {'max_calls': budget.max_calls,
                   'max_observation_chars': budget.max_observation_chars,
                   'max_searches': acquisition_budget.max_searches,
                   'max_fetches': acquisition_budget.max_fetches},
        'note': 'Limits are resource caps. Required paper count and private answers are not provided.'})


class LiveEnvironment:
    """A common PublicTask/ToolEvent environment backed by a dynamic source store."""
    def __init__(self, acquisition, budget=None):
        self.acquisition = acquisition
        self.task = PublicTask.model_validate(acquisition.task.model_dump())
        self.budget = budget or Budget(max_calls=16, max_observation_chars=60000)
        self.trace = [tool_catalog(self.budget, acquisition.budget)]
        self.opened = set()
        self.calls = self.observation_chars = 0
        self.documents: dict[str, Evidence] = {}
        self.timings, self.corpus_timeline = [], []

    def _refresh(self):
        self.documents = {'d-' + digest(self.task.task_id + '|' + e.evidence_id)[:20]: e
                          for e in self.acquisition.corpus}

    def call(self, action):
        self.calls += 1
        started = time.monotonic()
        stage = {'search_papers': 'discovery', 'fetch_paper': 'fetch_parse',
                 'search_local': 'local_search', 'open': 'read'}.get(action.tool, 'tool_contract')
        try:
            if self.calls > self.budget.max_calls:
                raise ValueError('Live tool-call budget exceeded')
            args = action.arguments
            if action.tool in ('search_papers', 'fetch_paper'):
                event = self.acquisition.call(action)
                if getattr(getattr(self.acquisition, 'provider', None), 'name', '') == 'original_synthetic_demo':
                    self.acquisition.corpus = [e.model_copy(update={
                        'synthetic': True, 'annotation_status': 'fixture',
                        'license': 'CC0-1.0 original fictional protocol fixture',
                        'license_url': 'https://creativecommons.org/publicdomain/zero/1.0/'})
                        for e in self.acquisition.corpus]
                self.corpus_timeline.append([e.evidence_id for e in self.acquisition.corpus])
                self._refresh()
                if event['error']:
                    raise ValueError(event['error'])
                result = json.loads(json.dumps(event['observation'], ensure_ascii=False))
                if action.tool == 'fetch_paper':
                    source_url = 'https://arxiv.org/abs/' + args['paper_id']
                    passages = [_metadata(i, e) for i, e in self.documents.items()
                                if e.source_url == source_url]
                    # A bounded preview identifies starting passages; search_local
                    # can locate any indexed passage without enumerating all text.
                    result.update(documents=passages[:10], indexed_passages=len(passages))
            elif action.tool == 'search_local':
                if set(args) - {'query', 'limit', 'paper_id'}:
                    raise ValueError('Unknown search_local argument')
                query, limit = args.get('query'), args.get('limit', 5)
                paper_id = args.get('paper_id')
                if (not isinstance(query, str) or not 1 <= len(query.strip()) <= 1500
                        or type(limit) is not int or not 1 <= limit <= 10
                        or (paper_id is not None and not isinstance(paper_id, str))):
                    raise ValueError('search_local needs query, limit 1..10 and optional paper_id')
                terms = Counter(re.findall(r'\w+', query.casefold()))
                ranked = []
                for identifier, evidence in self.documents.items():
                    if paper_id is not None and evidence.paper_id != paper_id:
                        continue
                    words = Counter(re.findall(r'\w+', (evidence.title + ' ' + evidence.text).casefold()))
                    score = sum(min(count, words[term]) for term, count in terms.items())
                    ranked.append((score, identifier, evidence))
                ranked.sort(key=lambda item: (-item[0], item[1]))
                result = {'results': [_metadata(i, e) for _, i, e in ranked[:limit]]}
            elif action.tool == 'open':
                if set(args) != {'document_id'} or args['document_id'] not in self.documents:
                    raise ValueError('Unknown document_id or open arguments')
                identifier = args['document_id']
                evidence = self.documents[identifier]
                result = {**_metadata(identifier, evidence), 'text': evidence.text}
            else:
                # tool_catalog is initial harness metadata, never an agent tool.
                raise ValueError('Unknown live paper tool')
            size = len(_json(result))
            if self.observation_chars + size > self.budget.max_observation_chars:
                raise ValueError('Live observation budget exceeded; evidence was not truncated')
            self.observation_chars += size
            if action.tool == 'open':
                self.opened.add(action.arguments['document_id'])
            self.trace.append(ToolEvent(action=action, observation=result))
            error = None
            return result
        except Exception as exc:
            # Provider errors were sanitized by acquisition. Do not expose a
            # policy command, HTTP headers or arbitrary exception repr here.
            error = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            self.trace.append(ToolEvent(action=action, error=error))
            return {'error': error}
        finally:
            self.timings.append({'tool': action.tool, 'stage': stage,
                                 'elapsed_seconds': time.monotonic() - started,
                                 'error': error})


def execute_live(policy_factory, environment):
    """No private Case/gold reaches the plugin; tool failures remain observable."""
    failure_stage = None
    try:
        failure_stage = 'policy_initialization'
        policy = policy_factory()
        for _ in range(environment.budget.max_calls + 1):
            failure_stage = 'policy_decision'
            history = [ToolEvent.model_validate(e.model_dump(mode='json')) for e in environment.trace]
            decision = policy.step(PublicTask.model_validate(environment.task.model_dump()), history)
            if isinstance(decision, Answer):
                return Prediction(task_id=environment.task.task_id, answer=decision,
                                  response_sha256=answer_hash(decision), trace=environment.trace,
                                  opened_ids=sorted(environment.opened)), None
            if not isinstance(decision, Action):
                raise ValueError('Policy must return an Action or Answer')
            failure_stage = 'tool_execution'
            environment.call(decision)
        failure_stage = 'budget'
        raise ValueError('Live policy did not answer within the tool budget')
    except Exception as exc:
        return Prediction(task_id=environment.task.task_id, trace=environment.trace,
                          opened_ids=sorted(environment.opened),
                          error='Live episode failed: ' + type(exc).__name__), failure_stage


def _structural(prediction, environment, reviews=(), failure_stage=None):
    answer = prediction.answer
    cited = {i for claim in answer.claims for i in claim.citations} if answer else set()
    known = set(environment.documents)
    citation_valid = bool(cited) and cited <= known and cited <= environment.opened
    all_claims_cited = bool(answer) and all(claim.citations for claim in answer.claims)
    group_keys = set(answer.study_groups) if answer else set()
    asserted_groups = {i for i, group in answer.study_groups.items() if group is not None} if answer else set()
    group_refs_valid = group_keys <= known and asserted_groups <= cited and asserted_groups <= environment.opened
    structural = bool(answer) and not prediction.error and citation_valid and all_claims_cited and group_refs_valid
    if any((r.task_id, r.response_sha256) != (prediction.task_id, prediction.response_sha256) for r in reviews):
        raise ValueError('Review task/response checksum does not match the live episode')
    matching = list(reviews)
    if len(matching) > 1:
        raise ValueError('Duplicate final semantic review for one response')
    return {'scheduled_episodes': 1, 'failed_episodes': int(not structural),
            'model_or_policy_error': prediction.error is not None,
            'failure_stage': failure_stage,
            'tool_failures': sum(bool(e.error) for e in environment.trace),
            'tool_failures_by_stage': dict(Counter(t['stage'] for t in environment.timings if t['error'])),
            'citation_read_validity': float(citation_valid),
            'group_reference_validity': float(group_refs_valid),
            'all_claims_cited': float(all_claims_cited), 'structural_pass': float(structural),
            'opened_passages': len(environment.opened), 'indexed_passages': len(known),
            'discovered_papers': len(environment.acquisition.candidates),
            'acquired_papers': len(environment.acquisition.fetched),
            'human_response_review': matching[0].semantic_pass if matching else None,
            'scientific_semantic_accuracy': None, 'gold_available': False,
            'interpretation': 'Structural provenance of a live paper episode only. A response review '
                              'does not independently certify source rights, complete task gold or benchmark validity.'}


def save_run(environment, prediction, *, policy_metadata=None, reviews=(), failure_stage=None):
    root = environment.acquisition.out.parent
    reviews = list(reviews or ())
    environment.acquisition.finished = prediction.answer is not None
    acquisition = environment.acquisition.save(policy_metadata=policy_metadata,
        policy_error=prediction.error if prediction.error else None)
    files = {'task.json': environment.task.model_dump(mode='json'),
             'prediction.json': prediction.model_dump(mode='json'),
             'corpus_timeline.json': environment.corpus_timeline,
             'tool_metrics.json': environment.timings}
    for name, value in files.items():
        (root / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    (root / 'trace.jsonl').write_text(''.join(e.model_dump_json() + '\n' for e in environment.trace))
    (root / 'corpus.jsonl').write_text(''.join(e.model_dump_json() + '\n' for e in environment.acquisition.corpus))
    (root / 'response_reviews.jsonl').write_text(''.join(r.model_dump_json() + '\n' for r in reviews))
    scores = _structural(prediction, environment, reviews, failure_stage)
    (root / 'scores.json').write_text(json.dumps(scores, ensure_ascii=False, indent=2) + '\n')
    artifact_sha = {p.relative_to(root).as_posix(): _file_sha(p)
                    for p in sorted(root.rglob('*')) if p.is_file()
                    and not p.is_relative_to(environment.acquisition.cache)}
    manifest = {'schema_version': 1, 'mode': 'live_interleaved_paper_agent',
                'task': environment.task.model_dump(mode='json'),
                'budget': environment.budget.model_dump(),
                'acquisition_budget': environment.acquisition.budget.model_dump(),
                'cache_mode': environment.acquisition.cache_mode,
                'provider': acquisition['provider'],
                'synthetic_demo': acquisition['provider'] == 'original_synthetic_demo',
                'policy': policy_metadata, 'failure_stage': failure_stage,
                'scheduled_episodes': 1, 'scientific_semantic_accuracy': None,
                'acquisition_status': acquisition['status'],
                'evaluation_scope': 'Agent-directed external paper search/fetch/read within the episode; '
                    'not a scientific performance result, OS sandbox or completed production backend.',
                'time_budget_note': 'Acquisition checks elapsed time cooperatively. Configure policy '
                    'timeouts in the adapter; this loop is not a hard process deadline.',
                'module_sha256': _file_sha(Path(__file__)), 'artifact_sha256': artifact_sha}
    (root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return scores


def _verify_run(root):
    root = Path(root)
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest.get('mode') != 'live_interleaved_paper_agent':
        raise ValueError('Not a live paper agent run')
    for name, expected in manifest['artifact_sha256'].items():
        if _file_sha(contained_file(root, name)) != expected:
            raise ValueError('Live artifact checksum mismatch: ' + name)
    return manifest


class RecordedAcquisition:
    """Replay exact captured acquisition events without network or PDF parsing."""
    def __init__(self, root, manifest):
        self.root = Path(root)
        self.task = PublicTask.model_validate(manifest['task'])
        self.budget = AcquisitionBudget.model_validate(manifest['acquisition_budget'])
        self.events = [json.loads(line) for line in (self.root / 'acquisition/trace.jsonl').read_text().splitlines()]
        self.states = json.loads((self.root / 'corpus_timeline.json').read_text())
        self.all_records = {e.evidence_id: e for e in
            (Evidence.model_validate_json(line) for line in (self.root / 'corpus.jsonl').read_text().splitlines())}
        if len(self.events) != len(self.states):
            raise ValueError('Acquisition timeline length mismatch')
        self.corpus, self.candidates, self.fetched = [], {}, set()
        self.index = 0

    def call(self, action):
        if self.index >= len(self.events):
            raise ValueError('Unexpected extra acquisition action during replay')
        event, state = self.events[self.index], self.states[self.index]
        if event['action'] != action.model_dump(mode='json'):
            raise ValueError('Acquisition replay action mismatch')
        old = {e.evidence_id for e in self.corpus}
        if len(state) != len(set(state)) or not old <= set(state) or not set(state) <= self.all_records.keys():
            raise ValueError('Invalid acquired evidence timeline')
        added = set(state) - old
        if added and (action.tool != 'fetch_paper' or any(
                self.all_records[e].source_url != 'https://arxiv.org/abs/' + action.arguments['paper_id']
                for e in added)):
            raise ValueError('Evidence activated without matching fetch_paper')
        self.corpus = [self.all_records[e] for e in state]
        if action.tool == 'search_papers' and not event['error']:
            for paper in event['observation']['results']:
                self.candidates[paper['paper_id']] = paper
        if action.tool == 'fetch_paper' and (added or (event['observation'] or {}).get('already_fetched')):
            self.fetched.add(action.arguments['paper_id'])
        self.index += 1
        return event


def replay_run(root, reviews=None):
    """Recompute local tool responses and reject altered traces/citation claims."""
    root = Path(root)
    manifest = _verify_run(root)
    if reviews is None:
        reviews = [Review.model_validate_json(line) for line in
                   (root / 'response_reviews.jsonl').read_text().splitlines() if line.strip()]
    prediction = Prediction.model_validate_json((root / 'prediction.json').read_text())
    task = PublicTask.model_validate_json((root / 'task.json').read_text())
    if task.model_dump() != manifest['task'] or prediction.task_id != task.task_id:
        raise ValueError('Live task identity mismatch')
    trace = [ToolEvent.model_validate_json(line) for line in (root / 'trace.jsonl').read_text().splitlines()]
    if trace != prediction.trace:
        raise ValueError('Prediction/recorded trace mismatch')
    acquisition = RecordedAcquisition(root, manifest)
    env = LiveEnvironment(acquisition, Budget.model_validate(manifest['budget']))
    if not trace or trace[0] != env.trace[0]:
        raise ValueError('Missing or modified initial live tool catalog')
    for expected in trace[1:]:
        if expected.action.tool == 'tool_catalog':
            raise ValueError('Injected live tool catalog')
        env.call(expected.action)
        if env.trace[-1] != expected:
            raise ValueError('Live replay observation mismatch')
    if acquisition.index != len(acquisition.events):
        raise ValueError('Unused acquisition events in live run')
    if sorted(env.opened) != prediction.opened_ids:
        raise ValueError('Opened evidence assertion differs from replay')
    scores = _structural(prediction, env, reviews, manifest.get('failure_stage'))
    scores.update(replay_validated=True, network_calls_during_replay=0)
    return scores


class DemoProvider:
    """Original fictional bytes/passages for the CPU protocol demo, no network."""
    name = 'original_synthetic_demo'

    def search(self, query, limit):
        paper = Paper(paper_id='0000.00001v1', title='Original synthetic LinkPaper demo',
                      abstract='Fictional method and measurement for software validation.',
                      authors=['LinkPaper synthetic fixture'])
        body = _json({'fixture': True, 'query': query, 'limit': limit}).encode()
        return SearchResult([paper], body, 'https://arxiv.org/api/demo-fixture')

    def fetch(self, paper):
        return b'%PDF-original-fictional-protocol-fixture-not-a-real-paper'


def demo_extractor(data, max_pages):
    return [(1, 'Original fictional fixture. Method M uses setting C and measurement score 12.'),
            (2, 'Original fictional fixture. The same method M under setting C reports score 12.')]


class DemoPolicy:
    """Search/fetch/read protocol control; produces no scientific answer claim."""
    def __init__(self, query=None, limit=1):
        self.query, self.limit = query, limit

    def step(self, task, history):
        actions = [e for e in history if e.action.tool != 'tool_catalog']
        if not actions:
            return Action(tool='search_papers', arguments={'query': self.query or task.question, 'limit': self.limit})
        searches = [e for e in actions if e.action.tool == 'search_papers' and not e.error]
        fetches = [e for e in actions if e.action.tool == 'fetch_paper']
        if searches and not fetches and searches[0].observation.get('results'):
            return Action(tool='fetch_paper', arguments={'paper_id': searches[0].observation['results'][0]['paper_id']})
        local = [e for e in actions if e.action.tool == 'search_local' and not e.error]
        if fetches and not fetches[-1].error and not local:
            return Action(tool='search_local', arguments={'query': task.question, 'limit': 2})
        opened = [e for e in actions if e.action.tool == 'open' and not e.error]
        if local:
            already = {e.observation['document_id'] for e in opened}
            for item in local[-1].observation['results']:
                if item['document_id'] not in already:
                    return Action(tool='open', arguments={'document_id': item['document_id']})
        return Answer(answer='논문 검색·수집·열람의 연결을 확인한 scripted protocol smoke입니다. 답의 과학적 정확성은 평가하지 않았습니다.',
                      claims=[Claim(text='공개 도구로 전달된 근거를 열람한 프로토콜 기록입니다.',
                                    citations=[e.observation['document_id'] for e in opened])])


def _policy_factory(spec):
    if not spec or spec.count(':') != 1:
        raise ValueError('--policy must be module:factory')
    module, name = spec.split(':')
    factory = getattr(importlib.import_module(module), name)
    if not callable(factory):
        raise ValueError('Policy factory must be callable')
    path = inspect.getsourcefile(factory)
    return factory, {'kind': 'trusted_policy_plugin', 'module': module, 'factory': name,
                     'source_sha256': _file_sha(path) if path else None,
                     'boundary': 'Public DTO transport; not an OS sandbox. Credentials are not recorded.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['run-demo', 'run', 'replay', 'score'])
    parser.add_argument('--question')
    parser.add_argument('--question-language', choices=['ko', 'en'], default='ko')
    parser.add_argument('--source-language', choices=['ko', 'en', 'mixed'], default='mixed')
    parser.add_argument('--provider', choices=['demo', 'arxiv'], default='demo')
    parser.add_argument('--query', help='Demo query override; plugin policies choose their own queries.')
    parser.add_argument('--policy')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--reviews', type=Path)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--cache-mode', choices=['cold', 'warm'], default='cold')
    parser.add_argument('--max-calls', type=int, default=16)
    parser.add_argument('--max-observation-chars', type=int, default=60000)
    for name, field in AcquisitionBudget.model_fields.items():
        parser.add_argument('--' + name.replace('_', '-'),
                            type=float if name == 'max_elapsed_seconds' else int, default=field.default)
    args = parser.parse_args(argv)
    reviews = ([Review.model_validate_json(line) for line in args.reviews.read_text().splitlines() if line.strip()]
               if args.reviews else None)
    if args.command in ('replay', 'score'):
        if args.run_dir is None:
            parser.error('--run-dir is required')
        print(json.dumps(replay_run(args.run_dir, reviews), ensure_ascii=False, indent=2))
        return 0
    if not args.question or args.out is None:
        parser.error('--question and --out are required')
    if args.command == 'run' and not args.policy:
        parser.error('run requires --policy module:factory')
    if args.command == 'run' and args.provider == 'demo':
        parser.error('Use run-demo for the fictional provider; run requires an external provider')
    budget = Budget(max_calls=args.max_calls, max_observation_chars=args.max_observation_chars)
    acquisition_budget = AcquisitionBudget(**{name: getattr(args, name) for name in AcquisitionBudget.model_fields})
    args.out.mkdir(parents=True, exist_ok=False)
    provider = DemoProvider() if args.provider == 'demo' else ArxivProvider(max_pdf_bytes=acquisition_budget.max_pdf_bytes)
    extractor = demo_extractor if args.provider == 'demo' else extract_pdf
    acquisition = AcquisitionEnvironment(provider, args.out / 'acquisition', args.question,
        language=args.question_language, budget=acquisition_budget, cache=args.cache,
        cache_mode=args.cache_mode, source_language=args.source_language, extractor=extractor)
    env = LiveEnvironment(acquisition, budget)
    if args.policy:
        try:
            factory, metadata = _policy_factory(args.policy)
        except Exception:
            # Factory loading is also retained as one scheduled failed episode.
            def factory():
                raise ValueError('Policy factory could not be loaded')
            metadata = {'kind': 'unavailable_policy_plugin'}
    else:
        factory = lambda: DemoPolicy(args.query)
        metadata = {'kind': 'scripted_protocol_smoke', 'model': None,
                    'scientific_answer_claim': False, 'query_override': bool(args.query)}
    try:
        prediction, failure_stage = execute_live(factory, env)
        scores = save_run(env, prediction, policy_metadata=metadata, reviews=reviews, failure_stage=failure_stage)
    finally:
        if hasattr(provider, 'close'):
            provider.close()
    print(json.dumps(scores, ensure_ascii=False, indent=2))
    return 0 if prediction.answer is not None else 1


if __name__ == '__main__':
    raise SystemExit(main())
