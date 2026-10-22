"""Sequential model loading, isolated calls, durable raw outputs and re-scoring."""

from __future__ import annotations

import json
import os
import platform
import random
import subprocess
import time
from collections.abc import Callable
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .config import ExperimentConfig, key_env, preflight
from .contracts import Generation, Prediction, Review, TaskInput, digest
from .prompts import SYSTEM, parse_answer, user_prompt
from .providers import TextBackend, build_backend
from .scoring import score_predictions
from .worlds import load_bundle, read_jsonl, write_json, write_jsonl


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _error(exc: Exception, config: ExperimentConfig) -> str:
    value = f"{type(exc).__name__}: {exc}"
    names = {"HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"}
    names.update(
        key_env(s)
        for s in config.models.values()
        if s.provider not in {"transformers", "abstain"}
    )
    for name in names:
        token = os.environ.get(name)
        if token:
            value = value.replace(token, "[REDACTED]")
    return value[:1600]


def _versions() -> dict:
    result = {"python": platform.python_version()}
    for name in (
        "linkpaper-eval",
        "httpx",
        "pydantic",
        "torch",
        "transformers",
        "accelerate",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
        "numpy",
        "triton",
    ):
        try:
            result[name] = version(name)
        except PackageNotFoundError:
            pass
    return result


def _predict(
    backend: TextBackend, task: TaskInput, repetition: int, config: ExperimentConfig
) -> Prediction:
    prompt = SYSTEM + "\n" + user_prompt(task)
    started = time.perf_counter()
    parsed, error = None, None
    generation = Generation()
    try:
        if len(prompt) > config.max_prompt_chars:
            raise ValueError(
                "Shared prompt character budget exceeded; evidence was not truncated"
            )
        # Serialize/copy the PUBLIC contract; no GoldRecord is ever passed in.
        public_task = TaskInput.model_validate_json(task.model_dump_json())
        # Per-case RNG makes resumed sampled local runs independent of skipped calls.
        set_seed = getattr(backend, "set_seed", None)
        if set_seed is not None:
            set_seed(int(digest(f"{config.seed}|{task.task_id}|{repetition}")[:8], 16))
        generation = backend.generate(public_task)
        error = generation.error
        if error is None:
            parsed = parse_answer(generation.text)
    except Exception as exc:  # noqa: BLE001 - every planned case must remain in the denominator
        error = _error(exc, config)
        # Preserve a provider's raw output and usage after parsing failures.
    return Prediction(
        task_id=task.task_id,
        repetition=repetition,
        prompt_sha256=digest(prompt),
        generation=generation,
        parsed=parsed,
        error=error,
        latency_ms=(time.perf_counter() - started) * 1000,
    )


def render_report(scores: dict) -> str:
    a = scores["aggregate"]
    lines = [
        "# LINK-DELTA text-only experiment",
        "",
        "Structured diagnostics are not semantic task correctness. Paper Joint4 remains",
        "unavailable until every non-error response has a response-bound semantic review.",
        "",
        f"Cases: {scores['case_count']} · groups: {scores['group_count']} · families: {scores['family_count']}",
        "",
        f"Verdict macro-F1: {a['verdict_macro_f1']:.4f} (labels: {scores['verdict_macro_f1_labels']})",
        "",
        "| World | Diagnostic pass | Verdict accuracy | Error rate |",
        "|---|---:|---:|---:|",
    ]
    for world, values in scores["by_world"].items():
        lines.append(
            f"| {world} | {values['diagnostic_pass']:.4f} | {values['verdict_correct']:.4f} | {values['error']:.4f} |"
        )
    lines.extend(
        [
            "",
            f"Diagnostic Joint4: {a['diagnostic_joint4']:.4f}",
            f"Family cluster 95% CI: {a['diagnostic_joint4_cluster_ci95']}",
            f"Diagnostic PairPass: {a['diagnostic_pairpass']}",
            f"Semantic review coverage: {a['review_coverage']:.1%}",
            f"Paper Joint4: {a['paper_joint4'] if a['paper_joint4'] is not None else 'pending semantic review'}",
            "",
        ]
    )
    return "\n".join(lines)


