"""Public paper discovery -> PDF acquisition -> frozen draft corpus.

This stage has no gold or paper-count oracle. It is a paper API client, not a
general browser, and does not turn downloaded passages into reviewed evidence.
Run the existing agent evaluator only after separately curating the frozen data.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib
import importlib.metadata
import inspect
import io
import json
from pathlib import Path
import re
import time
from typing import Callable, Protocol
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

import httpx
from pydantic import Field

from .agent_bench.contracts import Action, Evidence, PublicTask, StrictModel, digest

ARXIV_ID = re.compile(r'^(?:\d{4}\.\d{4,5}|[a-zA-Z][a-zA-Z.\-]+/\d{7})(?:v[1-9]\d*)?$')
ALLOWED_HOSTS = {'arxiv.org', 'export.arxiv.org'}
ATOM = '{http://www.w3.org/2005/Atom}'
ARXIV = '{http://arxiv.org/schemas/atom}'
UNKNOWN_LICENSE_URL = 'https://info.arxiv.org/help/license/index.html'


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_id(value: str) -> str:
    if not isinstance(value, str) or not ARXIV_ID.fullmatch(value):
        raise ValueError('Invalid arXiv paper ID')
    return value


class Paper(StrictModel):
    paper_id: str
    title: str
    abstract: str = ''
    authors: list[str] = Field(default_factory=list)
    published: str = ''
    updated: str = ''
    license_url: str | None = None

    @property
    def source_url(self):
        return 'https://arxiv.org/abs/' + validate_id(self.paper_id)

    @property
    def pdf_url(self):
        return 'https://arxiv.org/pdf/' + validate_id(self.paper_id)


@dataclass
class SearchResult:
    papers: list[Paper]
    body: bytes
    url: str


class Provider(Protocol):
    name: str

    def search(self, query: str, limit: int) -> SearchResult: ...

    def fetch(self, paper: Paper) -> bytes: ...


class AcquisitionBudget(StrictModel):
    max_actions: int = Field(default=16, ge=1, le=100)
    max_searches: int = Field(default=3, ge=1, le=30)
    max_fetches: int = Field(default=5, ge=1, le=30)
    max_pdf_bytes: int = Field(default=16 * 1024 * 1024, ge=1024, le=64 * 1024 * 1024)
    max_total_bytes: int = Field(default=64 * 1024 * 1024, ge=1024)
    max_pdf_pages: int = Field(default=80, ge=1, le=1000)
    max_text_chars: int = Field(default=1_000_000, ge=100)
    max_elapsed_seconds: float = Field(default=180., gt=0, le=3600)
    chunk_chars: int = Field(default=3000, ge=100, le=16000)


def parse_atom(data: bytes) -> list[Paper]:
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Unexpected XML declaration')
    root = ET.fromstring(data)
    papers = []
    for entry in root.findall(ATOM + 'entry'):
        identifier = entry.findtext(ATOM + 'id', '')
        parsed = urlparse(identifier)
        if parsed.hostname not in ALLOWED_HOSTS or '/abs/' not in parsed.path:
            raise ValueError('Unexpected paper identifier in provider response')
        paper_id = validate_id(parsed.path.split('/abs/', 1)[1])
        title = ' '.join(entry.findtext(ATOM + 'title', '').split())
        if not title:
            raise ValueError('Missing paper title')
        papers.append(Paper(paper_id=paper_id, title=title,
                            abstract=' '.join(entry.findtext(ATOM + 'summary', '').split()),
                            authors=[a.findtext(ATOM + 'name', '') for a in entry.findall(ATOM + 'author')],
                            published=entry.findtext(ATOM + 'published', ''),
                            updated=entry.findtext(ATOM + 'updated', ''),
                            license_url=entry.findtext(ARXIV + 'license')))
    return papers


class ArxivProvider:
    """Sequential, rate-limited official API/PDF requests; injectable HTTP in tests."""
    name = 'arxiv'

    def __init__(self, client=None, *, request_timeout=20., min_interval=3.,
                 max_pdf_bytes=16 * 1024 * 1024, clock=time.monotonic, sleep=time.sleep):
        self.client = client or httpx.Client(timeout=request_timeout, follow_redirects=False,
                                            headers={'User-Agent': 'LinkPaper-Evaluation/0.2 (academic research)'})
        self.owns_client = client is None
        self.min_interval, self.max_pdf_bytes = min_interval, max_pdf_bytes
        self.clock, self.sleep, self.last_request = clock, sleep, None

    def close(self):
        if self.owns_client:
            self.client.close()

    @staticmethod
    def _allowed(url):
        parsed = urlparse(str(url))
        if (parsed.scheme != 'https' or parsed.hostname not in ALLOWED_HOSTS
                or parsed.username or parsed.password or parsed.port not in (None, 443)):
            raise ValueError('Provider URL is outside the arXiv allowlist')

    def _get(self, url, max_bytes, params=None):
        self._allowed(url)
        for _ in range(4):
            if self.last_request is not None:
                wait = self.min_interval - (self.clock() - self.last_request)
                if wait > 0:
                    self.sleep(wait)
            self.last_request = self.clock()
            with self.client.stream('GET', url, params=params) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    url = urljoin(str(response.url), response.headers.get('location', ''))
                    self._allowed(url)
                    params = None
                    continue
                response.raise_for_status()
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > max_bytes:
                        raise ValueError('Provider response exceeded byte budget')
                return bytes(data), str(response.url)
        raise ValueError('Provider redirect limit exceeded')

    def search(self, query, limit):
        body, url = self._get('https://export.arxiv.org/api/query', 4 * 1024 * 1024,
                              {'search_query': query, 'start': 0, 'max_results': limit,
                               'sortBy': 'relevance'})
        papers = parse_atom(body)
        if len(papers) > limit:
            raise ValueError('Provider returned more results than requested')
        return SearchResult(papers, body, url)

    def fetch(self, paper):
        body, _ = self._get(paper.pdf_url, self.max_pdf_bytes)
        if not body.startswith(b'%PDF-'):
            raise ValueError('Provider response is not a PDF')
        return body


def contained_file(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Artifact path escapes recorded run')
    return path


class ReplayProvider:
    """No network: replay the exact queries and PDF bytes recorded by an earlier run."""
    name = 'recorded_replay'

    def __init__(self, run_dir):
        self.root = Path(run_dir)
        manifest = json.loads((self.root / 'manifest.json').read_text())
        records = {}
        for name in ('provider_searches.jsonl', 'paper_attempts.jsonl'):
            data = (self.root / name).read_bytes()
            if sha(data) != manifest['artifact_sha256'].get(name):
                raise ValueError('Recorded metadata checksum mismatch')
            records[name] = [json.loads(line) for line in data.decode('utf-8').splitlines()]
        self.searches = records['provider_searches.jsonl']
        self.search_positions = {}
        self.papers = {r['paper_id']: r for r in
                       records['paper_attempts.jsonl']
                       if r.get('pdf_file')}

    def search(self, query, limit):
        matches = [r for r in self.searches if (r['query'], r['limit']) == (query, limit)]
        key = (query, limit)
        occurrence = self.search_positions.get(key, 0)
        if occurrence >= len(matches):
            raise ValueError('Query/limit is absent from recorded run')
        record = matches[occurrence]
        self.search_positions[key] = occurrence + 1
        if record.get('error'):
            raise ValueError('Recorded provider search failure: ' + record['error'])
        body = contained_file(self.root, record['raw_file']).read_bytes()
        if sha(body) != record['sha256']:
            raise ValueError('Recorded search checksum mismatch')
        return SearchResult([Paper.model_validate(p) for p in record['papers']], body, record['url'])

    def fetch(self, paper):
        record = self.papers.get(paper.paper_id)
        if record is None:
            raise ValueError('PDF is absent from recorded run')
        body = contained_file(self.root, record['pdf_file']).read_bytes()
        if sha(body) != record['pdf_sha256']:
            raise ValueError('Recorded PDF checksum mismatch')
        return body


def extract_pdf(data: bytes, max_pages: int) -> list[tuple[int, str]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError('PDF parsing needs the optional acquire extra: uv sync --project evaluation --extra acquire') from exc
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError('Encrypted PDF is not supported')
    if len(reader.pages) > max_pages:
        raise ValueError('PDF exceeds page budget; not silently truncated')
    pages = [(number, (page.extract_text() or '').replace('\x00', '').strip())
             for number, page in enumerate(reader.pages, 1)]
    if not any(text for _, text in pages):
        raise ValueError('PDF has no extractable text; OCR is not provided')
    return pages


class AcquisitionEnvironment:
    def __init__(self, provider: Provider, out: Path, question: str, *, language='ko',
                 budget=None, cache=None, cache_mode='cold', source_language='mixed',
                 extractor: Callable = extract_pdf, clock=time.monotonic):
        if not question.strip() or cache_mode not in ('cold', 'warm'):
            raise ValueError('A question and cold/warm cache mode are required')
        self.out = Path(out)
        if source_language not in ('ko', 'en', 'mixed'):
            raise ValueError('Invalid declared source language')
        cache_path = Path(cache) if cache else self.out / 'cache'
        if self.out.resolve().is_relative_to(cache_path.resolve()):
            raise ValueError('Cache must not contain the run output directory')
        self.out.mkdir(parents=True, exist_ok=False)
        (self.out / 'raw').mkdir()
        self.provider, self.budget = provider, budget or AcquisitionBudget()
        self.cache = cache_path
        self.cache.mkdir(parents=True, exist_ok=True)
        self.cache_mode, self.source_language, self.extractor = cache_mode, source_language, extractor
        self.task = PublicTask(task_id=digest('acquire|' + language + '|' + question)[:24],
                               question=question, question_language=language)
        self.clock, self.started = clock, clock()
        self.trace, self.search_records, self.paper_attempts, self.corpus = [], [], [], []
        self.candidates: dict[str, Paper] = {}
        self.fetched = set()
        self.actions = self.searches = self.fetches = self.download_bytes = self.text_chars = 0
        self.finished = False

    def _cache_paths(self, kind, key):
        base = self.cache / (kind + '-' + digest(self.provider.name + '|' + key))
        return base.with_suffix('.json'), base.with_suffix('.bin')

    def _read_cache(self, kind, key):
        meta_path, body_path = self._cache_paths(kind, key)
        if self.cache_mode != 'warm' or not meta_path.exists():
            return None
        meta = json.loads(meta_path.read_text())
        body = body_path.read_bytes()
        if sha(body) != meta['sha256']:
            raise ValueError('Cache checksum mismatch')
        return meta, body

    def _write_cache(self, kind, key, meta, body):
        meta_path, body_path = self._cache_paths(kind, key)
        body_path.write_bytes(body)
        meta_path.write_text(json.dumps({**meta, 'sha256': sha(body)}, ensure_ascii=False))

    def _check_time(self):
        if self.clock() - self.started > self.budget.max_elapsed_seconds:
            raise ValueError('Acquisition elapsed-time budget exceeded')

    def call(self, action: Action):
        started = self.clock()
        self.actions += 1
        event = {'action': action.model_dump(), 'observation': None, 'error': None}
        try:
            self._check_time()
            if self.finished or self.actions > self.budget.max_actions:
                raise ValueError('Acquisition action budget exceeded or already finished')
            if action.tool == 'finish':
                if action.arguments:
                    raise ValueError('finish takes no arguments')
                self.finished = True
                result = {'finished': True, 'fetched_papers': len(self.fetched), 'evidence_records': len(self.corpus)}
            elif action.tool == 'search_papers':
                result = self._search(action.arguments)
            elif action.tool == 'fetch_paper':
                result = self._fetch(action.arguments)
            else:
                raise ValueError('Unknown acquisition tool')
            self._check_time()
            event['observation'] = result
        except Exception as exc:
            # Do not log arbitrary provider/HTTP exception reprs, headers or credentials.
            event['error'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        event['elapsed_seconds'] = self.clock() - started
        self.trace.append(event)
        return event

    def _search(self, arguments):
        if set(arguments) - {'query', 'limit'}:
            raise ValueError('Unknown search_papers argument')
        query, limit = arguments.get('query'), arguments.get('limit', 5)
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 1500 or type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError('search_papers needs a query and limit 1..20')
        self.searches += 1
        if self.searches > self.budget.max_searches:
            raise ValueError('Search budget exceeded')
        record = {'query': query, 'limit': limit, 'error': None}
        try:
            key = json.dumps([query, limit], ensure_ascii=False)
            cached = self._read_cache('search', key)
            if cached:
                meta, body = cached
                result = SearchResult([Paper.model_validate(p) for p in meta['papers']], body, meta['url'])
            else:
                result = self.provider.search(query, limit)
            if len(result.papers) > limit or len(result.body) > 4 * 1024 * 1024:
                raise ValueError('Search response exceeds the requested result/byte budget')
            for paper in result.papers:
                validate_id(paper.paper_id)
                self.candidates[paper.paper_id] = paper
            meta = {'papers': [p.model_dump() for p in result.papers], 'url': result.url}
            self._write_cache('search', key, meta, result.body)
            path = f'raw/search-{len(self.search_records):03d}.atom'
            (self.out / path).write_bytes(result.body)
            record.update(**meta, raw_file=path, sha256=sha(result.body), cache_hit=bool(cached))
            return {'results': meta['papers'], 'cache_hit': bool(cached)}
        except Exception as exc:
            record['error'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            raise
        finally:
            self.search_records.append(record)

    def _fetch(self, arguments):
        if set(arguments) != {'paper_id'}:
            raise ValueError('fetch_paper requires paper_id only')
        identifier = validate_id(arguments['paper_id'])
        if identifier not in self.candidates:
            raise ValueError('Discover a paper with search_papers before fetching it')
        self.fetches += 1
        if self.fetches > self.budget.max_fetches:
            raise ValueError('Fetch budget exceeded')
        if identifier in self.fetched:
            return {'paper_id': identifier, 'already_fetched': True}
        paper = self.candidates[identifier]
        record = {'paper_id': identifier, 'metadata': paper.model_dump(), 'status': 'failed'}
        try:
            cached = self._read_cache('pdf', identifier)
            body = cached[1] if cached else self.provider.fetch(paper)
            if not body.startswith(b'%PDF-') or len(body) > self.budget.max_pdf_bytes:
                raise ValueError('Invalid PDF or per-paper byte budget exceeded')
            self.download_bytes += len(body)
            if self.download_bytes > self.budget.max_total_bytes:
                raise ValueError('Total PDF byte budget exceeded')
            path = 'raw/paper-' + digest(identifier)[:20] + '.pdf'
            (self.out / path).write_bytes(body)
            record.update(pdf_file=path, pdf_sha256=sha(body), pdf_bytes=len(body), cache_hit=bool(cached))
            self._write_cache('pdf', identifier, {'paper_id': identifier}, body)
            pages = self.extractor(body, self.budget.max_pdf_pages)
            if len(pages) > self.budget.max_pdf_pages:
                raise ValueError('PDF exceeds page budget; not silently truncated')
            chars = sum(len(t) for _, t in pages)
            if self.text_chars + chars > self.budget.max_text_chars:
                raise ValueError('Text budget exceeded; not silently truncated')
            passages = []
            version = re.search(r'v\d+$', identifier)
            base_id = identifier[:version.start()] if version else identifier
            ver = version.group() if version else 'unversioned-api-id; check before publication'
            for page, text in pages:
                for start in range(0, len(text), self.budget.chunk_chars):
                    raw_chunk = text[start:start + self.budget.chunk_chars]
                    chunk = raw_chunk.strip()
                    if not chunk:
                        continue
                    offset_start = start + len(raw_chunk) - len(raw_chunk.lstrip())
                    offset_end = start + len(raw_chunk.rstrip())
                    passages.append(Evidence(evidence_id='acq-' + digest(f'{identifier}|{page}|{start}|{chunk}')[:24],
                        paper_id='arxiv:' + base_id, paper_version=ver, original_version=ver,
                        title=paper.title, text=chunk, source_language=self.source_language,
                        source_url=paper.source_url, source_locator=f'PDF page {page}; extracted text characters {offset_start}:{offset_end}',
                        license='Unverified article rights; verify exact source version before publication',
                        license_url=paper.license_url or UNKNOWN_LICENSE_URL, content_sha256=digest(chunk),
                        annotation_status='draft', synthetic=False, study_unit_id=None, reviewers=[]))
            if not passages:
                raise ValueError('PDF has no extractable text; OCR is not provided')
            self.text_chars += chars
            self.corpus.extend(passages)
            self.fetched.add(identifier)
            record.update(status='parsed', pages=len(pages), text_chars=chars, evidence_records=len(passages))
            return {'paper_id': identifier, 'cache_hit': bool(cached), 'pages': len(pages),
                    'evidence_records': len(passages), 'text_chars': chars}
        except Exception as exc:
            record['error'] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            raise
        finally:
            self.paper_attempts.append(record)

    def save(self, *, policy_metadata=None, policy_error=None):
        for name, rows in [('trace.jsonl', self.trace), ('provider_searches.jsonl', self.search_records),
                           ('paper_attempts.jsonl', self.paper_attempts)]:
            (self.out / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
        (self.out / 'corpus.jsonl').write_text(''.join(e.model_dump_json() + '\n' for e in self.corpus))
        failures = sum(bool(e['error']) for e in self.trace) + bool(policy_error)
        status = 'failed' if not self.corpus else ('partial' if failures or not self.finished else 'completed')
        artifacts = {p.relative_to(self.out).as_posix(): sha(p.read_bytes())
                     for p in sorted(self.out.rglob('*')) if p.is_file() and not p.is_relative_to(self.cache)}
        try:
            parser_version = importlib.metadata.version('pypdf')
        except importlib.metadata.PackageNotFoundError:
            parser_version = None
        manifest = {'schema_version': 1, 'stage': 'paper_acquisition_then_freeze', 'status': status,
                    'provider': self.provider.name, 'task': self.task.model_dump(),
                    'budget': self.budget.model_dump(), 'cache_mode': self.cache_mode,
                    'actions': self.actions, 'search_attempts': self.searches, 'fetch_attempts': self.fetches,
                    'parsed_papers': len(self.fetched), 'evidence_records': len(self.corpus),
                    'downloaded_pdf_bytes_including_cache': self.download_bytes,
                    'elapsed_seconds': self.clock() - self.started, 'tool_failures': failures,
                    'policy_error': policy_error, 'policy': policy_metadata,
                    'source_language_declaration': self.source_language,
                    'source_language_note': 'Caller declaration, not automatic language verification; mixed default is provisional.',
                    'publication_ready': False, 'gold_available': False,
                    'evaluation_boundary': 'Curate/map frozen records to private cases before QA scoring; no dynamic gold or end-to-end scientific score here.',
                    'time_budget_note': 'Cooperative between-step and post-call checks; HTTP timeout is separate, not a hard process deadline.',
                    'pypdf_version': parser_version, 'module_sha256': sha(Path(__file__).read_bytes()),
                    'artifact_sha256': artifacts}
        (self.out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        return manifest


class QueryFetchPolicy:
    """Explicit deterministic acquisition baseline, not a model/semantic agent."""
    def __init__(self, queries, limit=3, max_fetches=5):
        self.queries, self.limit, self.max_fetches = list(queries), limit, max_fetches
        self.query_index = 0
        self.pending, self.seen, self.attempted = [], set(), 0

    def step(self, task, history):
        if history and history[-1].get('observation'):
            for paper in history[-1]['observation'].get('results', []):
                if paper['paper_id'] not in self.seen:
                    self.seen.add(paper['paper_id'])
                    self.pending.append(paper['paper_id'])
        if self.pending and self.attempted < self.max_fetches:
            self.attempted += 1
            return Action(tool='fetch_paper', arguments={'paper_id': self.pending.pop(0)})
        if self.query_index < len(self.queries):
            query = self.queries[self.query_index]
            self.query_index += 1
            return Action(tool='search_papers', arguments={'query': query, 'limit': self.limit})
        return Action(tool='finish')


def run_acquisition(environment, policy, policy_metadata=None):
    policy_error = None
    while not environment.finished and environment.actions < environment.budget.max_actions:
        try:
            # JSON roundtrip prevents the policy from mutating evaluator history.
            history = json.loads(json.dumps(environment.trace, ensure_ascii=False))
            action = policy.step(environment.task.model_copy(), history)
            action = Action.model_validate(action)
        except Exception as exc:
            policy_error = type(exc).__name__
            break
        environment.call(action)
    return environment.save(policy_metadata=policy_metadata, policy_error=policy_error)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--question', required=True)
    parser.add_argument('--question-language', choices=['ko', 'en'], default='ko')
    parser.add_argument('--source-language', choices=['ko', 'en', 'mixed'], default='mixed')
    parser.add_argument('--provider', choices=['arxiv', 'replay'], default='arxiv')
    parser.add_argument('--replay-run', type=Path)
    parser.add_argument('--query', action='append', help='Explicit query override for the deterministic baseline; repeatable.')
    parser.add_argument('--policy', help='module:factory creating policy.step(public_task, public_history) -> Action')
    parser.add_argument('--limit', type=int, default=3)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--cache-mode', choices=['cold', 'warm'], default='cold')
    for name, field in AcquisitionBudget.model_fields.items():
        parser.add_argument('--' + name.replace('_', '-'), type=float if name == 'max_elapsed_seconds' else int,
                            default=field.default)
    args = parser.parse_args(argv)
    budget = AcquisitionBudget(**{name: getattr(args, name) for name in AcquisitionBudget.model_fields})
    if not 1 <= args.limit <= 20:
        parser.error('--limit must be 1..20')
    if args.provider == 'replay' and args.replay_run is None:
        parser.error('--replay-run is required for replay')
    provider = ReplayProvider(args.replay_run) if args.provider == 'replay' else ArxivProvider(max_pdf_bytes=budget.max_pdf_bytes)
    metadata = {'kind': 'deterministic_query_fetch_baseline', 'model': None}
    if args.policy:
        if args.policy.count(':') != 1:
            parser.error('--policy requires module:factory')
        module, factory_name = args.policy.split(':')
        factory = getattr(importlib.import_module(module), factory_name)
        policy = factory()
        source = inspect.getsourcefile(factory)
        metadata = {'kind': 'trusted_policy_plugin', 'module': module, 'factory': factory_name,
                    'source_sha256': sha(Path(source).read_bytes()) if source else None,
                    'security_boundary': 'Trusted plugin, not an OS sandbox; no gold is passed by this API.'}
    else:
        policy = QueryFetchPolicy(args.query or [args.question], args.limit, budget.max_fetches)
    environment = AcquisitionEnvironment(provider, args.out, args.question, language=args.question_language,
                                         budget=budget, cache=args.cache, cache_mode=args.cache_mode,
                                         source_language=args.source_language)
    try:
        manifest = run_acquisition(environment, policy, metadata)
    finally:
        if hasattr(provider, 'close'):
            provider.close()
    print(json.dumps({k: manifest[k] for k in ('status', 'provider', 'parsed_papers', 'evidence_records', 'tool_failures')}, ensure_ascii=False))
    return 0 if manifest['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
