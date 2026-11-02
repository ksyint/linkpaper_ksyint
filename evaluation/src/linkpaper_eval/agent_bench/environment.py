"""Allowlisted, budgeted tools over one frozen visible corpus; no network access."""
from __future__ import annotations

import json
import re
from collections import Counter

from .contracts import Action, Budget, Case, Evidence, PublicTask, ToolEvent, digest


def validate_study(corpus: list[Evidence], cases: list[Case], publication=False):
    if not corpus or not cases:
        raise ValueError('Empty corpus/cases')
    lookup = {e.evidence_id: e for e in corpus}
    if len(lookup) != len(corpus) or len({c.case_id for c in cases}) != len(cases):
        raise ValueError('Duplicate source/case ID')
    for evidence in corpus:
        if not set(evidence.cites_ids) <= lookup.keys():
            raise ValueError('Citation edge points outside frozen corpus')
    paper_splits, family_splits, pair_records, questions, pair_languages = {}, {}, {}, {}, {}
    study_units = {}
    for case in cases:
        if any(not getattr(case, name).strip() for name in
               ('case_id', 'pair_id', 'family_id', 'question', 'author', 'control_tag')):
            raise ValueError('Blank case metadata/question')
        visible = set(case.visible_evidence_ids)
        if len(visible) != len(case.visible_evidence_ids) or not visible <= lookup.keys():
            raise ValueError('Unknown/duplicate visible evidence')
        if any(not set(s) <= visible for s in case.gold.sufficient_sets):
            raise ValueError('Gold requires inaccessible evidence')
        for paper in {lookup[e].paper_id for e in visible}:
            # Includes background/citation-review/condition-shift papers, all versions.
            if paper in paper_splits and paper_splits[paper] != case.split:
                raise ValueError('Cross-split paper/version leakage: ' + paper)
            paper_splits[paper] = case.split
        for unit in {lookup[e].study_unit_id for e in visible
                     if lookup[e].study_unit_id is not None}:
            previous = study_units.get(unit)
            if previous is not None and previous[0] != case.split:
                raise ValueError('Cross-split study-unit leakage: ' + unit)
            if previous is not None and previous[1] != case.family_id:
                raise ValueError('Shared study unit requires one family_id: ' + unit)
            study_units[unit] = (case.split, case.family_id)
        for mapping, key in ((family_splits, case.family_id),
                             (questions, ' '.join(case.question.casefold().split()))):
            if key in mapping and mapping[key] != case.split:
                raise ValueError('Cross-split family/question leakage')
            mapping[key] = case.split
        if case.question_language in pair_languages.setdefault(case.pair_id, set()):
            raise ValueError('Duplicate language within a paired group')
        pair_languages[case.pair_id].add(case.question_language)
        if case.pair_id in pair_records:
            previous = pair_records[case.pair_id]
            if (previous.split, previous.family_id, set(previous.visible_evidence_ids), previous.gold) != (
                case.split, case.family_id, visible, case.gold
            ):
                raise ValueError('Language pair must share split/family/world/gold and differ in language')
        else:
            pair_records[case.pair_id] = case
        independent_reviewers = {name.strip().casefold() for name in case.reviewers
                                 if name.strip() and name.strip().casefold() != case.author.strip().casefold()}
        if publication and (case.synthetic or case.annotation_status != 'reviewed'
                            or len(independent_reviewers) < 2):
            raise ValueError('Publication requires real, independently reviewed cases')
    if publication and any(e.synthetic or e.annotation_status != 'reviewed'
                           or len({name.strip().casefold() for name in e.reviewers if name.strip()}) < 2
                           or not (e.source_locator and e.source_locator.strip())
                           for e in corpus):
        raise ValueError('Publication requires real, independently reviewed evidence')
    return {'cases': len(cases), 'papers': len(paper_splits), 'evidence': len(corpus),
            'paired_groups': len(pair_records), 'publication_schema_validated': bool(publication),
            'validation_scope': 'Metadata/format assertions only; not independent certification of source rights or review truth.'}


