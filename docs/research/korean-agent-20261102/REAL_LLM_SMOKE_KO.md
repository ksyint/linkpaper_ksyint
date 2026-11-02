# 실제 HF LLM policy smoke: 성공 범위와 실패 기록

실행일: 2026-11-02. **Qwen/Qwen3-0.6B 한 모델을 실제로 물리 GPU3에서 실행했다.** 목적은 모델 로딩·generation·public-only JSONL policy·엄격한 출력 검사·실패 분모·trace→GLRS 연결을 확인하는 integration smoke다. 대상은 새로 작성한 **가상 B/R/N fixture 3개**이며 실제 논문 데이터나 사람 주석 test set이 아니다. 이 결과를 논문 성능, 한국어 agent 역량 비교 또는 GLRS 타당성 검증으로 사용하면 안 된다.

이후 원천 언어 구성 검사와 fixture를 보강했다. **이 문서의 실제 GPU 실행은 보강 전 corpus hash**를 사용했다. 당시 B/N은 영어2·한국어2 record, R은 영어1·한국어3이어서 원천 언어가 통제된 실험이 아니었다. 현재 fixture는 R 전용 가상 재서술 record를 영어로 다시 작성해 세 arm 모두 영어2·한국어2로 맞췄고 CPU로만 재검증했다. 아래 실제 모델의 원 응답·점수·시간·hash는 소급 변경하지 않았다. 영어 다수·다분야 본 데이터의 gold와 모델 성능은 별도 구축·측정할 대상이다.

## 1. 실제 결과: 3개 모두 schema 실패로 보존

| 항목 | 실제 관측 |
|---|---:|
| 예정 한국어 episode | 3 (B/R/N 각 1개) |
| 실제 model generation | 3 |
| 유효한 최종 Answer | 0 |
| 실패 episode | 3 |
| 실제 agent tool 호출 | 0 |
| 생성 토큰 합 | 345 |
| generation latency 합 | 12.508474초 |
| eligible triplet / 예정 triplet | 1 / 1 |
| family macro GLRS | 0.0 |
| scientific semantic accuracy | null (사람 semantic review 없음) |

세 출력은 JSON object로 읽을 수 있었지만 필수 `claims`가 없는 Answer 형태였다. `kind/verdict/answer/conditions/study_groups`는 있었으나 strict Answer schema를 충족하지 못했다. 세 번 모두 EOS stop이고 token cap에 의한 `length` 종료는 아니었다. 이 응답을 보완하거나 근거/claim을 만들어 넣지 않고 `ModelPolicyError`로 실패 처리했다.

| model call | prompt tokens | completion tokens | finish reason | latency |
|---|---:|---:|---|---:|
| 1 | 398 | 106 | stop | 5.596362초 |
| 2 | 395 | 112 | stop | 3.188651초 |
| 3 | 394 | 127 | stop | 3.723461초 |

**실제 모델이 search/open/citations를 호출하는 경로는 이 실행에서 관측되지 않았다.** 따라서 이 smoke가 실제 LLM의 다단계 도구 사용을 성공 검증했다고 쓰면 안 된다. 실제 모델→잘못된 출력→실패 기록→3개 분모 유지→core/GLRS 0 연결은 확인했다. 유효 policy→실제 Environment의 search/open 경로는 별도의 **CPU fake transport 테스트**에서 확인했으며, 이는 진짜 모델의 도구 능력 결과가 아니다.

실패를 지우고 성공한 episode만 평가하거나, 실패 응답을 heuristic tool call로 바꾸거나, oracle/lexical policy의 답을 대신 넣지 않았다. 3개 episode 한도를 지켰고 두 번째 모델이나 추가 GPU run을 수행하지 않았다. tiny LLM의 형식 실패를 큰 모델 전체나 제안 벤치마크의 난이도에 일반화할 수 없다.

## 2. 한 모델만 다운로드하고 revision/hash 고정

기존 두 narrow cache 경로를 확인했을 때 같은 revision의 config/tokenizer는 있었지만 safetensors는 없었다. 공개 모델 **Qwen/Qwen3-0.6B만** `token=False`로 다운로드했다. 저장된 HF credential을 사용하거나 사용자 비밀 토큰을 다시 사용하지 않았다.

- model ID: `Qwen/Qwen3-0.6B`
- 실제 고정 revision: `c1899de289a04d12100db370d81485cdf75e47ca`
- safetensors 파일: `model.safetensors`, 1,503,300,328 bytes
- weights SHA-256: `f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`
- tokenizer.json SHA-256: `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`
- tokenizer_config.json SHA-256: `d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101`
- config.json SHA-256: `660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd`
- 공식 model card/라이선스: [Qwen/Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B), Apache-2.0. 캐시의 LICENSE와 README도 hash에 포함했다.

