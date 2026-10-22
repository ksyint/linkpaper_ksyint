#!/usr/bin/env bash
# One-command synthetic fixture demo, including automatic local weight loading.
# Usage: LINKPAPER_PYTHON=/path/to/python scripts/run_research_demo.sh [local-smoke|abstain]
set -euo pipefail
research_repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${research_repo_root}/evaluation"
research_model_alias="${1:-local-smoke}"
research_demo_dir="runs/research-demo-$(date -u +%Y%m%dT%H%M%SZ)-$$"
echo "Synthetic fixture demo only. Outputs: ${research_demo_dir}" >&2
"${research_repo_root}/scripts/run_research_experiment.sh" build \
  --corpus fixtures/research/corpus.jsonl --groups fixtures/research/groups.jsonl \
  --out "${research_demo_dir}/bundle"
"${research_repo_root}/scripts/run_research_experiment.sh" run \
  --bundle "${research_demo_dir}/bundle" --config configs/research/llms.yaml \
  --models "${research_model_alias}" --out "${research_demo_dir}/results"
