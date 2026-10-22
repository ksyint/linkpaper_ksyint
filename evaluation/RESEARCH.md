# LINK-DELTA: 텍스트 LLM 실험 실행

이 경로는 [NeurIPS 2027 연구 제안](../docs/research/neurips-2027/PROPOSAL_KO.md)의 첫 실행 구현이다. **텍스트 근거 패킷에서 FULL / CUT / PLACEBO / SCOPE를 비교**하며, GPT·Claude·Gemini API와 로컬 Hugging Face CausalLM을 같은 입력 계약으로 실행한다.

현재 포함된 자료는 **직접 작성한 가상의 질문 2개 × 4환경 = 8개 실행 사례**다. API·로컬 로더·누출 방지·결과 집계 경로를 점검하기 위한 fixture이며, 논문용 실데이터나 모델 성능 근거가 아니다. 실험용 과학 문항은 별도로 수집·검수해야 한다.

## 1. 범위와 구현 상태

- 입력·출력은 텍스트만 허용한다. 이미지·PDF 파일·음성·비디오·웹 도구 호출은 모델에 전달하지 않는다. PDF에서 미리 추출·검수한 텍스트는 코퍼스로 사용할 수 있다.
- 로컬은 `AutoModelForCausalLM`이며 vision/audio 구성과 비텍스트 architecture를 거부한다. `trust_remote_code=False`다.
- Claude·Gemini·GPT의 내부 아키텍처가 텍스트 전용이라고 주장하는 것은 아니다. 이 벤치마크는 해당 API를 **텍스트 입력·출력 모드**로 평가한다.
- 로컬 모델은 실험 명령 실행 시 tokenizer·가중치를 자동 로드한다. HF 캐시를 우선 사용하고 없으면 설정된 revision을 다운로드한다. 별도 serving 명령이 필요 없다.
- API 모델 가중치는 제공사가 관리한다. 실행기는 인증 client를 초기화하고 각 제공사의 native text endpoint를 호출한다.
- 주 실험은 고정 근거 패킷이다. 전체 코퍼스 검색·BM25/dense/graph 비교, 실제 논문 주석 확대, 자동 의미 평가기 보정은 연구의 다음 단계다.

## 2. 한 번 설치하고 실행

아래 명령은 **레포 root** 기준이다. 새 clone의 `.venv`를 사용하며 공유 시스템 Python을 바꾸지 않는다.

```bash
# API/CPU 실험만 필요하면 --local 생략
scripts/setup_research_env.sh --local

# API 키와 GPU 없이 전체 경로 확인
scripts/run_research_demo.sh abstain

# 모델 자동 로드 → GPU 6에서 8개 가상 사례 추론 → 저장·집계
scripts/run_research_demo.sh local-smoke
```

기본 local-smoke는 고정 revision의 `Qwen/Qwen3-0.6B`다. 작은 모델의 출력 형식·추론 품질은 낮을 수 있다. smoke 성공은 논문 성능 검증을 의미하지 않는다. 실행 결과는 `evaluation/runs/research-demo-<시각>-<pid>/`에 저장된다.

실행기는 `LINKPAPER_PYTHON`을 지정하면 그 Python을 쓰고, 없으면 레포 `.venv/bin/python`, 그마저 없으면 `python`을 사용한다. 의존성은 setup 단계에서 설치하며, package import·help·doctor 명령은 가중치를 로드하지 않는다.

### GPU 제한

로컬 로더는 `nvidia-smi -i 6`으로 **물리 GPU 6의 UUID**를 찾고, torch/CUDA 초기화 전에 `CUDA_VISIBLE_DEVICES`를 그 UUID 하나로 고정한다. 그 후의 `cuda:0`은 물리 6을 뜻한다. 모델 전체는 `device_map={"": 0}`으로 배치하고, 다른 GPU로 자동 분산하지 않는다. `gpu_index`는 6만 허용한다.

CUDA가 다른 범위로 이미 초기화된 프로세스에서는 실행을 거부한다. 새 CLI 프로세스를 사용한다. 이 로더는 다른 사용자의 프로세스나 GPU를 재설정·종료하지 않는다. 사용 가능 메모리가 부족하면 실패를 기록한다.

## 3. 새 과학 문항으로 근거 환경 만들기

코퍼스와 그룹 형식은 다음 예제를 따른다.

- [fixtures/research/corpus.jsonl](fixtures/research/corpus.jsonl): 원문 span ID, 논문 ID·버전, 텍스트, 출처, 라이선스, 사람의 조건 주석.
- [fixtures/research/groups.jsonl](fixtures/research/groups.jsonl): 질문·조건, 계보/분할, 제거·교체 목록, 환경별 정답·대안 충분 근거·rubric.
- [contracts.py](src/linkpaper_eval/research_bench/contracts.py): 전체 strict 스키마.