config, generation_config, vocab, merges, tokenizer, LICENSE, README, weights의 실제 파일 hash는 ignored 실행 산출물 `model_metadata.json`에 모두 남겼다. model weights는 Git에 추가하지 않는다. 원래 모델 snapshot과 tokenizer를 고정하는 것이 로컬 경로 이름만 적는 것보다 중요한 재현성 정보다.

## 3. 물리 GPU3만 사용하고 소유 worker 종료

| 설정 | 실제 기록 |
|---|---|
| 장비 | NVIDIA A100 80GB PCIe |
| 물리 index / UUID | 3 / `GPU-8afc6c96-b6aa-69e2-7e1c-aad65ddc0119` |
| process 내부 device | `cuda:0`, visible count=1 |
| dtype | `torch.bfloat16` |
| 자체 PyTorch allocator cap | 8 GiB |
| 로딩 후 model allocated | 1,192,114,688 bytes |
| 기록된 최대 allocated / reserved | 1,286,434,304 / 1,361,051,648 bytes |
| thinking / sampling | `enable_thinking=False`, `do_sample=False` |
| max new / context tokens | 384 / 8192 |
| seed | 20261102 |

worker는 **torch import 전에** 명시적으로 전달한 GPU index/UUID를 UUID로 확인하고 `CUDA_VISIBLE_DEVICES`를 단일 UUID로 설정한다. 모델은 `device_map=None`으로 로드한 후 수동으로 `.to('cuda:0')`한다. `accelerate`나 자동 multi-GPU 배치를 사용하지 않는다. 프레임워크 allocator cap은 CUDA context를 포함한 장비 전체 예약량을 보증하는 수치가 아니므로 실제 peak와 process 종료도 따로 확인했다.

실행 전 GPU3의 기존 점유는 17,659 MiB, utilization 0%였다. 기존 프로세스를 종료하거나 바꾸지 않았다. 본 worker PID `254396`은 exit code 0으로 종료됐고, 이후 nvidia-smi compute-apps에서 해당 PID가 없음을 확인했다. GPU3은 다시 17,659 MiB / 0%로 관측됐다. 새 worker의 가중치/context 점유를 남겨두지 않았다.

**공개 코드에는 GPU3 default나 이 UUID를 고정하지 않았다.** `--gpu`는 필수 인자이고 명시적으로 할당받은 물리 index/UUID 한 개를 받아야 한다. 위 GPU3/UUID는 이 호스트에서 실제 사용한 실행 기록이다. 다른 환경에 portable하게 배포하더라도 해당 환경의 할당을 명시해야 한다. 현재 호스트에서의 실제 실행은 사용자 지시대로 물리 GPU3으로만 수행했다.

## 4. Python 환경 분리와 public-only 경계

기존 `/home/cole/anaconda3` Python 3.9.12에는 torch 2.8.0+cu128 / transformers 4.57.6이 있었다. evaluation의 Python 3.12 환경에는 core 평가 코드가 있다. 여러 GB 규모의 torch를 새 venv에 다시 설치하는 대신 다음처럼 분리했다.

- `scripts/hf_agent_worker.py`: Python 3.9-compatible persistent process. 한 모델만 local snapshot에서 `trust_remote_code=False`, `local_files_only=True`, safetensors로 로드한다. generation 중 HF offline mode이며 다운로드를 수행하지 않는다.
- `evaluation/src/linkpaper_eval/hf_agent_policy.py`: torch를 import하지 않는 Python 3.12 policy/transport. core의 `Action` 또는 `Answer`를 strict parser로 반환한다.
- `scripts/run_hf_agent_smoke.py`: 3개 이하 한국어 synthetic episode, max tool calls=6, observation budget=30,000자를 적용하고 evaluator-only agent_lineage bridge/GLRS로 보낸다.

모델 worker가 받는 것은 오직 PublicTask의 `task_id/question/question_language`와 현재 episode의 public tool history다. case/eligible witness/gold verdict/study_unit_id/triplet specification을 보내지 않는다. 같은 가중치 process는 재사용하지만 **매 호출마다 public task/history로 prompt를 새로 만들고 이전 episode의 답변·대화는 붙이지 않는다.** 답변 cache도 없다. 각 episode는 fresh policy/history로 시작한다.

모델은 tool action이나 final answer JSON을 직접 생성해야 한다. parser는 Markdown fence 제거, JSON substring 추출, 누락 필드 생성, tool 강제 선택, 정답 추측 fallback을 하지 않는다. duplicate JSON key, 비표준 NaN, 잘못된 schema, malformed JSON, truncation, worker/context 오류는 실패로 남긴다. 공개 모델 응답의 원문과 generation hash, token 수, latency, finish reason, prompt hash를 보관한다.

