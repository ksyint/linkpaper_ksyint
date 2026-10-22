"""Failure-inclusive diagnostics and separately reviewed scientific task scores."""

from __future__ import annotations

import random
from collections import defaultdict
from statistics import mean

from .contracts import WORLDS, GoldRecord, Prediction, Review, TaskInput, digest


def _norm(value: str) -> str:
    return " ".join(value.casefold().split())


def case_scores(
    task: TaskInput, record: GoldRecord, prediction: Prediction | None
) -> dict:
    if (
        prediction is None
        or prediction.error
        or prediction.generation.error
        or prediction.parsed is None
    ):
        return {
            "verdict_correct": 0.0,
            "condition_recall": 0.0,
            "citation_validity": 0.0,
            "sufficient_set_covered": 0.0,
            "diagnostic_pass": 0.0,
            "error": 1.0,
        }
    answer, gold = prediction.parsed, record.gold
    claims = answer.claims
    citations = {c for claim in claims for c in claim.citations}
    visible = {c.citation_id for c in task.contexts}
    validity = float(citations <= visible and all(claim.citations for claim in claims))
    sufficient = float(
        not gold.sufficient_sets
        or any(set(s) <= citations for s in gold.sufficient_sets)
    )
    condition_recall = (
        mean(
            float(_norm(answer.conditions.get(key, "")) == _norm(expected))
            for key, expected in gold.expected_conditions.items()
        )
        if gold.expected_conditions
        else 1.0
    )
    verdict = float(answer.verdict == gold.verdict)
    passed = float(verdict == validity == sufficient == condition_recall == 1.0)
    return {
        "verdict_correct": verdict,
        "condition_recall": condition_recall,
        "citation_validity": validity,
        "sufficient_set_covered": sufficient,
        "diagnostic_pass": passed,
        "error": 0.0,
    }


def _bootstrap(
    group_values: dict[str, float], families: dict[str, str], samples: int, seed: int
):
    if not samples:
        return None
    clusters = defaultdict(list)
    for group, value in group_values.items():
        clusters[families[group]].append(value)
    names = sorted(clusters)
    if len(names) < 2:
        return None  # One lineage cannot support a meaningful cluster interval.
    rng = random.Random(seed)
    values = sorted(
        mean(v for name in rng.choices(names, k=len(names)) for v in clusters[name])
        for _ in range(samples)
    )
    return [values[int((len(values) - 1) * q)] for q in (0.025, 0.975)]


