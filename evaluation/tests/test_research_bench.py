"""Scientific evaluation invariants, leakage boundaries and complete run paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from linkpaper_eval.cli import main
from linkpaper_eval.research_bench.config import (
    ExperimentConfig,
    ModelSpec,
    load_config,
)
from linkpaper_eval.research_bench.contracts import (
    Evidence,
    Generation,
    Prediction,
    Review,
    StudyGroup,
    TaskInput,
    digest,
)
from linkpaper_eval.research_bench.prompts import SYSTEM, parse_answer, user_prompt
from linkpaper_eval.research_bench.runner import (
    export_review,
    load_saved,
    rescore,
    run_experiment,
)
from linkpaper_eval.research_bench.scoring import score_predictions
from linkpaper_eval.research_bench.worlds import (
    compile_study,
    load_bundle,
    read_jsonl,
    validate_study,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/research"


@pytest.fixture
def bundle(tmp_path):
    folder = tmp_path / "bundle"
    compile_study(FIXTURE / "corpus.jsonl", FIXTURE / "groups.jsonl", folder)
    return folder


def config(repeats=1):
    return ExperimentConfig(
        models={"a": ModelSpec(provider="abstain")},
        repeats=repeats,
        bootstrap_samples=100,
    )


def scripted_prediction(task, record, repetition=0, text=None):
    gold = record.gold
    payload = {
        "verdict": gold.verdict,
        "answer": "Scripted test output, not a research result.",
        "conditions": gold.expected_conditions,
        "claims": [{"text": "Test claim", "citations": gold.sufficient_sets[0]}]
        if gold.sufficient_sets
        else [],
    }
    text = text or json.dumps(payload)
    return Prediction(
        task_id=task.task_id,
        repetition=repetition,
        prompt_sha256=digest(SYSTEM + "\n" + user_prompt(task)),
        generation=Generation(text=text, input_tokens=10, output_tokens=20),
        parsed=parse_answer(text),
        latency_ms=1,
    )


def test_four_worlds_have_no_hidden_labels_or_annotations_in_model_input(bundle):
    tasks, records, manifest = load_bundle(bundle)
    assert len(tasks) == len(records) == 8
    assert manifest["annotation_status_counts"]["fixture"] == 2
    source_terms = {
        "FULL",
        "CUT",
        "PLACEBO",
        "SCOPE",
        "sufficient_sets",
        "rubric",
        "family_id",
        "gold",
        "condition_annotations",
        "fixture-cedar",
    }
    for task in tasks:
        payload = user_prompt(task)
        assert all(term not in payload for term in source_terms)
        assert task.task_id not in payload
        assert all(c.citation_id.startswith("e-") for c in task.contexts)
    for record in records:
        if record.world in {"CUT", "SCOPE"}:
            assert not any(
                eid.endswith(("-0", "-1")) for eid in record.evidence_map.values()
            )


def test_input_rejects_gold_and_multimodal_fields(bundle):
    task = load_bundle(bundle)[0][0]
    for key, value in (("gold", {}), ("images", []), ("world", "FULL")):
        with pytest.raises(ValueError):
            TaskInput.model_validate({**task.model_dump(), key: value})


def test_cut_must_break_all_alternative_support_sets():
    group = read_jsonl(FIXTURE / "groups.jsonl", StudyGroup)[0].model_dump()
    group["cut_remove_ids"] = group["cut_remove_ids"][:1]
    with pytest.raises(ValueError, match="EVERY"):
        StudyGroup.model_validate(group)


def test_placebo_cannot_destroy_sufficient_evidence():
    group = read_jsonl(FIXTURE / "groups.jsonl", StudyGroup)[0].model_dump()
    group["placebo_remove_ids"] = group["cut_remove_ids"]
    with pytest.raises(ValueError):
        StudyGroup.model_validate(group)


def test_scope_requires_a_real_annotated_condition_difference():
    corpus = read_jsonl(FIXTURE / "corpus.jsonl", Evidence)
    groups = read_jsonl(FIXTURE / "groups.jsonl", StudyGroup)
    corpus = [
        item.model_copy(update={"condition_annotations": {"dataset": "Harbor"}})
        if item.evidence_id == "cedar-4"
        else item
        for item in corpus
    ]
    with pytest.raises(ValueError, match="condition mismatch"):
        validate_study(corpus, groups)


def test_family_and_decisive_papers_cannot_cross_splits():
    corpus = read_jsonl(FIXTURE / "corpus.jsonl", Evidence)
    groups = read_jsonl(FIXTURE / "groups.jsonl", StudyGroup)
    duplicate = groups[0].model_copy(
        update={"group_id": "copy", "split": "test", "question": "Different question"}
    )
    with pytest.raises(ValueError, match="Cross-split"):
        validate_study(corpus, groups + [duplicate])
    duplicate = duplicate.model_copy(update={"family_id": "new-family"})
    with pytest.raises(ValueError, match="decisive paper"):
        validate_study(corpus, groups + [duplicate])


def test_generation_is_reproducible_and_existing_bundle_is_protected(bundle, tmp_path):
    second = tmp_path / "second"
    compile_study(FIXTURE / "corpus.jsonl", FIXTURE / "groups.jsonl", second)
    assert (bundle / "tasks.jsonl").read_bytes() == (
        second / "tasks.jsonl"
    ).read_bytes()
    assert (bundle / "manifest.json").read_bytes() == (
        second / "manifest.json"
    ).read_bytes()
    with pytest.raises(FileExistsError):
        compile_study(FIXTURE / "corpus.jsonl", FIXTURE / "groups.jsonl", bundle)


@pytest.mark.parametrize(
    "name", ["tasks.jsonl", "gold.jsonl", "source_corpus.jsonl", "source_groups.jsonl"]
)
def test_corrupted_bundle_fails_before_models_load(bundle, name):
    path = bundle / name
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        load_bundle(bundle)


def test_always_abstain_cannot_game_joint_score(bundle, tmp_path):
    output = tmp_path / "run"
    summary = run_experiment(bundle, config(), ["a"], output)
    aggregate = summary["models"]["a"]["aggregate"]
    assert aggregate["verdict_correct"] == 0.5
    assert aggregate["diagnostic_joint4"] == 0
    assert aggregate["paper_joint4"] is None
    assert (output / "a/predictions.jsonl").exists()
    assert "pending semantic review" in (output / "a/report.md").read_text()
    assert rescore(bundle, output / "a")["aggregate"] == aggregate


def test_complete_support_set_alternative_is_accepted_and_missing_calls_are_failures(
    bundle,
):
    tasks, records, _ = load_bundle(bundle)
    tmap = {t.task_id: t for t in tasks}
    predictions = [scripted_prediction(tmap[r.task_id], r) for r in records]
    # Use the second alternative, not the first gold support.
    r = next(r for r in records if r.world == "FULL")
    i = next(i for i, p in enumerate(predictions) if p.task_id == r.task_id)
    payload = predictions[i].parsed.model_dump()
    payload["claims"][0]["citations"] = r.gold.sufficient_sets[1]
    predictions[i] = scripted_prediction(tmap[r.task_id], r, text=json.dumps(payload))
    scores = score_predictions(tasks, records, predictions, 1)
    assert scores["aggregate"]["diagnostic_joint4"] == 1
    assert scores["aggregate"]["verdict_macro_f1"] == 1
    assert scores["aggregate"]["paper_joint4"] is None
    missing = score_predictions(tasks, records, predictions[1:], 1)
    assert missing["case_count"] == 8
    assert missing["missing_predictions"] == 1
    assert missing["aggregate"]["error"] == 1 / 8
    assert missing["aggregate"]["diagnostic_joint4"] == 0.5


def test_fabricated_citation_fails_even_with_correct_verdict(bundle):
    tasks, records, _ = load_bundle(bundle)
    tmap = {t.task_id: t for t in tasks}
    predictions = [scripted_prediction(tmap[r.task_id], r) for r in records]
    full = next(p for p in predictions if p.parsed.verdict == "supported")
    bad = full.parsed.model_copy(
        update={"claims": [{"text": "Bad claim", "citations": ["gold-only"]}]}
    )
    # Validate the edited nested model explicitly.
    payload = {**full.parsed.model_dump(), "claims": bad.claims}
    replacement = full.model_copy(update={"parsed": parse_answer(json.dumps(payload))})
    predictions = [replacement if p.task_id == full.task_id else p for p in predictions]
    assert (
        score_predictions(tasks, records, predictions, 1)["aggregate"][
            "diagnostic_joint4"
        ]
        == 0.5
    )


def test_semantic_reviews_are_required_and_bound_to_exact_output(bundle):
    tasks, records, _ = load_bundle(bundle)
    tmap = {t.task_id: t for t in tasks}
    predictions = [scripted_prediction(tmap[r.task_id], r) for r in records]
    reviews = [
        Review(
            task_id=p.task_id,
            repetition=0,
            response_sha256=digest(p.generation.text),
            semantic_pass=True,
            annotator="test-reviewer",
        )
        for p in predictions
    ]
    assert (
        score_predictions(tasks, records, predictions, 1, reviews)["aggregate"][
            "paper_joint4"
        ]
        == 1
    )
    reviews[0] = reviews[0].model_copy(update={"semantic_pass": False})
    assert (
        score_predictions(tasks, records, predictions, 1, reviews)["aggregate"][
            "paper_joint4"
        ]
        == 0.5
    )
    reviews[0] = reviews[0].model_copy(update={"response_sha256": "0" * 64})
    with pytest.raises(ValueError, match="checksum"):
        score_predictions(tasks, records, predictions, 1, reviews)


def test_repeats_do_not_inflate_question_or_family_counts(bundle):
    tasks, records, _ = load_bundle(bundle)
    tmap = {t.task_id: t for t in tasks}
    predictions = [
        scripted_prediction(tmap[r.task_id], r, repeat)
        for repeat in range(3)
        for r in records
    ]
    scores = score_predictions(tasks, records, predictions, 3)
    assert (scores["case_count"], scores["group_count"], scores["family_count"]) == (
        24,
        2,
        2,
    )
    assert scores["aggregate"]["diagnostic_joint4_cluster_ci95"] == [1, 1]
    with pytest.raises(ValueError, match="duplicate"):
        score_predictions(tasks, records, predictions + predictions[:1], 3)


def test_model_load_once_and_no_gold_is_sent_to_backend(bundle, tmp_path):
    calls, loaded, closed = [], [], []

    class Backend:
        def __init__(self):
            self.metadata = {"provider": "scripted-test"}

        def generate(self, task):
            assert type(task) is TaskInput
            calls.append(task.model_dump())
            return Generation(text="INVALID_JSON", input_tokens=9, output_tokens=3)

        def close(self):
            closed.append(True)

    def factory(spec):
        loaded.append(spec)
        return Backend()

    run_experiment(
        bundle, config(repeats=2), ["a"], tmp_path / "run", backend_factory=factory
    )
    assert len(loaded) == len(closed) == 1
    assert len(calls) == 16
    assert all(
        set(call) == {"task_id", "question", "requested_conditions", "contexts"}
        for call in calls
    )
    result = json.loads((tmp_path / "run/a/scores.json").read_text())
    assert result["aggregate"]["error"] == 1
    assert result["usage"]["input_tokens"] == 16 * 9
    raw = read_jsonl(tmp_path / "run/a/predictions.jsonl", Prediction)
    assert all(p.generation.text == "INVALID_JSON" for p in raw)


def test_model_initialization_failure_is_recorded_and_counted(bundle, tmp_path):
    def fail(spec):
        raise RuntimeError("Model unavailable")

    summary = run_experiment(
        bundle, config(), ["a"], tmp_path / "run", backend_factory=fail
    )
    assert summary["models"]["a"]["status"] == "failed"
    scores = rescore(bundle, tmp_path / "run/a")
    assert scores["case_count"] == scores["missing_predictions"] == 8
    assert scores["aggregate"]["error"] == 1


def test_api_preflight_happens_before_any_model_or_output_creation(
    bundle, tmp_path, monkeypatch
):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = ExperimentConfig(
        models={"api": ModelSpec(provider="openai", model="chosen-model")}
    )
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        run_experiment(bundle, cfg, ["api"], tmp_path / "run")
    assert not (tmp_path / "run").exists()


def test_prompt_budget_does_not_silently_truncate_evidence(bundle, tmp_path):
    cfg = config().model_copy(update={"max_prompt_chars": 10})
    result = run_experiment(bundle, cfg, ["a"], tmp_path / "run")
    assert result["models"]["a"]["aggregate"]["error"] == 1


def test_export_review_and_cli_rescore_preserve_original_predictions(bundle, tmp_path):
    run_experiment(bundle, config(), ["a"], tmp_path / "run")
    before = (tmp_path / "run/a/predictions.jsonl").read_bytes()
    review_dir = tmp_path / "review"
    assert export_review(bundle, tmp_path / "run/a", review_dir) == 8
    rows = [
        json.loads(line)
        for line in (review_dir / "reviews.jsonl").read_text().splitlines()
    ]
    for row in rows:
        row.update(semantic_pass=False, annotator="human-test")
    (review_dir / "reviews.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows)
    )
    assert (
        main(
            [
                "research",
                "score",
                "--bundle",
                str(bundle),
                "--run",
                str(tmp_path / "run/a"),
                "--reviews",
                str(review_dir / "reviews.jsonl"),
                "--out",
                str(tmp_path / "scored"),
            ]
        )
        == 0
    )
    assert (tmp_path / "run/a/predictions.jsonl").read_bytes() == before
    assert (
        json.loads((tmp_path / "scored/scores.json").read_text())["aggregate"][
            "paper_joint4"
        ]
        == 0
    )


def test_saved_predictions_are_checksum_verified(bundle, tmp_path):
    run_experiment(bundle, config(), ["a"], tmp_path / "run")
    path = tmp_path / "run/a/predictions.jsonl"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        load_saved(bundle, tmp_path / "run/a")


def test_registry_validates_only_selected_models_and_rejects_non_text_config(
    monkeypatch,
):
    cfg = load_config(ROOT / "configs/research/llms.yaml")
    from linkpaper_eval.research_bench.config import preflight

    preflight(cfg, ["abstain"])
    with pytest.raises(ValueError, match="model ID"):
        preflight(cfg, ["gpt"])
    with pytest.raises(ValueError):
        ModelSpec(provider="transformers", model="text", gpu_index=5)
    with pytest.raises(ValueError):
        ModelSpec(provider="transformers", model="text", modality="image")


def test_cli_build_validate_and_doctor(tmp_path):
    folder = tmp_path / "compiled"
    assert (
        main(
            [
                "research",
                "build",
                "--corpus",
                str(FIXTURE / "corpus.jsonl"),
                "--groups",
                str(FIXTURE / "groups.jsonl"),
                "--out",
                str(folder),
            ]
        )
        == 0
    )
    assert main(["research", "validate", "--bundle", str(folder)]) == 0
    assert (
        main(
            [
                "research",
                "doctor",
                "--config",
                str(ROOT / "configs/research/llms.yaml"),
                "--models",
                "abstain",
            ]
        )
        == 0
    )
    assert main(["research", "validate", "--bundle", str(tmp_path / "missing")]) == 2


def test_resume_never_reloads_or_recalls_a_completed_model(bundle, tmp_path):
    output = tmp_path / "run"
    run_experiment(bundle, config(), ["a"], output)
    before = (output / "a/predictions.jsonl").read_bytes()

    def forbidden(spec):
        pytest.fail("A completed model must not be loaded on resume")

    result = run_experiment(
        bundle, config(), ["a"], output, backend_factory=forbidden, resume=True
    )
    assert result["models"]["a"]["status"] == "completed"
    assert (output / "a/predictions.jsonl").read_bytes() == before
    with pytest.raises(ValueError, match="does not match"):
        run_experiment(bundle, config(repeats=2), ["a"], output, resume=True)


def test_interrupted_run_resumes_only_missing_cases(bundle, tmp_path):
    from linkpaper_eval.research_bench.providers import AbstainBackend

    calls = []

    class Interrupted(AbstainBackend):
        def generate(self, task):
            if len(calls) == 2:
                raise KeyboardInterrupt
            calls.append(task.task_id)
            return super().generate(task)

    output = tmp_path / "run"
    with pytest.raises(KeyboardInterrupt):
        run_experiment(
            bundle, config(), ["a"], output, backend_factory=lambda spec: Interrupted()
        )
    assert len(read_jsonl(output / "a/predictions.jsonl", Prediction)) == 2

    class Complete(AbstainBackend):
        def generate(self, task):
            assert task.task_id not in calls
            calls.append(task.task_id)
            return super().generate(task)

    run_experiment(
        bundle,
        config(),
        ["a"],
        output,
        backend_factory=lambda spec: Complete(),
        resume=True,
    )
    assert len(calls) == len(set(calls)) == 8
    assert len(read_jsonl(output / "a/predictions.jsonl", Prediction)) == 8


def test_failed_resume_preflight_preserves_existing_artifacts(
    bundle, tmp_path, monkeypatch
):
    output = tmp_path / "run"
    run_experiment(bundle, config(), ["a"], output)
    before = {
        str(p.relative_to(output)): p.read_bytes()
        for p in output.rglob("*")
        if p.is_file()
    }
    monkeypatch.setattr(
        "linkpaper_eval.research_bench.runner._versions", lambda: {"changed": True}
    )
    with pytest.raises(ValueError, match="dependency versions"):
        run_experiment(bundle, config(), ["a"], output, resume=True)
    after = {
        str(p.relative_to(output)): p.read_bytes()
        for p in output.rglob("*")
        if p.is_file()
    }
    assert before == after
