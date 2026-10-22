#!/usr/bin/env bash
# Repository-local dependencies only; weights load later when an experiment runs.
set -euo pipefail
research_repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
research_extra="dev"
if [[ "${1:-}" == "--local" && "$#" == 1 ]]; then
  research_extra="dev,local"
elif [[ "$#" != 0 ]]; then
  echo "Usage: scripts/setup_research_env.sh [--local]" >&2
  exit 2
fi
research_python="${research_repo_root}/.venv/bin/python"
if command -v uv >/dev/null 2>&1; then
  if [[ ! -x "${research_python}" ]]; then
    uv venv "${research_repo_root}/.venv"
  fi
  uv pip install --python "${research_python}" -e "${research_repo_root}/evaluation[${research_extra}]"
else
  if [[ ! -x "${research_python}" ]]; then
    python3 -m venv "${research_repo_root}/.venv"
  fi
  "${research_python}" -m pip install -e "${research_repo_root}/evaluation[${research_extra}]"
fi
echo "Research environment ready: ${research_python}" >&2