```bash
scripts/run_research_experiment.sh build \
  --corpus /path/to/curated-corpus.jsonl \
  --groups /path/to/curated-groups.jsonl \
  --out evaluation/runs/study-v1-bundle

scripts/run_research_experiment.sh validate \
  --bundle evaluation/runs/study-v1-bundle
```

기본 구축 규칙은 다음과 같다.

| 환경 | 접근 가능한 근거 |
|---|---|
| FULL | `full_evidence_ids` |
| CUT | FULL에서 `cut_remove_ids`를 제거 |
| PLACEBO | FULL에서 `placebo_remove_ids`를 제거 |
| SCOPE | CUT에 `scope_add_ids`를 추가 |

v1 구축기는 FULL의 supported/refuted, PLACEBO의 동일 판정, CUT/SCOPE의 insufficient를 다룬다. 일반적인 mixed/자연적 시간 갱신 환경은 아직 이 구축기의 범위가 아니다.

FULL의 `sufficient_sets: [[a,b], [c]]`는 `a+b` 또는 `c`가 대안 충분 근거라는 뜻이다. CUT은 **모든** 대안을 끊어야 하고 PLACEBO는 적어도 한 대안을 보존해야 한다. Gold가 없는 근거를 인용하거나 SCOPE에 주석된 조건 차이가 없으면 구축을 거부한다. 결정적 근거 논문·계보·중복 질문이 서로 다른 split에 있으면 실패한다. 결정적 논문을 공유하는 그룹은 같은 `family_id`를 써야 한다.

이 검사는 **이미 주석한** 충분 근거에 대한 구조 검사다. 주석하지 않은 대체 근거의 부재나 과학적 정답을 인증하지 않는다. 원문·초록·표·부록·중복 버전의 잔존 근거는 독립 전문가가 검수해야 한다. 문서 수·텍스트 길이 차이도 `manifest.audit`에 기록되므로 실제 데이터는 이를 이용한 shortcut을 검사·통제한다.

### 모델 입력과 정답 격리

Bundle에는 `tasks.jsonl`, `gold.jsonl`, `source_corpus.jsonl`, `source_groups.jsonl`, 해시 manifest가 있다. **모델에 넘기는 것은 TaskInput의 질문·요청 조건·허용된 contexts뿐**이다. group/family/world, gold 판정·조건 주석·rubric·필수 근거 표시는 전달하지 않는다. 모델 실행에 gold 파일을 통째로 붙이지 않는다.

근거의 공개 인용 ID는 과제마다 별도 opaque ID로 바꾸고, 순서도 seed로 섞는다. 매 호출은 새 메시지로 실행하여 다른 환경의 대화와 이전 답변을 전달하지 않는다. 같은 질문의 네 환경은 함께 보존하고 임의의 앞 N개 사례로 자르지 않는다. `--split dev|test|holdout`으로 완전한 묶음을 선택한다.

각 파일의 hash를 실행 전에 검증한다. 원본을 수정하려면 새 버전의 bundle을 만든다. 정답·원천 파일은 평가·감사용이고, 공개 task 파일과 구분해 다뤄야 한다.

## 4. GPT·Claude·Gemini·로컬을 같은 명령으로 비교

모델은 [configs/research/llms.yaml](configs/research/llms.yaml)에서 선택한다. 명시한 alias만 초기화되며, API 모델 ID를 자동으로 최신 모델로 바꾸지 않는다.

```bash
export OPENAI_API_KEY='...'
export ANTHROPIC_API_KEY='...'
export GEMINI_API_KEY='...'

# 본인 계정에서 실제 접근 가능한 정확한 모델 ID/스냅샷 지정
export LINKPAPER_GPT_MODEL='your-gpt-model-id'
export LINKPAPER_CLAUDE_MODEL='your-claude-model-id'
export LINKPAPER_GEMINI_MODEL='your-gemini-model-id'

scripts/run_research_experiment.sh doctor \
  --config evaluation/configs/research/llms.yaml --models gpt claude gemini

scripts/run_research_experiment.sh run \
  --bundle evaluation/runs/study-v1-bundle \
  --config evaluation/configs/research/llms.yaml \
  --models gpt claude gemini local-smoke \
  --split dev --out evaluation/runs/pilot-v1
```

