#!/usr/bin/env bash
# Original synthetic protocol control. No network, model or GPU calls.
set -euo pipefail
live_repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
live_python="${LINKPAPER_EVAL_PYTHON:-${live_repo_root}/evaluation/.venv/bin/python}"
live_output="${1:-${live_repo_root}/evaluation/runs/live-paper-demo-$(date -u +%Y%m%dT%H%M%SZ)}"
export CUDA_VISIBLE_DEVICES=""
export LINKPAPER_POLICY_USES_GPU=0
cd "${live_repo_root}"
"${live_python}" -m linkpaper_eval.live_paper_bench run-demo \
  --question '설정 C에서 방법 M의 측정 근거를 찾아 설명하라.' \
  --provider demo --out "${live_output}"
"${live_python}" -m linkpaper_eval.live_paper_bench replay --run-dir "${live_output}"
