"""Compile curated evidence interventions to hashed public/private artifacts."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from .contracts import (
    WORLDS,
    Context,
    Evidence,
    GoldRecord,
    StudyGroup,
    TaskInput,
    digest,
)

T = TypeVar("T", bound=BaseModel)


def read_jsonl(path: Path, model: type[T]) -> list[T]:
    result = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                result.append(model.model_validate_json(line))
            except ValueError as exc:
                raise ValueError(f"{path.name}:{number}: {exc}") from exc
    if not result:
        raise ValueError(f"Empty JSONL: {path}")
    return result


def write_json(path: Path, data: dict) -> None:
    temporary = path.with_name("." + path.name + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def write_jsonl(path: Path, rows: list) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            value = row.model_dump(mode="json") if isinstance(row, BaseModel) else row
            handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def unique(rows: list[T], key: str) -> dict[str, T]:
    index = {getattr(row, key): row for row in rows}
    if len(index) != len(rows):
        raise ValueError(f"Duplicate {key}")
    return index


def validate_study(corpus: list[Evidence], groups: list[StudyGroup]) -> None:
    lookup = unique(corpus, "evidence_id")
    unique(groups, "group_id")
    families: dict[str, str] = {}
    decisive_papers: dict[str, str] = {}
    paper_families: dict[str, str] = {}
    questions: dict[str, str] = {}
    for group in groups:
        for mapping, key, label in (
            (families, group.family_id, "family"),
            (questions, " ".join(group.question.lower().split()), "question"),
        ):
            if key in mapping and mapping[key] != group.split:
                raise ValueError(f"Cross-split {label} leakage: {key}")
            mapping[key] = group.split
        source_ids = set(group.full_evidence_ids + group.scope_add_ids)
        if not source_ids <= lookup.keys():
            raise ValueError(
                f"{group.group_id}: Unknown evidence IDs: {source_ids - lookup.keys()}"
            )
        defining_ids = set(group.cut_remove_ids)
        defining_ids.update(
            eid for support in group.gold["FULL"].sufficient_sets for eid in support
        )
        if not defining_ids <= lookup.keys():
            raise ValueError(f"{group.group_id}: Unknown decisive evidence")
        for eid in defining_ids:
            paper = lookup[eid].paper_id
            if paper in decisive_papers and decisive_papers[paper] != group.split:
                raise ValueError(f"Cross-split decisive paper leakage: {paper}")
            decisive_papers[paper] = group.split
            if paper in paper_families and paper_families[paper] != group.family_id:
                raise ValueError(
                    f"Shared decisive papers must use the same family_id: {paper}"
                )
            paper_families[paper] = group.family_id
        mismatch = any(
            key in lookup[eid].condition_annotations
            and lookup[eid].condition_annotations[key].casefold() != expected.casefold()
            for eid in group.scope_add_ids
            for key, expected in group.requested_conditions.items()
        )
        if not mismatch:
            raise ValueError(
                f"{group.group_id}: SCOPE needs an annotated condition mismatch"
            )
        for world, ids in world_ids(group).items():
            visible = set(ids)
            gold = group.gold[world]
            for support in gold.sufficient_sets:
                if not set(support) <= visible:
                    raise ValueError(
                        f"{group.group_id}/{world}: Gold cites unavailable evidence"
                    )
            if world in {"CUT", "SCOPE"} and any(
                set(s) <= visible for s in group.gold["FULL"].sufficient_sets
            ):
                raise ValueError(
                    f"{group.group_id}/{world}: A FULL alternative survived"
                )


def world_ids(group: StudyGroup) -> dict[str, list[str]]:
    cut = [eid for eid in group.full_evidence_ids if eid not in group.cut_remove_ids]
    return {
        "FULL": group.full_evidence_ids,
        "CUT": cut,
        "PLACEBO": [
            eid
            for eid in group.full_evidence_ids
            if eid not in group.placebo_remove_ids
        ],
        "SCOPE": cut + group.scope_add_ids,
    }


def compile_study(
    corpus_path: Path, groups_path: Path, output: Path, seed: int = 20261022
) -> dict:
    corpus = read_jsonl(corpus_path, Evidence)
    corpus = [
        item.model_copy(update={"content_sha256": digest(item.text)}) for item in corpus
    ]
    groups = read_jsonl(groups_path, StudyGroup)
    validate_study(corpus, groups)
    if output.exists():
        raise FileExistsError(
            f"Bundle already exists: {output}; choose a new directory"
        )
    lookup = {item.evidence_id: item for item in corpus}
    tasks, records = [], []
    for group in groups:
        for world in WORLDS:
            task_id = digest(f"{seed}|{group.group_id}|{world}")[:24]
            ids = list(world_ids(group)[world])
            random.Random(f"{seed}|{task_id}").shuffle(ids)
            # Per-task aliases prevent numbering gaps from exposing removals.
            aliases = {
                eid: "e-" + digest(f"{seed}|{task_id}|{eid}")[:16] for eid in ids
            }
            tasks.append(
                TaskInput(
                    task_id=task_id,
                    question=group.question,
                    requested_conditions=group.requested_conditions,
                    contexts=[
                        Context(
                            citation_id=aliases[eid],
                            paper_id=lookup[eid].paper_id,
                            paper_version=lookup[eid].paper_version,
                            source_url=lookup[eid].source_url,
                            text=lookup[eid].text,
                        )
                        for eid in ids
                    ],
                )
            )
            gold = group.gold[world].model_copy(
                update={
                    "sufficient_sets": [
                        [aliases[eid] for eid in support]
                        for support in group.gold[world].sufficient_sets
                    ],
                }
            )
            records.append(
                GoldRecord(
                    task_id=task_id,
                    group_id=group.group_id,
                    family_id=group.family_id,
                    split=group.split,
                    world=world,
                    gold=gold,
                    annotation_status=group.annotation_status,
                    annotation_version=group.annotation_version,
                    evidence_map={aliases[eid]: eid for eid in ids},
                )
            )
    random.Random(seed).shuffle(tasks)
    output.mkdir(parents=True)
    write_jsonl(output / "tasks.jsonl", tasks)
    write_jsonl(output / "gold.jsonl", records)
    # Keep exact source records for independent auditing, separate from task inputs.
    write_jsonl(output / "source_corpus.jsonl", corpus)
    write_jsonl(output / "source_groups.jsonl", groups)
    names = ("tasks.jsonl", "gold.jsonl", "source_corpus.jsonl", "source_groups.jsonl")
    world_by_id = {record.task_id: record.world for record in records}
    manifest = {
        "schema_version": 1,
        "modality": "text",
        "seed": seed,
        "group_count": len(groups),
        "task_count": len(tasks),
        "input_corpus_sha256": digest(corpus_path.read_text(encoding="utf-8")),
        "input_groups_sha256": digest(groups_path.read_text(encoding="utf-8")),
        "annotation_status_counts": {
            s: sum(g.annotation_status == s for g in groups)
            for s in ("fixture", "draft", "reviewed")
        },
        "artifacts": {
            name: digest((output / name).read_text(encoding="utf-8")) for name in names
        },
        "audit": {
            world: {
                "contexts": [
                    len(t.contexts) for t in tasks if world_by_id[t.task_id] == world
                ],
                "text_chars": [
                    sum(len(c.text) for c in t.contexts)
                    for t in tasks
                    if world_by_id[t.task_id] == world
                ],
            }
            for world in WORLDS
        },
        "limitations": "Structural validation cannot certify absence of unannotated alternative evidence.",
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def load_bundle(folder: Path) -> tuple[list[TaskInput], list[GoldRecord], dict]:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("modality") != "text":
        raise ValueError("Unsupported bundle schema or modality")
    expected = {
        "tasks.jsonl",
        "gold.jsonl",
        "source_corpus.jsonl",
        "source_groups.jsonl",
    }
    if set(manifest["artifacts"]) != expected:
        raise ValueError("Incomplete bundle artifact manifest")
    for name, checksum in manifest["artifacts"].items():
        if digest((folder / name).read_text(encoding="utf-8")) != checksum:
            raise ValueError(f"Bundle checksum mismatch: {name}")
    tasks = read_jsonl(folder / "tasks.jsonl", TaskInput)
    records = read_jsonl(folder / "gold.jsonl", GoldRecord)
    if unique(tasks, "task_id").keys() != unique(records, "task_id").keys():
        raise ValueError("Task/gold ID mismatch")
    if (
        len(tasks) != manifest["task_count"]
        or len(records) != manifest["group_count"] * 4
    ):
        raise ValueError("Bundle counts do not match manifest")
    pairs = {(r.group_id, r.world) for r in records}
    if len(pairs) != len(records):
        raise ValueError("Duplicate group/world in bundle gold")
    grouped = {r.group_id for r in records}
    if any(
        {r.world for r in records if r.group_id == group} != set(WORLDS)
        for group in grouped
    ):
        raise ValueError("Incomplete four-world group")
    validate_study(
        read_jsonl(folder / "source_corpus.jsonl", Evidence),
        read_jsonl(folder / "source_groups.jsonl", StudyGroup),
    )
    return tasks, records, manifest