API adapter는 GPT의 Responses, Claude의 Messages, Gemini의 generateContent, 그리고 OpenAI-compatible Chat Completions를 지원한다. 공통 JSON 지시문을 사용하고 특정 제공사만의 JSON grammar/도구 기능을 기본으로 강제하지 않는다. `temperature`는 기본 미전달이며 지원되는 모델에서만 명시한다. GPT의 `reasoning_effort`도 선택 설정이다. 출력 제한은 API의 reasoning token을 포함할 수 있으므로 실제 usage와 stop reason을 함께 확인한다.

API 키는 지정된 환경변수에서 읽고 config·manifest에 값으로 저장하지 않는다. native API 요청 재시도는 제한되어 있고, 형식 오류를 모델에 되물어 정답을 유도하는 재시도는 하지 않는다. API 모델마다 문맥 한도·추론 설정·샘플링 지원이 다르므로 본 비교 전에 설정을 고정하고 보고해야 한다.

### 원하는 오픈소스 모델 자동 로드

```bash
export LINKPAPER_LOCAL_MODEL='organization/text-only-causal-lm'
export LINKPAPER_LOCAL_REVISION='exact-huggingface-commit-sha'

scripts/run_research_experiment.sh run \
  --bundle evaluation/runs/study-v1-bundle \
  --config evaluation/configs/research/llms.yaml --models local \
  --split dev --out evaluation/runs/local-pilot-v1
```

`local.model`에는 HF ID 또는 로컬 모델 디렉터리를 쓸 수 있다. 모델당 한 번 로드하고 모든 과제·반복을 순차 실행한 뒤 해제한다. 여러 로컬 모델은 config에 alias를 추가해 `--models model-a model-b`로 순서대로 실행한다. gated 모델은 본인 HF 접근권한이 필요하다. 모델이 지원하는 quantization 형식의 추가 의존성은 별도 설치가 필요할 수 있다.

이미 실행 중인 텍스트 serving endpoint는 `served` alias의 `LINKPAPER_SERVED_URL`, `LINKPAPER_SERVED_MODEL`로 연결한다. 이 alias는 서버를 직접 시작하지 않으며, GPU 6 제한은 **이 저장소가 직접 로드하는 로컬 backend**에 적용된다. 외부 서버의 GPU 설정은 별도이므로 본 연구에서 쓰는 서버도 GPU 6으로 구성해야 한다.

### 중단 후 재개

동일한 `run` 명령에 `--resume`을 붙이면 **이미 저장된 과제/반복의 응답을 재호출하지 않고 누락분만** 실행한다. 완료 모델은 다시 로드하지 않는다. config·bundle·지시문·연구 코드가 바뀌면 재개를 거부한다. 이미 기록된 오류 응답도 완료된 시도로 보존하며 자동 재시도하지 않는다.

응답을 받은 직후 파일에 저장하기 전에 프로세스가 강제 종료되면 해당 호출을 이미 결제했는지는 실행기만으로 판별할 수 없다. 따라서 완전한 API exactly-once 보장을 주장하지 않는다. 마지막 JSONL 줄이 물리적으로 손상되면 조용히 버리지 않고 검증 실패로 알린다.

## 5. 산출물과 점수의 의미

```text
pilot-v1/
  summary.json
  gpt/
    manifest.json       # 선택 모델·설정·버전·코드/입력 해시·GPU 정보
    predictions.jsonl   # 원시 출력, 파싱 결과, 오류, usage, stop reason, 지연
    scores.json
    report.md
  claude/ ...
```

모든 예정된 과제/반복을 점수 분모에 포함한다. 모델 로드 실패·타임아웃·차단·잘린 출력·JSON 오류는 실패로 남는다. 출력 파싱이 실패해도 이미 받은 원문과 사용량을 보존한다. 근거가 길면 몰래 자르지 않고 예산 초과로 기록한다.

| 자동 지표 | 의미 |
|---|---|
| `verdict_correct` | corpus-relative 판정 일치 |
| `verdict_macro_f1` | 해당 평가 집합의 gold 라벨을 고정해 계산한 macro-F1. 오류 응답도 FN에 포함 |
| `condition_recall` | gold 필수 조건 값의 정규화된 일치. 의미적 faithfulness는 아님 |
| `citation_validity` | 실제 전달한 ID를 인용하고 claim마다 인용이 있는지 |
| `sufficient_set_covered` | 하나 이상의 주석된 대안 충분 근거를 완전히 인용했는지 |
| `diagnostic_pass` | 위 구조 조건을 모두 충족하는지 |
| `diagnostic_pairpass` | FULL과 비교 환경 모두 통과한 질문의 비율 |
| `diagnostic_joint4` | 네 환경 모두 통과한 질문의 비율 |
| `paper_joint4` | 응답별 의미 검수를 결합한 값. 미검수 응답이 있으면 `null` |

