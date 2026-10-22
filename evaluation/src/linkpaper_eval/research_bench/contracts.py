"""Strict, separate system-input and evaluator-only contracts."""

from __future__ import annotations

import hashlib
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

World = Literal["FULL", "CUT", "PLACEBO", "SCOPE"]
WORLDS: tuple[World, ...] = ("FULL", "CUT", "PLACEBO", "SCOPE")
Verdict = Literal["supported", "refuted", "mixed", "insufficient"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Evidence(StrictModel):
    evidence_id: str = Field(min_length=1)
    paper_id: str = Field(min_length=1)
    paper_version: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    license: str = Field(min_length=1)
    published_at: str | None = None
    # Human annotations used ONLY by construction/auditing, never the model.
    condition_annotations: dict[str, str] = Field(default_factory=dict)
    content_sha256: str | None = None

    @model_validator(mode="after")
    def check_hash(self) -> Self:
        if not self.text.strip():
            raise ValueError("Evidence text must not be blank")
        if self.content_sha256 is not None and self.content_sha256 != digest(self.text):
            raise ValueError(f"Evidence checksum mismatch: {self.evidence_id}")
        return self


class Gold(StrictModel):
    verdict: Verdict
    # Alternatives: ALL spans within ONE set must be cited, not their union.
    sufficient_sets: list[list[str]] = Field(default_factory=list)
    expected_conditions: dict[str, str] = Field(default_factory=dict)
    rubric: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def check_sets(self) -> Self:
        if self.verdict != "insufficient" and not self.sufficient_sets:
            raise ValueError("Decisive/mixed verdicts need sufficient evidence sets")
        if self.verdict == "insufficient" and self.sufficient_sets:
            raise ValueError("Insufficient verdicts cannot declare sufficient evidence")
        if any(
            not group or len(set(group)) != len(group) for group in self.sufficient_sets
        ):
            raise ValueError("Sufficient sets must be nonempty and contain unique IDs")
        if any(not point.strip() for point in self.rubric):
            raise ValueError("Rubric points must not be blank")
        return self


class StudyGroup(StrictModel):
    group_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    split: Literal["dev", "test", "holdout"]
    question: str = Field(min_length=1)
    requested_conditions: dict[str, str] = Field(min_length=1)
    full_evidence_ids: list[str] = Field(min_length=1)
    cut_remove_ids: list[str] = Field(min_length=1)
    placebo_remove_ids: list[str] = Field(min_length=1)
    scope_add_ids: list[str] = Field(min_length=1)
    gold: dict[World, Gold]
    annotation_status: Literal["fixture", "draft", "reviewed"] = "draft"
    annotation_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_intervention(self) -> Self:
        if set(self.gold) != set(WORLDS):
            raise ValueError("Each group needs all four world gold records")
        for name in (
            "full_evidence_ids",
            "cut_remove_ids",
            "placebo_remove_ids",
            "scope_add_ids",
        ):
            ids = getattr(self, name)
            if len(set(ids)) != len(ids):
                raise ValueError(f"Duplicate IDs in {name}")
        base, cut, placebo, added = map(
            set,
            (
                self.full_evidence_ids,
                self.cut_remove_ids,
                self.placebo_remove_ids,
                self.scope_add_ids,
            ),
        )
        if not cut <= base or not placebo <= base:
            raise ValueError("Removed evidence must belong to FULL")
        if cut & placebo or base & added:
            raise ValueError(
                "CUT/PLACEBO removals must be disjoint; SCOPE additions must be new"
            )
        full = self.gold["FULL"]
        if full.verdict not in {"supported", "refuted"}:
            raise ValueError("v1 builder requires a decisive supported/refuted FULL")
        if self.gold["PLACEBO"].verdict != full.verdict:
            raise ValueError("PLACEBO must preserve the FULL verdict")
        if any(self.gold[w].verdict != "insufficient" for w in ("CUT", "SCOPE")):
            raise ValueError("v1 CUT/SCOPE gold must be insufficient")
        if any(not (set(s) & cut) for s in full.sufficient_sets):
            raise ValueError(
                "CUT must break EVERY annotated alternative sufficient set"
            )
        if not any(not (set(s) & placebo) for s in full.sufficient_sets):
            raise ValueError("PLACEBO must preserve at least one sufficient set")
        return self


class Context(StrictModel):
    citation_id: str
    paper_id: str
    paper_version: str
    source_url: str
    text: str


class TaskInput(StrictModel):
    """The ONLY object accepted by the system-under-test interface."""

    task_id: str
    question: str
    requested_conditions: dict[str, str]
    contexts: list[Context]


class GoldRecord(StrictModel):
    task_id: str
    group_id: str
    family_id: str
    split: Literal["dev", "test", "holdout"]
    world: World
    annotation_status: Literal["fixture", "draft", "reviewed"]
    annotation_version: str
    gold: Gold
    # Private trace from shuffled opaque IDs back to the source archive.
    evidence_map: dict[str, str]


class Claim(StrictModel):
    text: str = Field(min_length=1)
    citations: list[str] = Field(default_factory=list)


class Answer(StrictModel):
    verdict: Verdict
    answer: str = Field(min_length=1)
    conditions: dict[str, str]
    claims: list[Claim]


class Generation(StrictModel):
    text: str = ""
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    finish_reason: str | None = None
    request_id: str | None = None
    resolved_model: str | None = None
    usage: dict = Field(default_factory=dict)
    error: str | None = None


class Prediction(StrictModel):
    task_id: str
    repetition: int = Field(ge=0)
    prompt_sha256: str
    generation: Generation
    parsed: Answer | None = None
    error: str | None = None
    latency_ms: float = Field(ge=0)


class Review(StrictModel):
    task_id: str
    repetition: int = Field(ge=0)
    response_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    semantic_pass: bool = Field(strict=True)
    annotator: str = Field(min_length=1)
    notes: str = ""
