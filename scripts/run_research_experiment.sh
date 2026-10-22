#!/usr/bin/env bash
# Model loading is automatic for `run --models local ...`; no separate server.
set -euo pipefail
research_repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${research_repo_root}/evaluation/src${PYTHONPATH:+:${PYTHONPATH}}"
if [[ -n "${LINKPAPER_PYTHON:-}" ]]; then
  research_python="${LINKPAPER_PYTHON}"
elif [[ -x "${research_repo_root}/.venv/bin/python" ]]; then
  research_python="${research_repo_root}/.venv/bin/python"
else
  research_python="python"
fi
exec "${research_python}" -m linkpaper_eval research "$@"
