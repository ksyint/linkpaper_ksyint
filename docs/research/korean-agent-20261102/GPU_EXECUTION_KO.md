# 한 개·여러 개 GPU로 재현 가능한 평가 실행

기준일 2026-11-02. 공개 저장소는 특정 물리 GPU 번호를 강제하지 않습니다. 관리자·스케줄러가 할당한 장치 중에서 실행자가 선택합니다. 아래 0·1은 설명용 번호이며 실제 할당 번호·UUID로 바꿉니다. 이번 변경의 검증은 CPU 테스트와 mock CUDA/모델 로더로 수행했습니다. GPU 모델 적재·vLLM 서버 실행·유료 API 실험은 별도 자원 할당 후 수행하는 실행 절차입니다.

## 실행 방식의 구분

| 목적 | 실행 방식 | 이 저장소의 지원 범위 |
|---|---|---|
| 한 GPU에 들어가는 모델 평가 | 내장 `transformers` backend 또는 외부 단일 GPU 서버 | 내장 로더는 선택한 GPU 하나에 모델 전체를 둠 |
| 같은 모델로 여러 과제를 더 빨리 처리 | GPU별 독립 모델 복제본·평가 워커 | 서로 다른 계보 단위 shard와 출력 경로를 사용하고 전체 예정 과제로 재집계 |
| 한 GPU에 안 들어가는 큰 모델 적재 | 외부 서버의 tensor parallel(TP) | vLLM 같은 외부 서버를 할당한 여러 GPU로 시작한 뒤 HTTP로 연결 |
| 여러 agent의 역할 분담·토론·검증 | 알고리즘적 multi-agent 실험 | GPU 개수·모델 복제와 별도 실험 축. agent별 도구·토큰 비용 합계 비교 필요 |

