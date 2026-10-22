"""Research CLI. Optional model dependencies are imported only by run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import load_config, preflight
from .runner import export_review, render_report, rescore, run_experiment
from .worlds import compile_study, load_bundle, write_json


def register(subparsers) -> None:
    parser = subparsers.add_parser(
        "research", help="LINK-DELTA text-only paired experiments"
    )
    commands = parser.add_subparsers(dest="research_command", required=True)
    build = commands.add_parser(
        "build", help="Validate curated evidence and compile four worlds"
    )
    build.add_argument("--corpus", type=Path, required=True)
    build.add_argument("--groups", type=Path, required=True)
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--seed", type=int, default=20261022)
    validate = commands.add_parser(
        "validate", help="Check source annotations and artifact checksums"
    )
    validate.add_argument("--bundle", type=Path, required=True)
    doctor = commands.add_parser(
        "doctor",
        help="Check selected configuration/key presence without loading models",
    )
    doctor.add_argument("--config", type=Path, required=True)
    doctor.add_argument("--models", nargs="+", required=True)
    run = commands.add_parser(
        "run", help="Automatically load selected models and run the experiment"
    )
    run.add_argument("--bundle", type=Path, required=True)
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--models", nargs="+", required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--split", choices=("dev", "test", "holdout"))
    run.add_argument(
        "--resume",
        action="store_true",
        help="Run only missing cases with the exact original code/config",
    )
    score = commands.add_parser(
        "score", help="Re-score immutable predictions, optionally with semantic reviews"
    )
    score.add_argument("--bundle", type=Path, required=True)
    score.add_argument("--run", type=Path, required=True)
    score.add_argument("--reviews", type=Path)
    score.add_argument("--out", type=Path, required=True)
    review = commands.add_parser(
        "export-review", help="Export model-blind human review files"
    )
    review.add_argument("--bundle", type=Path, required=True)
    review.add_argument("--run", type=Path, required=True)
    review.add_argument("--out", type=Path, required=True)
    for command in (build, validate, doctor, run, score, review):
        command.set_defaults(handler=dispatch)


def dispatch(args: argparse.Namespace) -> int:
    try:
        command = args.research_command
        if command == "build":
            result = compile_study(args.corpus, args.groups, args.out, args.seed)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif command == "validate":
            _, _, manifest = load_bundle(args.bundle)
            print(
                f"Valid text-only bundle: {manifest['group_count']} groups, {manifest['task_count']} tasks"
            )
        elif command == "doctor":
            config = load_config(args.config)
            preflight(config, args.models)
            print(
                "Configuration/key checks passed; no weights loaded and no API requests sent"
            )
        elif command == "run":
            config = load_config(args.config)
            result = run_experiment(
                args.bundle,
                config,
                args.models,
                args.out,
                args.split,
                resume=args.resume,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return int(any(m["status"] == "failed" for m in result["models"].values()))
        elif command == "export-review":
            count = export_review(args.bundle, args.run, args.out)
            print(f"Exported {count} semantic review records to {args.out}")
        elif command == "score":
            if args.out.exists():
                raise FileExistsError(f"Score output already exists: {args.out}")
            result = rescore(args.bundle, args.run, args.reviews)
            args.out.mkdir(parents=True)
            write_json(args.out / "scores.json", result)
            (args.out / "report.md").write_text(render_report(result), encoding="utf-8")
            print(json.dumps(result["aggregate"], indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(f"Research experiment error: {exc}", file=sys.stderr)
        return 2
