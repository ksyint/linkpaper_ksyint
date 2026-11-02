"""Original frozen-corpus agent contracts; gold records never enter PublicTask."""
from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Verdict = Literal['supported', 'refuted', 'mixed', 'insufficient']
Status = Literal['fixture', 'draft', 'reviewed']


def digest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, hide_input_in_errors=True)


class Evidence(StrictModel):
    evidence_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    paper_version: str = Field(min_length=1)
    original_version: str = Field(min_length=1)
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_language: Literal['ko', 'en', 'mixed']
    source_url: str = Field(pattern=r'^https?://\S+$')
    license: str = Field(min_length=1)
    license_url: str = Field(pattern=r'^https?://\S+$')
    content_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    # One record is an atomic query-relevant result span, not a whole paper.
    source_locator: str | None = None
    cites_ids: list[str] = Field(default_factory=list)
    # Curator-only identity of the actual experiment/study, NOT independence.
    study_unit_id: str | None = None
    annotation_status: Status = 'draft'
    synthetic: bool = False
    reviewers: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_source(self):
        if not self.text.strip() or digest(self.text) != self.content_sha256:
            raise ValueError('Evidence text/checksum mismatch')
        if any(not getattr(self, field).strip() for field in
               ('evidence_id', 'paper_id', 'paper_version', 'original_version', 'title', 'license')):
            raise ValueError('Blank provenance field')
        if len(self.cites_ids) != len(set(self.cites_ids)):
            raise ValueError('Duplicate citation edge')
        if self.study_unit_id is not None and not self.study_unit_id.strip():
            raise ValueError('Unknown study provenance must be null, not blank')
        if self.annotation_status == 'reviewed' and (
            self.synthetic or len({name.strip().casefold() for name in self.reviewers if name.strip()}) < 2
        ):
            raise ValueError('Reviewed scientific evidence needs two reviewers and real sources')
        if self.annotation_status == 'reviewed' and not self.synthetic and not (
            self.source_locator and self.source_locator.strip()
        ):
            raise ValueError('Reviewed scientific evidence needs a nonblank source locator')
        return self


class Gold(StrictModel):
    verdict: Verdict
    sufficient_sets: list[list[str]] = Field(default_factory=list)
    expected_conditions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode='after')
    def validate_sets(self):
        if self.verdict != 'insufficient' and not self.sufficient_sets:
            raise ValueError('Decisive/mixed labels require sufficient evidence')
        if self.verdict == 'insufficient' and self.sufficient_sets:
            raise ValueError('Insufficient labels cannot declare sufficient evidence')
        if any(not ids or len(ids) != len(set(ids)) for ids in self.sufficient_sets):
            raise ValueError('Invalid sufficient set')
        return self


class Case(StrictModel):
    case_id: str = Field(min_length=1)
    pair_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    split: Literal['dev', 'test', 'holdout']
    question: str = Field(min_length=5)
    question_language: Literal['ko', 'en']
    visible_evidence_ids: list[str] = Field(min_length=1)
    gold: Gold
    # Descriptive curator tag; there is deliberately no tag->verdict rule.
    control_tag: str = Field(min_length=1)
    author: str = Field(min_length=1)
    annotation_status: Status = 'draft'
    synthetic: bool = False
    reviewers: list[str] = Field(default_factory=list)


class PublicTask(StrictModel):
    task_id: str
    question: str
    question_language: Literal['ko', 'en']


class Action(StrictModel):
    tool: str
    arguments: dict = Field(default_factory=dict)


class Claim(StrictModel):
    text: str = Field(min_length=2)
    citations: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def substantive(self):
        if sum(character.isalnum() for character in self.text) < 2:
            raise ValueError('Empty/substanceless claim')
        return self


class Answer(StrictModel):
    verdict: Verdict
    answer: str = Field(min_length=2)
    claims: list[Claim] = Field(min_length=1)
    conditions: dict[str, str] = Field(default_factory=dict)
    # Agent-inferred arbitrary group labels; unknown is null. No gold unit IDs.
    study_groups: dict[str, str | None] = Field(default_factory=dict)

    @model_validator(mode='after')
    def nonempty_answer(self):
        if sum(character.isalnum() for character in self.answer) < 2:
            raise ValueError('Empty/substanceless answer')
        return self


class ToolEvent(StrictModel):
    action: Action
    observation: dict = Field(default_factory=dict)
    error: str | None = None


def answer_hash(answer: Answer) -> str:
    return digest(json.dumps(answer.model_dump(mode='json'), ensure_ascii=False,
                             sort_keys=True, separators=(',', ':')))


class Prediction(StrictModel):
    task_id: str
    answer: Answer | None = None
    trace: list[ToolEvent] = Field(default_factory=list)
    opened_ids: list[str] = Field(default_factory=list)
    error: str | None = None
    oracle: bool = False
    response_sha256: str | None = None

    @model_validator(mode='after')
    def check_response(self):
        if self.answer is not None and self.response_sha256 != answer_hash(self.answer):
            raise ValueError('Prediction answer checksum mismatch')
        if self.answer is None and self.response_sha256 is not None:
            raise ValueError('Missing answer cannot have a response checksum')
        return self


class Review(StrictModel):
    task_id: str
    response_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    semantic_pass: bool = Field(strict=True)
    annotator: str = Field(min_length=1)
    notes: str = ''


class Budget(StrictModel):
    max_calls: int = Field(default=12, ge=1, le=100)
    max_observation_chars: int = Field(default=30000, ge=1, le=1_000_000)
