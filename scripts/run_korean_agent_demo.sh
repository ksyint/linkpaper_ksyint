#!/usr/bin/env bash
# Original synthetic CPU fixtures only. No model/API/GPU invocation.
set -euo pipefail
agent_repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
agent_python="${LINKPAPER_EVAL_PYTHON:-${agent_repo_root}/evaluation/.venv/bin/python}"
agent_output="${1:-${agent_repo_root}/evaluation/runs/korean-agent-$(date -u +%Y%m%dT%H%M%SZ)}"
if [[ ! -x "${agent_python}" ]]; then
  echo 'Install CPU dependencies first: uv sync --project evaluation --extra dev --python 3.12' >&2
  exit 2
fi
if [[ -e "${agent_output}" ]]; then
  echo 'Choose a new output directory; existing results are preserved.' >&2
  exit 2
fi
export CUDA_VISIBLE_DEVICES=""
export LINKPAPER_POLICY_USES_GPU=0
cd "${agent_repo_root}"
mkdir -p -- "${agent_output}"
"${agent_python}" -m linkpaper_eval.agent_bench validate
for agent_name in lexical blind oracle; do
  "${agent_python}" -m linkpaper_eval.agent_bench run-demo \
    --agent "${agent_name}" --out "${agent_output}/${agent_name}"
done
"${agent_python}" -m linkpaper_eval.lineage_metric \
  --input evaluation/fixtures/lineage_metric/synthetic_triplets.json \
  --output "${agent_output}/metric-unit-demo.json" --bootstrap-samples 1000 --seed 0
for agent_name in lexical blind; do
  "${agent_python}" -m linkpaper_eval.agent_bench run-demo \
    --corpus evaluation/fixtures/agent_lineage/corpus.jsonl \
    --cases evaluation/fixtures/agent_lineage/cases.jsonl \
    --agent "${agent_name}" --out "${agent_output}/bridge-${agent_name}-run"
  "${agent_python}" -m linkpaper_eval.agent_lineage \
    --corpus evaluation/fixtures/agent_lineage/corpus.jsonl \
    --cases evaluation/fixtures/agent_lineage/cases.jsonl \
    --predictions "${agent_output}/bridge-${agent_name}-run/predictions.jsonl" \
    --triplets evaluation/fixtures/agent_lineage/triplets.jsonl \
    --out "${agent_output}/bridge-${agent_name}-scores"
done
"${agent_python}" - "${agent_output}" <<'PY'
import json
import sys
from pathlib import Path
output = Path(sys.argv[1])
for name, expected in [('lexical', 1.0), ('blind', 0.0)]:
    report = json.loads((output / f'bridge-{name}-scores/glrs.json').read_text())
    assert report['family_macro_GLRS'] == expected, (name, report)
    assert report['coverage']['total_triplets'] == 1
print('Integrated synthetic GLRS: lexical=1, blind=0 (not scientific performance).')
PY
echo "CPU fixture artifacts: ${agent_output}"