class ToolError(ValueError):
    pass


class Environment:
    def __init__(self, corpus: list[Evidence], case: Case, seed=20261102, budget=None):
        self.budget = budget or Budget()
        self.task = PublicTask(task_id=digest(f'{seed}|{case.case_id}')[:24],
                               question=case.question, question_language=case.question_language)
        lookup = {e.evidence_id: e for e in corpus}
        self._aliases = {eid: 'd-' + digest(f'{seed}|{self.task.task_id}|{eid}')[:16]
                         for eid in case.visible_evidence_ids}
        self._documents = {self._aliases[eid]: lookup[eid] for eid in case.visible_evidence_ids}
        self.opened: set[str] = set()
        self.trace: list[ToolEvent] = []
        self.calls = 0
        self.observation_chars = 0

    def public_id(self, evidence_id):
        """Evaluator/oracle helper; never supplied to a regular policy."""
        return self._aliases[evidence_id]

    @staticmethod
    def _metadata(document_id, evidence):
        metadata = {'document_id': document_id, 'paper_id': evidence.paper_id,
                'paper_version': evidence.paper_version, 'original_version': evidence.original_version,
                'title': evidence.title, 'source_language': evidence.source_language,
                'source_url': evidence.source_url, 'license': evidence.license,
                'content_sha256': evidence.content_sha256}
        if evidence.source_locator is not None:
            metadata['source_locator'] = evidence.source_locator
        return metadata

    def call(self, action: Action) -> dict:
        self.calls += 1
        try:
            if self.calls > self.budget.max_calls:
                raise ToolError('Tool-call budget exceeded')
            arguments = action.arguments
            if action.tool == 'search':
                if set(arguments) - {'query', 'limit'}:
                    raise ToolError('Unknown search argument')
                query, limit = arguments.get('query'), arguments.get('limit', 5)
                if not isinstance(query, str) or not query.strip() or type(limit) is not int or not 1 <= limit <= 10:
                    raise ToolError('search needs nonempty query and limit 1..10')
                terms = Counter(re.findall(r'[\w]+', query.casefold()))
                ranked = []
                for identifier, evidence in self._documents.items():
                    tokens = Counter(re.findall(r'[\w]+', (evidence.title + ' ' + evidence.text).casefold()))
                    score = sum(min(count, tokens[term]) for term, count in terms.items())
                    ranked.append((score, identifier, evidence))
                ranked.sort(key=lambda row: (-row[0], row[1]))
                result = {'results': [self._metadata(i, e) for _, i, e in ranked[:limit]]}
            elif action.tool in {'open', 'citations'}:
                if set(arguments) != {'document_id'} or arguments['document_id'] not in self._documents:
                    raise ToolError('Unknown document_id or arguments')
                identifier = arguments['document_id']
                evidence = self._documents[identifier]
                if action.tool == 'open':
                    result = {**self._metadata(identifier, evidence), 'text': evidence.text}
                else:
                    if identifier not in self.opened:
                        raise ToolError('Open the source document before citation traversal')
                    result = {'results': [self._metadata(self._aliases[e], self._documents[self._aliases[e]])
                                          for e in evidence.cites_ids if e in self._aliases]}
            else:
                raise ToolError('Unknown tool')
            size = len(json.dumps(result, ensure_ascii=False, sort_keys=True))
            if self.observation_chars + size > self.budget.max_observation_chars:
                raise ToolError('Observation character budget exceeded; evidence was not truncated')
            self.observation_chars += size
            if action.tool == 'open':
                self.opened.add(action.arguments['document_id'])
            self.trace.append(ToolEvent(action=action, observation=result))
            return result
        except (ToolError, TypeError) as exc:
            message = str(exc) if isinstance(exc, ToolError) else 'Invalid tool argument type'
            self.trace.append(ToolEvent(action=action, error=message))
            raise ToolError(message) from exc