def run_experiment(
    bundle: Path,
    config: ExperimentConfig,
    models: list[str],
    output: Path,
    split: str | None = None,
    backend_factory: Callable = build_backend,
    resume: bool = False,
) -> dict:
    preflight(config, models)
    tasks, records, bundle_manifest = load_bundle(bundle)
    records = [r for r in records if split is None or r.split == split]
    selected = {r.task_id for r in records}
    tasks = [t for t in tasks if t.task_id in selected]
    if not tasks:
        raise ValueError("No complete question groups in the requested split")
    fingerprint = digest(
        json.dumps(
            {
                "bundle": digest(
                    (bundle / "manifest.json").read_text(encoding="utf-8")
                ),
                "models": {
                    name: config.models[name].model_dump(mode="json") for name in models
                },
                "seed": config.seed,
                "repeats": config.repeats,
                "split": split,
                "max_prompt_chars": config.max_prompt_chars,
                "bootstrap_samples": config.bootstrap_samples,
                "prompt": SYSTEM,
            },
            sort_keys=True,
        )
    )
    if output.exists() and not resume:
        raise FileExistsError(f"Run already exists: {output}; choose a new --out")
    if resume and not output.exists():
        raise ValueError("--resume requires an existing run directory")
    current_versions = _versions()
    current_source = {
        p.name: digest(p.read_text(encoding="utf-8"))
        for p in sorted(Path(__file__).parent.glob("*.py"))
    }
    resume_states = {}
    if resume:
        previous = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        if previous.get("experiment_sha256") != fingerprint:
            raise ValueError(
                "Resume configuration/bundle/prompt does not match the original run"
            )
        # Validate EVERY saved model before changing artifacts or making calls.
        for name in models:
            folder = output / name
            if not (folder / "manifest.json").exists():
                continue
            previous_model = json.loads(
                (folder / "manifest.json").read_text(encoding="utf-8")
            )
            saved = (folder / "predictions.jsonl").read_text(encoding="utf-8")
            if previous_model.get("status") in {
                "completed",
                "failed",
                "interrupted",
            } and digest(saved) != previous_model.get("predictions_sha256"):
                raise ValueError("Resume predictions checksum mismatch")
            predictions = [
                Prediction.model_validate_json(line)
                for line in saved.splitlines()
                if line.strip()
            ]
            score_predictions(
                tasks, records, predictions, config.repeats, bootstrap_samples=0
            )
            if previous_model.get("source_sha256") != current_source:
                raise ValueError("Resume requires the exact original research code")
            if previous_model.get("versions") != current_versions:
                raise ValueError(
                    "Resume dependency versions do not match the original run"
                )
            resume_states[name] = previous_model, predictions
    output.mkdir(parents=True, exist_ok=resume)
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        git_sha = None
    summary = {
        "schema_version": 1,
        "modality": "text",
        "started_at": _now(),
        "experiment_sha256": fingerprint,
        "bundle_manifest_sha256": digest(
            (bundle / "manifest.json").read_text(encoding="utf-8")
        ),
        "fixture_or_draft": any(r.annotation_status != "reviewed" for r in records),
        "models": {},
    }
    write_json(output / "summary.json", summary)
    for name in models:
        spec = config.models[name]
        folder = output / name
        folder.mkdir(exist_ok=resume)
        predictions: list[Prediction] = []
        manifest = {
            "schema_version": 1,
            "status": "running",
            "started_at": _now(),
            "model_alias": name,
            "model_spec": spec.model_dump(mode="json"),
            "seed": config.seed,
            "repeats": config.repeats,
            "max_prompt_chars": config.max_prompt_chars,
            "bootstrap_samples": config.bootstrap_samples,
            "split": split,
            "task_ids": [t.task_id for t in tasks],
            "bundle_manifest_sha256": summary["bundle_manifest_sha256"],
            "bundle_artifacts": bundle_manifest["artifacts"],
            "prompt_sha256": digest(SYSTEM),
            "git_sha": git_sha,
            "versions": current_versions,
            "source_sha256": current_source,
        }
        if name in resume_states:
            previous_model, predictions = resume_states[name]
            manifest["previous_attempt"] = previous_model
            if "backend" in previous_model:
                manifest["backend"] = previous_model["backend"]
        completed = {(p.task_id, p.repetition) for p in predictions}
        write_json(folder / "manifest.json", manifest)
        backend = None
        (folder / "predictions.jsonl").touch()
        try:
            if len(completed) < len(tasks) * config.repeats:
                backend = backend_factory(
                    spec
                )  # Local weights load ONCE; completed runs need no reload.
                manifest["backend"] = backend.metadata
                write_json(folder / "manifest.json", manifest)
            with (folder / "predictions.jsonl").open(
                "a" if resume else "w", encoding="utf-8"
            ) as handle:
                for repetition in range(config.repeats):
                    ordered = list(tasks)
                    random.Random(config.seed + repetition).shuffle(ordered)
                    for task in ordered:
                        if (task.task_id, repetition) in completed:
                            continue
                        prediction = _predict(backend, task, repetition, config)
                        handle.write(prediction.model_dump_json() + "\n")
                        handle.flush()
                        predictions.append(prediction)
            manifest["status"] = "completed"
        except KeyboardInterrupt:
            manifest["status"] = "interrupted"
            raise
        except Exception as exc:  # noqa: BLE001 - persist model setup/run failures for all planned cases
            manifest["status"] = "failed"
            manifest["startup_or_run_error"] = _error(exc, config)
            if not (folder / "predictions.jsonl").exists():
                write_jsonl(folder / "predictions.jsonl", [])
        finally:
            if backend is not None:
                try:
                    backend.close()
                except Exception as exc:  # noqa: BLE001 - preserve results even when cleanup fails
                    manifest["cleanup_error"] = _error(exc, config)
            manifest["finished_at"] = _now()
            manifest["predictions_sha256"] = digest(
                (folder / "predictions.jsonl").read_text(encoding="utf-8")
            )
            write_json(folder / "manifest.json", manifest)
        scores = score_predictions(
            tasks,
            records,
            predictions,
            config.repeats,
            bootstrap_samples=config.bootstrap_samples,
            seed=config.seed,
        )
        usage = {
            key: sum(getattr(p.generation, key) or 0 for p in predictions)
            for key in ("input_tokens", "output_tokens")
        }
        usage["missing_token_usage_cases"] = len(tasks) * config.repeats - sum(
            p.generation.input_tokens is not None
            and p.generation.output_tokens is not None
            for p in predictions
        )
        usage["estimated_uncached_cost_usd"] = (
            (
                usage["input_tokens"] * spec.input_usd_per_million
                + usage["output_tokens"] * spec.output_usd_per_million
            )
            / 1_000_000
            if spec.input_usd_per_million is not None
            and spec.output_usd_per_million is not None
            and not usage["missing_token_usage_cases"]
            else None
        )
        scores["usage"] = usage
        write_json(folder / "scores.json", scores)
        (folder / "report.md").write_text(render_report(scores), encoding="utf-8")
        summary["models"][name] = {
            "status": manifest["status"],
            "aggregate": scores["aggregate"],
            "usage": usage,
        }
        write_json(output / "summary.json", summary)
    summary["finished_at"] = _now()
    write_json(output / "summary.json", summary)
    return summary