context가 8,192 token cap을 넘으면 evidence를 자르지 않고 명시적 오류로 기록한다. 모델이 길이 cap에서 끝나면 겉보기에 JSON이 완성되어도 불완전 generation으로 처리한다. source 조건/근거 누락을 숨기기 위해 조용히 history를 줄이지 않는다.

## 5. CPU boundary 테스트

실행 명령:

```bash
cd evaluation
.venv/bin/python -m pytest tests/test_hf_agent_policy.py -q
```

실제 결과: **13 passed in 0.22s**. fake worker/transport임을 명시한 테스트로 다음을 확인했다.

- Action/Answer strict JSON parsing과 미수리 정책
- truncated/error/malformed 응답의 raw 기록과 실패 전파
- fake model decision→실제 Environment search/open observation→Prediction 경로
- PublicTask에 허용한 세 필드와 public history만 전달되고 gold 필드는 전달되지 않음
- invalid 출력의 3개 예정 episode 분모 유지
- persistent subprocess의 fresh episode payload와 정상 종료

이 테스트의 성공은 모델 성능 검증이 아니다. 위 실제 모델 run의 실패 결과와 섞어 “13번 실제 모델 도구 사용 성공”으로 보고하지 않는다.

## 6. 실제 산출물과 재현 명령

산출물은 다음 **Git ignored** 디렉터리에 있으며 토큰/weights는 포함하지 않는다.

```text
evaluation/runs/hf-agent-smoke-20261102/
  model_metadata.json             # 모델/토크나이저/파일hash/dtype/GPU/worker provenance
  raw_public_responses.jsonl      # 실제 public 요청과 raw generation, tokens/latency/finish reason
  predictions.jsonl              # 3개 모두 schema failure로 남은 실제 prediction
  core_diagnostics.json          # 구조적 채점, scientific_semantic_accuracy=null
  triplets.private.json          # EVALUATOR ONLY, gold mapping 포함
  glrs.json                      # known eligible triplet의 실패를 포함한 GLRS=0
  manifest.json                  # 명령, input/code hash, 예정 수/실패 수, worker 종료 확인
  worker.stderr.log              # 라이브러리 warning/상태, 비밀키 없음
```

`git check-ignore`로 manifest가 ignored임을 확인했다. `triplets.private.json`은 synthetic fixture라도 evaluator 입력의 경계를 보여 주므로 agent prompt나 공개 tool 데이터로 사용하면 안 된다. 실제 held-out 자료에서도 같은 비공개 경계를 유지해야 한다.

worker source SHA-256은 `bbb91d11dedbf2895595c43b77912353c683499626a933f532988ac3a2a24f7b`, policy source SHA-256은 `6aee24a27ce7148c4e86d211419bb1d746e1b2d36708286b928fd79ea68555a9`로 실행 metadata에 기록돼 있다. runner/source fixture hash도 manifest에 보관했다. CLI/API 변경 후 재실행하면 새 실행 디렉터리와 새 hash를 사용해야 한다.

재현할 때 caller가 세 환경변수를 실제로 지정한다. 아래 명령은 weights를 다운로드하지 않고 이미 준비한 **같은 revision snapshot**을 사용한다. 출력 디렉터리는 기존 실행 기록을 덮어쓰지 않도록 새 경로로 지정한다.

```bash
# HF_WORKER_PYTHON: torch/transformers가 있는 Python interpreter
# HF_MODEL_SNAPSHOT: pinned Qwen3-0.6B snapshot directory
# ALLOCATED_GPU: 명시적으로 할당받은 물리 index 또는 UUID
# 이 호스트의 이번 실제 실행은 GPU3 UUID를 사용했다.
evaluation/.venv/bin/python scripts/run_hf_agent_smoke.py \
  --worker-python "$HF_WORKER_PYTHON" \
  --model-path "$HF_MODEL_SNAPSHOT" \
  --revision c1899de289a04d12100db370d81485cdf75e47ca \
  --gpu "$ALLOCATED_GPU" \
  --out evaluation/runs/hf-agent-smoke-reproduce
```

실제 모델 도구 선택/관찰/최종 답변 성공을 검증하는 후속 run은 별도로 필요하다. 현재 결과는 실제 실행을 했다는 사실과 실패를 정직하게 처리했다는 근거이며, 완료되지 않은 benchmark 개발·실제 영어·한국어 문헌 gold 수집·전문가 meta-eval을 대신하지 않는다.
