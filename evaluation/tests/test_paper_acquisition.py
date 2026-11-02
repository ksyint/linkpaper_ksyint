"""Acquisition contracts, offline replay, cache integrity and bounded HTTP."""
import io
import json
from pathlib import Path

import httpx
import pytest

from linkpaper_eval.agent_bench.contracts import Action, Evidence
from linkpaper_eval.paper_acquisition import (
    AcquisitionBudget, AcquisitionEnvironment, ArxivProvider, Paper,
    QueryFetchPolicy, ReplayProvider, SearchResult, extract_pdf, parse_atom,
    run_acquisition, sha, validate_id,
)

ATOM = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
<id>http://arxiv.org/abs/1502.03167v3</id><title> Original paper </title>
<summary>Original abstract</summary><published>2015-02-11</published>
<updated>2015-03-02</updated><author><name>A Researcher</name></author>
</entry></feed>'''
PDF = b'%PDF-1.4 synthetic test bytes only'


class FakeProvider:
    name = 'synthetic_test_provider'

    def __init__(self):
        self.calls = []

    def search(self, query, limit):
        self.calls.append(('search', query, limit))
        return SearchResult(parse_atom(ATOM), ATOM, 'https://export.arxiv.org/api/query')

    def fetch(self, paper):
        self.calls.append(('fetch', paper.paper_id))
        return PDF


def pages(data, limit):
    assert data == PDF
    return [(1, '  Fixture evidence about the requested scientific question.  ')]


def run(tmp_path, name='run', provider=None, **kwargs):
    provider = provider or FakeProvider()
    environment = AcquisitionEnvironment(provider, tmp_path / name, '어떤 조건에서 결과가 보고되었는가?',
                                          extractor=pages, **kwargs)
    manifest = run_acquisition(environment, QueryFetchPolicy(['topic'], limit=1, max_fetches=1))
    return environment, manifest, provider


def test_discovery_fetch_freeze_contains_no_fabricated_gold(tmp_path):
    env, manifest, provider = run(tmp_path)
    assert manifest['status'] == 'completed'
    assert manifest['parsed_papers'] == manifest['evidence_records'] == 1
    assert manifest['publication_ready'] is manifest['gold_available'] is False
    assert set(env.task.model_dump()) == {'task_id', 'question', 'question_language'}
    record = Evidence.model_validate_json((env.out / 'corpus.jsonl').read_text())
    assert record.paper_id == 'arxiv:1502.03167'
    assert record.paper_version == 'v3'
    assert record.study_unit_id is None and record.reviewers == []
    assert record.annotation_status == 'draft' and not record.synthetic
    assert 'Unverified' in record.license
    assert record.source_locator.endswith('characters 2:59')
    assert provider.calls == [('search', 'topic', 1), ('fetch', '1502.03167v3')]
    for name, checksum in manifest['artifact_sha256'].items():
        assert sha((env.out / name).read_bytes()) == checksum
    assert not any(name.startswith('cache/') for name in manifest['artifact_sha256'])


def test_existing_output_is_never_overwritten(tmp_path):
    run(tmp_path)
    with pytest.raises(FileExistsError):
        run(tmp_path)


def test_warm_cache_does_not_call_network_and_cold_cache_bypasses_reads(tmp_path):
    cache = tmp_path / 'shared-cache'
    first, _, _ = run(tmp_path, cache=cache)
    second, report, provider = run(tmp_path, 'warm', cache=cache, cache_mode='warm')
    assert provider.calls == []
    assert report['status'] == 'completed'
    assert all(t['observation'].get('cache_hit') for t in second.trace[:-1])
    _, _, cold_provider = run(tmp_path, 'cold-again', cache=cache)
    assert len(cold_provider.calls) == 2


def test_corrupt_cache_fails_visibly_instead_of_fetching_silently(tmp_path):
    cache = tmp_path / 'shared-cache'
    run(tmp_path, cache=cache)
    next(cache.glob('search-*.bin')).write_bytes(b'corrupt')
    env, report, provider = run(tmp_path, 'warm', cache=cache, cache_mode='warm')
    assert report['status'] == 'failed'
    assert report['tool_failures'] == 1
    assert provider.calls == []
    assert 'checksum' in env.trace[0]['error']


def test_recorded_provider_replays_without_network_and_rejects_tampering(tmp_path):
    original, _, _ = run(tmp_path)
    replay, report, _ = run(tmp_path, 'replay', provider=ReplayProvider(original.out))
    assert report['status'] == 'completed'
    assert [e.model_dump() for e in replay.corpus] == [e.model_dump() for e in original.corpus]
    metadata = original.paper_attempts[0]
    (original.out / metadata['pdf_file']).write_bytes(b'%PDF-altered')
    env, report, _ = run(tmp_path, 'bad-replay', provider=ReplayProvider(original.out))
    assert report['status'] == 'failed' and not env.corpus
    assert any('checksum' in (t['error'] or '') for t in env.trace)


def test_replay_requires_the_same_query_and_limit(tmp_path):
    original, _, _ = run(tmp_path)
    replay = ReplayProvider(original.out)
    with pytest.raises(ValueError, match='absent'):
        replay.search('different topic', 1)
    with pytest.raises(ValueError, match='absent'):
        replay.search('topic', 2)


def test_unseen_paper_cannot_be_fetched_by_private_oracle_id(tmp_path):
    env = AcquisitionEnvironment(FakeProvider(), tmp_path / 'run', '논문 결과를 설명하시오', extractor=pages)
    result = env.call(Action(tool='fetch_paper', arguments={'paper_id': '1502.03167v3'}))
    assert 'Discover' in result['error'] and env.fetches == 0


@pytest.mark.parametrize('kind', ['pages', 'chars', 'bytes'])
def test_resource_overflow_is_an_explicit_failure_not_a_truncated_corpus(tmp_path, kind):
    budget = AcquisitionBudget(max_pdf_pages=1, max_text_chars=100, max_total_bytes=1024)
    provider = FakeProvider()
    extractor = pages
    if kind == 'pages':
        extractor = lambda data, limit: [(1, 'first'), (2, 'second')]
    elif kind == 'chars':
        extractor = lambda data, limit: [(1, 'x' * 101)]
    else:
        provider.fetch = lambda paper: b'%PDF-' + b'x' * 1024
    env = AcquisitionEnvironment(provider, tmp_path / 'run', '조건을 찾아 설명하시오', extractor=extractor, budget=budget)
    report = run_acquisition(env, QueryFetchPolicy(['topic'], 1, 1))
    assert report['status'] == 'failed' and env.corpus == []
    assert report['tool_failures'] == 1
    assert env.paper_attempts[0]['status'] == 'failed'


def test_parser_failure_preserves_downloaded_pdf_and_failure_denominator(tmp_path):
    def broken(data, limit):
        raise ValueError('PDF has no extractable text; OCR is not provided')
    env = AcquisitionEnvironment(FakeProvider(), tmp_path / 'run', '어떤 결론인가?', extractor=broken)
    report = run_acquisition(env, QueryFetchPolicy(['topic'], 1, 1))
    assert report['status'] == 'failed' and report['fetch_attempts'] == 1
    assert env.paper_attempts[0]['pdf_sha256'] == sha(PDF)
    assert env.paper_attempts[0]['status'] == 'failed'
    assert 'OCR' in env.trace[1]['error']


def test_policy_receives_only_public_task_and_cannot_mutate_history(tmp_path):
    class Policy:
        def step(self, task, history):
            assert set(task.model_dump()) == {'task_id', 'question', 'question_language'}
            if not history:
                return Action(tool='search_papers', arguments={'query': 'topic', 'limit': 1})
            history[0]['observation']['results'].clear()
            return Action(tool='finish')
    env = AcquisitionEnvironment(FakeProvider(), tmp_path / 'run', '근거를 찾아 답하시오', extractor=pages)
    report = run_acquisition(env, Policy())
    assert len(env.trace[0]['observation']['results']) == 1
    assert report['status'] == 'failed'  # Search-only acquisition is not a usable QA corpus.


def test_policy_exception_and_action_exhaustion_are_not_reported_as_success(tmp_path):
    class Broken:
        def step(self, task, history):
            raise RuntimeError('private credential must not be copied')
    env = AcquisitionEnvironment(FakeProvider(), tmp_path / 'broken', '근거를 찾아 답하시오', extractor=pages)
    report = run_acquisition(env, Broken())
    assert report['policy_error'] == 'RuntimeError'
    assert 'private credential' not in json.dumps(report)
    env = AcquisitionEnvironment(FakeProvider(), tmp_path / 'limited', '근거를 찾아 답하시오', extractor=pages,
                                 budget=AcquisitionBudget(max_actions=2))
    report = run_acquisition(env, QueryFetchPolicy(['topic'], 1, 1))
    assert report['status'] == 'partial' and not env.finished


def test_atom_identifier_validation_and_no_external_entity_expansion():
    papers = parse_atom(ATOM)
    assert papers[0].paper_id == '1502.03167v3'
    assert papers[0].authors == ['A Researcher']
    for bad in ('../secret', '1502.03167?token=x', '1502.03167v0', 'http://localhost/'):
        with pytest.raises(ValueError):
            validate_id(bad)
    with pytest.raises(ValueError, match='Unexpected XML'):
        parse_atom(b'<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><feed/>')
    with pytest.raises(ValueError):
        parse_atom(ATOM.replace(b'http://arxiv.org/abs/', b'http://localhost/abs/'))


def test_official_provider_streams_validates_redirects_and_applies_rate_limit():
    urls, sleeps = [], []
    times = iter([0., 0., 0., 3.])
    def handle(request):
        urls.append(str(request.url))
        if request.url.path == '/api/query':
            return httpx.Response(200, content=ATOM)
        return httpx.Response(200, content=PDF)
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        provider = ArxivProvider(client=client, clock=lambda: next(times), sleep=sleeps.append)
        paper = provider.search('topic', 1).papers[0]
        assert provider.fetch(paper) == PDF
    assert sleeps == [3.]
    assert urls[0].startswith('https://export.arxiv.org/api/query?')
    assert urls[1] == 'https://arxiv.org/pdf/1502.03167v3'
    def redirect(request):
        return httpx.Response(302, headers={'location': 'http://127.0.0.1/private'})
    with httpx.Client(transport=httpx.MockTransport(redirect)) as client:
        with pytest.raises(ValueError, match='allowlist'):
            ArxivProvider(client=client, min_interval=0).fetch(paper)


def test_official_provider_enforces_stream_byte_limit_and_rejects_html():
    for payload, message in [(b'x' * 21, 'byte budget'), (b'<html>blocked</html>', 'not a PDF')]:
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=payload))) as client:
            with pytest.raises(ValueError, match=message):
                ArxivProvider(client=client, min_interval=0, max_pdf_bytes=20).fetch(Paper(paper_id='1502.03167v3', title='Paper'))


def test_real_pdf_cpu_parser_rejects_empty_and_page_overflow():
    pypdf = pytest.importorskip('pypdf')
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    body = io.BytesIO(); writer.write(body)
    with pytest.raises(ValueError, match='no extractable text'):
        extract_pdf(body.getvalue(), 1)
    writer.add_blank_page(width=100, height=100)
    body = io.BytesIO(); writer.write(body)
    with pytest.raises(ValueError, match='page budget'):
        extract_pdf(body.getvalue(), 1)


def test_replay_preserves_repeated_query_occurrences_and_metadata_integrity(tmp_path):
    class Changing(FakeProvider):
        def search(self, query, limit):
            title = 'First response' if not self.calls else 'Second response'
            self.calls.append(('search', query, limit))
            body = ATOM.replace(b'Original paper', title.encode())
            return SearchResult(parse_atom(body), body, 'https://export.arxiv.org/api/query')
    env = AcquisitionEnvironment(Changing(), tmp_path / 'run', '근거를 찾으시오', extractor=pages)
    for _ in range(2):
        env.call(Action(tool='search_papers', arguments={'query': 'topic', 'limit': 1}))
    env.save()
    replay = ReplayProvider(env.out)
    assert replay.search('topic', 1).papers[0].title == 'First response'
    assert replay.search('topic', 1).papers[0].title == 'Second response'
    with pytest.raises(ValueError, match='absent'):
        replay.search('topic', 1)
    p = env.out / 'provider_searches.jsonl'
    p.write_text(p.read_text().replace('First response', 'Tampered title'))
    with pytest.raises(ValueError, match='metadata checksum'):
        ReplayProvider(env.out)


def test_warm_cache_is_namespaced_by_provider(tmp_path):
    cache = tmp_path / 'shared-cache'
    run(tmp_path, cache=cache)
    other = FakeProvider()
    other.name = 'different_provider'
    _, report, provider = run(tmp_path, 'other', provider=other, cache=cache, cache_mode='warm')
    assert report['status'] == 'completed'
    assert len(provider.calls) == 2


def test_actual_pdf_text_parser_feeds_a_frozen_draft_corpus(tmp_path):
    pypdf = pytest.importorskip('pypdf')
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=200, height=100)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
        DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 10 50 Td (Original synthetic measurement 42.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    pdf = io.BytesIO(); writer.write(pdf)
    assert extract_pdf(pdf.getvalue(), 1) == [(1, 'Original synthetic measurement 42.')]
    provider = FakeProvider()
    provider.fetch = lambda paper: pdf.getvalue()
    env = AcquisitionEnvironment(provider, tmp_path / 'run', '어떤 값이 보고되었는가?')
    manifest = run_acquisition(env, QueryFetchPolicy(['topic'], 1, 1))
    assert manifest['status'] == 'completed'
    assert len(env.corpus) == 1 and env.corpus[0].text == 'Original synthetic measurement 42.'
    assert env.corpus[0].annotation_status == 'draft'