구조적 진단은 인용 문장이 실제 주장을 함의하는지, 답변이 과학적으로 옳은지, 설명에서 조건을 과장했는지 자동 인증하지 않는다. “항상 유보”는 가상 fixture에서 판정 정확도 0.5를 얻어도 Joint4는 0이다. 이 수치는 평가 배관 예시이며 실제 과학 benchmark 결과가 아니다.

반복 실행은 같은 기본 질문 안에서 평균하고, CI는 `family_id` 군집을 재표집한다. 하나의 군집뿐이면 CI를 내지 않는다. 이 CI는 모델 간 차이의 유의성을 자동 입증하지 않으며, 별도 paired 비교·검정력 분석이 필요하다.

usage에는 제공사의 원시 token 집계를 보존한다. `input_usd_per_million`, `output_usd_per_million`을 직접 설정하면 단순 단가 추정치도 기록한다. 캐시 할인·재시도 결제·reasoning 과금 방식은 제공사마다 달라 실제 청구액과 같다고 해석하지 않는다. token usage가 빠진 경우 추정 비용은 `null`이다.

## 6. 의미 검수 후 재채점

```bash
scripts/run_research_experiment.sh export-review \
  --bundle evaluation/runs/study-v1-bundle \
  --run evaluation/runs/pilot-v1/gpt \
  --out evaluation/runs/pilot-v1-gpt-review
```

`review_context.jsonl`에는 질문·근거·rubric·모델 답변을, `reviews.jsonl`에는 채점 양식을 쓴다. 검수자는 각 답변이 모든 rubric을 만족하고 중요한 과장·허위 주장이 없는지 판단해 `semantic_pass`를 JSON boolean으로 채우고, `annotator`, `notes`를 기록한다. 실제 논문에서는 독립 검수와 불일치 조정 절차를 운영한다. 단일 self-rating은 전문가 합의의 대체가 아니다.

각 검수는 **해당 원시 답변의 SHA-256**에 묶인다. 다른 응답의 점수를 붙이거나 원문을 바꿔 재사용하면 거부한다.

```bash
scripts/run_research_experiment.sh score \
  --bundle evaluation/runs/study-v1-bundle \
  --run evaluation/runs/pilot-v1/gpt \
  --reviews evaluation/runs/pilot-v1-gpt-review/reviews.jsonl \
  --out evaluation/runs/pilot-v1-gpt-reviewed
```

기존 raw predictions를 덮어쓰지 않는다. 미검수 semantic score를 0으로 조용히 바꾸거나, 검수된 응답만 골라 논문 점수를 부풀리지 않는다. 새로운 유효 근거가 확인되면 bundle/주석 버전을 올리고 전체 모델을 같은 규칙으로 재평가한다.

## 7. 검증

```bash
cd evaluation
../.venv/bin/python -m pytest -q tests/test_research_bench.py tests/test_research_providers.py
```

API wire contract는 모의 HTTP transport로 검사한다. 실 API 평가에는 본인 키·모델 접근권한이 필요하다. GPU 실검증과 본 데이터 성능은 구분해 보고한다. CI는 CPU에서 가상 fixture와 abstain을 실행하므로 유료 API나 모델 다운로드를 사용하지 않는다.

2026-10-22 검증 기록: 연구 코드 테스트 44개를 포함해 평가 패키지 **157개 통과, 2개 skip**. skip은 Ragas 미설치 상황 전용 검사와 opt-in Docker/Neo4j 통합 검사다. 기존 Ragas wrapper의 deprecation warning 2개가 있다. Qwen3-0.6B의 위 고정 revision을 **물리 GPU 6 하나에서 자동 로드하여 8개 추론 응답**을 저장했다. 그중 6개는 출력 JSON 스키마 오류로 집계됐으며, 이를 정상 정답이나 논문 성능으로 해석하지 않는다. 실 API 호출은 하지 않았고 네 provider의 요청·응답·재시도·비밀값 비기록 계약을 모의 transport로 검사했다.

공식 구현 참고: [OpenAI text generation](https://developers.openai.com/api/docs/guides/text), [Claude Messages](https://platform.claude.com/docs/en/api/messages/create), [Gemini generateContent](https://ai.google.dev/api/generate-content), [HF chat templates](https://huggingface.co/docs/transformers/chat_templating), [Qwen3-0.6B 모델 카드](https://huggingface.co/Qwen/Qwen3-0.6B).