독립 복제본의 데이터 병렬 처리는 처리량을, TP는 한 모델의 분산 배치를 다룹니다. GPU 수 증가 자체를 agent 알고리즘의 개선으로 해석하지 않습니다. 내장 backend에는 TP·pipeline parallel·자동 다중 GPU 분산이 구현되어 있지 않습니다. vLLM의 GPU별 복제·분산 실행 방법은 [공식 parallelism 문서](https://docs.vllm.ai/en/stable/serving/parallelism_scaling/)와 [data parallel 배포 문서](https://docs.vllm.ai/en/stable/serving/data_parallel_deployment/)를 따릅니다.

## 장치 번호와 UUID 확인

CUDA는 보이는 장치를 다시 0부터 번호 매깁니다. 예를 들어 할당된 GPU UUID 하나만 노출했다면 프로세스의 `cuda:0`은 그 UUID의 장치입니다. 호스트/컨테이너의 `nvidia-smi` 번호와 CUDA 논리 번호를 혼동하지 않습니다. 컨테이너·스케줄러 환경에서는 같은 숫자가 호스트의 같은 번호라는 보장이 없으므로 UUID를 기준으로 추적합니다. `CUDA_VISIBLE_DEVICES`의 순서·UUID 의미는 [NVIDIA CUDA 환경변수 명세](https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/environment-variables.html#cuda-visible-devices)에 설명되어 있습니다.

```bash
# 자원 할당이 끝난 실행 환경에서 번호·UUID·메모리 확인
nvidia-smi --query-gpu=index,uuid,name,memory.total --format=csv
nvidia-smi -L
```

내장 `ModelSpec.gpu_index`는 현재 실행 환경의 `nvidia-smi -i <번호>`로 조회하는 **엄격한 0 이상의 정수**입니다. bool·음수·문자열은 거부합니다. `pin_gpu(index)`는 선택한 장치를 UUID로 조회해 `CUDA_VISIBLE_DEVICES`에 그 UUID 하나만 설정하며 모델은 `device_map={"": 0}`으로 적재합니다. 이미 다른 범위로 CUDA를 초기화한 프로세스에서는 새 프로세스를 요구합니다. 기존 `CUDA_VISIBLE_DEVICES`가 있으면 그 번호/UUID 범위를 넓히는 선택을 거부합니다. 빈 mask나 MIG 인스턴스 할당을 전체 GPU 사용권으로 해석하지 않습니다. MIG 전용 배치는 운영자가 설정한 외부 서버 경로로 구성합니다. UUID 사용 배경은 [NVIDIA 배포 가이드](https://docs.nvidia.com/deploy/topics/topic_5_2_1.html)에서도 확인할 수 있습니다.

## 내장 단일 GPU 로더

저장소 root 기준입니다. 먼저 할당 번호에 맞는 별도 설정 파일을 만듭니다. 다음 예시는 shell 환경변수 `LINKPAPER_ALLOCATED_GPU_INDEX`를 사람이 명시한 정수로 받아 YAML의 정수 필드에 넣습니다. 저장소의 예제 기본값 0이 GPU0 사용 권한을 뜻하지 않습니다.

```bash
export LINKPAPER_ALLOCATED_GPU_INDEX='0'  # 실제 할당 번호로 변경
mkdir -p evaluation/runs/configs
evaluation/.venv/bin/python - <<'PY'
import os
from pathlib import Path
import yaml
raw = os.environ['LINKPAPER_ALLOCATED_GPU_INDEX']
if not raw.isdecimal():
    raise ValueError('할당 GPU 번호를 0 이상의 정수로 지정하세요')
config = yaml.safe_load(Path('evaluation/configs/research/llms.yaml').read_text())
for name in ('local', 'local-smoke'):
    config['models'][name]['gpu_index'] = int(raw)
Path('evaluation/runs/configs/local-allocated.yaml').write_text(yaml.safe_dump(config), encoding='utf-8')
PY

# 설정·키의 형식 확인: 모델을 적재하지 않음
evaluation/.venv/bin/python -m linkpaper_eval research doctor \
  --config evaluation/runs/configs/local-allocated.yaml --models local-smoke

# 실제 자원을 할당한 뒤 실행하는 모델 적재·추론 예시
evaluation/.venv/bin/python -m linkpaper_eval research run \
  --bundle /absolute/path/to/frozen-bundle \
  --config evaluation/runs/configs/local-allocated.yaml \
  --models local-smoke --split dev --out evaluation/runs/local-single-gpu
```

`local-smoke`는 작은 모델의 적재·출력 형식 점검용입니다. 본 실험은 실제 모델 ID·고정 revision·지원 dtype·문맥 길이·출력 제한·seed를 별도로 고정합니다. 서로 다른 GPU를 쓰는 로컬 모델은 각각 새 프로세스로 실행합니다. 한 프로세스의 이미 초기화된 CUDA를 다른 장치로 재배치하는 방식은 사용하지 않습니다. 실제 GPU가 부족하면 모델 적재 실패를 기록하고, 다른 GPU로 자동 확장하지 않습니다.

위 명령은 기존 LINK-DELTA 근거 패킷 실행기입니다. 새 도구 agent benchmark는 `python -m linkpaper_eval.agent_bench run --policy module:factory` 또는 JSON 명령 policy를 통해 모델 결정 함수를 연결합니다. JSON policy의 직접 로컬 GPU 사용은 `LINKPAPER_POLICY_USES_GPU=1`, `LINKPAPER_POLICY_GPU_INDEX=<할당 정수>`로 명시합니다. 이 옵션도 하나의 UUID만 노출합니다. HTTP 서버를 호출하는 CPU client는 `LINKPAPER_POLICY_USES_GPU=0`으로 두며 GPU 배치는 서버에서 별도로 관리합니다.

## 여러 GPU: 독립 평가 워커로 과제 병렬 처리

각 GPU에 들어가는 동일 모델 복제본을 하나씩 두는 방식입니다. 워커 간에는 모델 revision·프롬프트·도구 예산·관측 문자 예산·출력 토큰·seed·dtype를 맞추고, 계보 군집을 통째로 나눕니다. 같은 질문의 언어 쌍과 B/R/N 대조군은 서로 다른 워커로 찢지 않습니다. 워커별 실패·누락도 원래 전체 예정 과제 분모에 남깁니다.

다음은 평가용 `cases.jsonl`을 계보 단위로 나누는 CPU 준비 예시입니다. 기존 corpus는 고정하고, split/계보 누출 검사는 전체 원본에 먼저 적용합니다. shard 생성은 train/test 분할을 새로 만드는 과정이 아닙니다.

```bash
export LINKPAPER_CASES='/absolute/path/to/curated-cases.jsonl'
mkdir -p evaluation/runs/shards
evaluation/.venv/bin/python - <<'PY'
import json, os
from pathlib import Path
rows = [json.loads(line) for line in Path(os.environ['LINKPAPER_CASES']).read_text().splitlines() if line.strip()]
families = sorted({r['family_id'] for r in rows})
assignment = {family: index % 2 for index, family in enumerate(families)}
for worker in range(2):
    selected = [r for r in rows if assignment[r['family_id']] == worker]
    if not selected:
        raise ValueError('각 워커에 하나 이상의 전체 계보 군집이 필요합니다')
    Path(f'evaluation/runs/shards/cases-{worker}.jsonl').write_text(
        ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in selected), encoding='utf-8')
PY
```

각 워커의 GPU 선택은 실행 전에 따로 설정합니다. 예를 들어 첫 JSON policy 워커는 할당 번호 0, 둘째는 할당 번호 1을 선택할 수 있습니다. 이 숫자는 실제 할당에 맞게 바꿉니다. `LINKPAPER_POLICY_COMMAND_JSON`에는 PublicTask/history를 입력받고 Action/Answer JSON 하나를 반환하는 **사용자가 준비한 신뢰 가능한 모델 policy 명령**의 절대 argv를 넣습니다. 이 저장소의 명령 어댑터가 임의 모델의 agent 프롬프트·파서를 자동 구현하는 것은 아닙니다. 명령은 결정 단계마다 새 subprocess로 호출되므로, 큰 모델을 매번 적재하는 비용을 피하려면 할당 GPU의 상주 서버와 CPU policy client를 연결합니다.

```bash
# 별도 셸/작업 1: 이미 준비된 모델 policy를 GPU 하나에 연결
export LINKPAPER_POLICY_COMMAND_JSON='["/absolute/path/to/python", "/absolute/path/to/policy.py"]'
LINKPAPER_POLICY_USES_GPU=1 LINKPAPER_POLICY_GPU_INDEX=0 \
evaluation/.venv/bin/python -m linkpaper_eval.agent_bench run \
  --corpus /absolute/path/to/curated-corpus.jsonl --cases evaluation/runs/shards/cases-0.jsonl \
  --policy linkpaper_eval.agent_bench_policy:factory --seed 20261102 \
  --max-calls 12 --max-observation-chars 30000 --out evaluation/runs/worker-0

# 별도 셸/작업 2: 같은 모델·설정, 다른 할당 GPU와 출력 경로
export LINKPAPER_POLICY_COMMAND_JSON='["/absolute/path/to/python", "/absolute/path/to/policy.py"]'
LINKPAPER_POLICY_USES_GPU=1 LINKPAPER_POLICY_GPU_INDEX=1 \
evaluation/.venv/bin/python -m linkpaper_eval.agent_bench run \
  --corpus /absolute/path/to/curated-corpus.jsonl --cases evaluation/runs/shards/cases-1.jsonl \
  --policy linkpaper_eval.agent_bench_policy:factory --seed 20261102 \
  --max-calls 12 --max-observation-chars 30000 --out evaluation/runs/worker-1
```

워커를 늘려도 예정 case ID는 동일 seed에서 유지됩니다. worker별 predictions JSONL을 합친 다음 **전체 원래 cases**로 `agent_bench score`를 실행합니다. 중복 ID는 거부되고 누락은 실패로 집계됩니다. shard별 평균 점수를 단순 평균해 전체 점수로 쓰지 않습니다. GLRS는 원래 전체 TripletSpec으로 연결·재집계합니다.

```bash
cat evaluation/runs/worker-0/predictions.jsonl evaluation/runs/worker-1/predictions.jsonl \
  > evaluation/runs/predictions-merged.jsonl
evaluation/.venv/bin/python -m linkpaper_eval.agent_bench score \
  --corpus /absolute/path/to/curated-corpus.jsonl --cases "$LINKPAPER_CASES" \
  --predictions evaluation/runs/predictions-merged.jsonl --seed 20261102 \
  --max-calls 12 --max-observation-chars 30000 --out evaluation/runs/merged-score
```

## 여러 GPU: 한 큰 모델을 외부 vLLM TP 서버로 실행

할당된 GPU 두 개에 한 모델을 나누는 예시입니다. 내장 Transformers backend의 옵션이 아니라 별도 서버 구성입니다. 모델 architecture와 TP 크기의 호환성·장치간 통신·실제 VRAM을 운영 환경에서 확인합니다. `--tensor-parallel-size`, dtype·길이·revision 옵션은 [vLLM 분산 실행](https://docs.vllm.ai/en/stable/serving/parallelism_scaling/)과 [engine arguments](https://docs.vllm.ai/en/stable/configuration/engine_args/)에 근거합니다.

```bash
# 별도 서버 환경: 실행자가 승인된 장치의 전체 UUID 두 개를 기입
export LINKPAPER_GPU_UUID_A='GPU-REPLACE-WITH-ALLOCATED-UUID-A'
export LINKPAPER_GPU_UUID_B='GPU-REPLACE-WITH-ALLOCATED-UUID-B'
export LINKPAPER_PINNED_MODEL_PATH='/absolute/path/to/pinned-text-model-snapshot'

CUDA_VISIBLE_DEVICES="$LINKPAPER_GPU_UUID_A,$LINKPAPER_GPU_UUID_B" \
vllm serve "$LINKPAPER_PINNED_MODEL_PATH" \
  --tensor-parallel-size 2 --dtype bfloat16 --max-model-len 16384 \
  --served-model-name linkpaper-text --seed 20261102 --host 127.0.0.1 --port 8000
```

위 local snapshot은 정확한 모델 commit·tokenizer·파일 해시로 고정합니다. HF ID로 시작하는 경우에는 `--revision <정확한 commit SHA>`를 명시하고 서버가 resolve한 실제 revision도 보관합니다. `bfloat16`은 예시이며 해당 GPU·모델이 지원하는 dtype을 선택합니다. GPU 장치와 dtype 변경은 동일 조건 비교에 반영합니다. 필요 메모리가 부족하다고 공유 서버의 모든 GPU를 자동 점유하도록 바꾸지 않습니다.

vLLM 서버는 `/v1/chat/completions` 등 호환 API를 제공합니다. 같은 호스트 또는 준비된 터널의 별도 CPU 평가 client에서 기존 `served` 모델을 선택하려면 다음처럼 URL·서빙 이름을 지정합니다. API 응답의 model 이름은 weights revision 인증을 대신하지 않습니다. [공식 online serving 명세](https://docs.vllm.ai/en/stable/serving/online_serving/)와 [serve CLI](https://docs.vllm.ai/en/stable/cli/serve/)를 확인합니다.

```bash
export LINKPAPER_SERVED_URL='http://127.0.0.1:8000/v1'
export LINKPAPER_SERVED_MODEL='linkpaper-text'
evaluation/.venv/bin/python -m linkpaper_eval research run \
  --bundle /absolute/path/to/frozen-bundle --config evaluation/configs/research/llms.yaml \
  --models served --split dev --out evaluation/runs/external-tp-server
```

새 도구 agent는 같은 서버를 호출하는 policy를 따로 연결합니다. CPU client의 CUDA mask나 `gpu_index`로 원격 서버의 GPU 구성을 강제할 수는 없습니다. 서버 운영자가 할당 UUID·TP world size·프로세스 배치와 접근 범위를 확인하고 기록해야 합니다. multi-node 배포는 여기의 두 장치 예시에 포함되지 않으며 [공식 vLLM multi-node 절차](https://docs.vllm.ai/en/stable/serving/parallelism_scaling/#multi-node-deployment)를 따라 별도로 검증합니다.

## 실행 기록과 비교 기준

모델별 manifest와 서버 배포 기록에 model/tokenizer의 정확한 revision·파일 해시, backend와 Python/PyTorch/Transformers/vLLM/CUDA/driver 버전, GPU 모델·UUID·메모리, 논리↔실제 장치 대응, TP/PP/복제본 수, dtype·양자화·문맥/KV-cache 제한을 남깁니다. 총 벽시계 시간·GPU-seconds·최대 VRAM·토큰·API 비용 또는 하드웨어 비용 산정법, 호출 동시성·실패/재시도와 출력 해시도 기록합니다. 내장 backend는 실제 선택 index/UUID, logical cuda:0, dtype, TP=1, torch/transformers 버전과 GPU 총 메모리를 기록하며 실행 전후의 실제 peak 사용량·서버 로그는 운영 측에서 보완합니다.

DP worker 수나 TP 크기는 실험 자원 조건입니다. 같은 논리 agent의 예산과 multi-agent의 합산 예산을 고정하고, 자원 차이가 답변 품질에 준 영향을 분석합니다. 숨긴 test를 자원 설정이나 프롬프트 선택에 반복 사용하지 않습니다. 과거 GPU6 등 실제 실행 기록은 당시 사실로 유지하고 현재 공개 실행 설정으로 소급해서 바꾸지 않습니다.

## 이 작업 환경의 실제 실행과 공개 예제의 구분

공개 매뉴얼의 0/1·UUID 예제는 이 호스트에서 실행한 배치가 아니다. 이번 작업에서 실제 LLM 연결 검증을 수행할 때는 사용자가 별도로 허용한 **물리 GPU3 하나만** 사용한다. 모델 적재/호출 여부·버전·점수 해석은 REAL_LLM_SMOKE_KO.md와 VALIDATION_KO.md의 실제 기록을 따른다. 다중 GPU/외부 TP 명령은 여기서 실행하지 않았다.

서버의 gpu-memory-utilization, max-model-len, KV-cache와 동시성은 할당된 VRAM에 맞춰 별도로 계획한다. 예제의 TP=2나 bfloat16 자체가 임의 모델이 해당 메모리에 들어간다는 보장은 아니다. GPU 수를 늘렸을 때 처리량·GPU-seconds·비용이 어떻게 바뀌는지도 함께 보고한다.