def load_saved(bundle: Path, run: Path):
    tasks, records, _ = load_bundle(bundle)
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    if (
        digest((bundle / "manifest.json").read_text(encoding="utf-8"))
        != manifest["bundle_manifest_sha256"]
    ):
        raise ValueError("Run was produced using a different bundle")
    text = (run / "predictions.jsonl").read_text(encoding="utf-8")
    if digest(text) != manifest["predictions_sha256"]:
        raise ValueError("Saved predictions checksum mismatch")
    ids = set(manifest["task_ids"])
    tasks = [t for t in tasks if t.task_id in ids]
    records = [r for r in records if r.task_id in ids]
    predictions = [
        Prediction.model_validate_json(line)
        for line in text.splitlines()
        if line.strip()
    ]
    return tasks, records, predictions, manifest


def rescore(bundle: Path, run: Path, reviews_path: Path | None = None) -> dict:
    tasks, records, predictions, manifest = load_saved(bundle, run)
    reviews = read_jsonl(reviews_path, Review) if reviews_path else None
    result = score_predictions(
        tasks,
        records,
        predictions,
        manifest["repeats"],
        reviews,
        manifest["bootstrap_samples"],
        manifest["seed"],
    )
    result["reviews_sha256"] = (
        digest(reviews_path.read_text(encoding="utf-8")) if reviews_path else None
    )
    return result


def export_review(bundle: Path, run: Path, output: Path) -> int:
    tasks, records, predictions, _ = load_saved(bundle, run)
    if output.exists():
        raise FileExistsError(f"Review directory exists: {output}")
    output.mkdir(parents=True)
    task_map, gold_map = {t.task_id: t for t in tasks}, {r.task_id: r for r in records}
    contexts, templates = [], []
    for prediction in predictions:
        if prediction.error or prediction.generation.error:
            continue  # Already scored as failures; no semantic rating needed.
        identity = {
            "task_id": prediction.task_id,
            "repetition": prediction.repetition,
            "response_sha256": digest(prediction.generation.text),
        }
        templates.append(
            {**identity, "semantic_pass": None, "annotator": "", "notes": ""}
        )
        contexts.append(
            {
                **identity,
                "task": task_map[prediction.task_id].model_dump(mode="json"),
                "rubric": gold_map[prediction.task_id].gold.model_dump(mode="json"),
                "response": prediction.generation.text,
            }
        )
    write_jsonl(output / "reviews.jsonl", templates)
    write_jsonl(output / "review_context.jsonl", contexts)
    return len(templates)