def score_predictions(
    tasks: list[TaskInput],
    records: list[GoldRecord],
    predictions: list[Prediction],
    repeats: int,
    reviews: list[Review] | None = None,
    bootstrap_samples: int = 1000,
    seed: int = 20261022,
) -> dict:
    if repeats < 1 or not records:
        raise ValueError(
            "Scoring requires nonempty complete groups and positive repeats"
        )
    task_map = {t.task_id: t for t in tasks}
    if len(task_map) != len(tasks) or len({r.task_id for r in records}) != len(records):
        raise ValueError("Scoring requires unique task and gold IDs")
    if task_map.keys() != {r.task_id for r in records}:
        raise ValueError("Scoring task/gold IDs do not match")
    if len({(r.group_id, r.world) for r in records}) != len(records):
        raise ValueError("Duplicate group/world gold records")
    prediction_map = {}
    for p in predictions:
        key = (p.task_id, p.repetition)
        if (
            p.task_id not in task_map
            or p.repetition >= repeats
            or key in prediction_map
        ):
            raise ValueError("Unknown/duplicate prediction or unexpected repetition")
        prediction_map[key] = p
    review_map = {}
    for review in reviews or []:
        key = (review.task_id, review.repetition)
        prediction = prediction_map.get(key)
        if prediction is None or key in review_map:
            raise ValueError("Unknown/duplicate review")
        if digest(prediction.generation.text) != review.response_sha256:
            raise ValueError("Review response checksum mismatch")
        review_map[key] = review
    rows = []
    verdict_pairs = []
    by_group = defaultdict(dict)
    for record in records:
        for repetition in range(repeats):
            key = (record.task_id, repetition)
            prediction = prediction_map.get(key)
            scores = case_scores(task_map[record.task_id], record, prediction)
            verdict_pairs.append(
                (
                    record.gold.verdict,
                    prediction.parsed.verdict if not scores["error"] else "__error__",
                )
            )
            review = review_map.get(key)
            # Never present structured agreement as semantic correctness.
            paper_pass = (
                0.0
                if scores["error"]
                else scores["diagnostic_pass"] * float(review.semantic_pass)
                if review
                else None
            )
            row = {
                "task_id": record.task_id,
                "group_id": record.group_id,
                "family_id": record.family_id,
                "world": record.world,
                "repetition": repetition,
                **scores,
                "paper_pass": paper_pass,
                "reviewed": review is not None,
            }
            rows.append(row)
            by_group[(record.group_id, repetition)][record.world] = row
    if any(set(worlds) != set(WORLDS) for worlds in by_group.values()):
        raise ValueError("Every scored group must contain all four worlds")
    aggregate = {
        key: mean(r[key] for r in rows)
        for key in (
            "verdict_correct",
            "condition_recall",
            "citation_validity",
            "sufficient_set_covered",
            "diagnostic_pass",
            "error",
        )
    }
    labels = sorted({truth for truth, _ in verdict_pairs})
    f1s = []
    for label in labels:
        tp = sum(truth == predicted == label for truth, predicted in verdict_pairs)
        fp = sum(
            truth != label and predicted == label for truth, predicted in verdict_pairs
        )
        fn = sum(
            truth == label and predicted != label for truth, predicted in verdict_pairs
        )
        f1s.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    aggregate["verdict_macro_f1"] = mean(f1s)
    joint_values = defaultdict(list)
    pairs = {w: [] for w in WORLDS[1:]}
    paper_joint = []
    for (group, _), worlds in by_group.items():
        joint = float(all(worlds[w]["diagnostic_pass"] for w in WORLDS))
        joint_values[group].append(joint)
        for world, values in pairs.items():
            values.append(
                worlds["FULL"]["diagnostic_pass"] * worlds[world]["diagnostic_pass"]
            )
        paper_joint.append(
            float(all(worlds[w]["paper_pass"] for w in WORLDS))
            if all(worlds[w]["paper_pass"] is not None for w in WORLDS)
            else None
        )
    group_joint = {group: mean(values) for group, values in joint_values.items()}
    families = {r.group_id: r.family_id for r in records}
    aggregate.update(
        {
            "diagnostic_joint4": mean(group_joint.values()),
            "diagnostic_joint4_cluster_ci95": _bootstrap(
                group_joint, families, bootstrap_samples, seed
            ),
            "diagnostic_pairpass": {w: mean(values) for w, values in pairs.items()},
            "paper_joint4": mean(paper_joint)
            if all(v is not None for v in paper_joint)
            else None,
            "review_coverage": len(review_map) / len(rows),
        }
    )
    return {
        "schema_version": 1,
        "case_count": len(rows),
        "group_count": len(group_joint),
        "family_count": len(set(families.values())),
        "repeats": repeats,
        "missing_predictions": len(rows) - len(prediction_map),
        "verdict_macro_f1_labels": labels,
        "verdict_confusion": {
            truth: {
                predicted: sum(t == truth and p == predicted for t, p in verdict_pairs)
                for predicted in (*labels, "mixed", "__error__")
            }
            for truth in labels
        },
        "score_scope": "Structured diagnostics; paper scores require response-bound semantic review.",
        "aggregate": aggregate,
        "by_world": {
            w: {
                key: mean(r[key] for r in rows if r["world"] == w)
                for key in ("diagnostic_pass", "verdict_correct", "error")
            }
            for w in WORLDS
        },
        "cases": rows,
    }
