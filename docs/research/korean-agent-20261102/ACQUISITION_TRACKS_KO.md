# 저장된 논문과 외부에서 찾는 논문을 모두 실험하기

핵심 QA는 같고 정보 접근 환경을 구분한다. **Live에서는 벤치마크 episode 도중 agent가 직접 외부 논문 검색·수집·열람을 선택한다.** 미리 수집한 자료에 답만 생성하는 실행과 다르다. 실제 구현·실행 범위와 계획을 아래처럼 구분한다.

| 모드 | 시작 상태와 도구 | 목적 |
|---|---|---|
| Offline archive | 고정된 corpus에서 `search/open/citations`; private availability mask 지원 | 저장된 논문에서 발견·근거 연결·정답 능력 평가 |
| Live interleaved | 비어 있는 로컬 registry에서 `search_papers/fetch_paper/search_local/open`을 반복하고 답변 | 외부 발견·PDF 확보·로컬 색인·열람·답변을 같은 episode에서 실행 |
| Frozen live replay | 해당 live 실행의 검색 응답·PDF·추출문·활성화 시점·trace를 고정 | 네트워크/PDF 파서 없이 기록된 도구 실행과 인용을 재검증 |
| Acquire-then-answer | 별도 획득 policy가 snapshot을 만든 뒤 curated QA에 사용 | 발견/수집과 답변을 분리하는 대조·데이터 준비 |

현재 offline backend는 benchmark용 고정 JSONL archive와 결정적 텍스트 검색이다. 기존 Neo4j/Qdrant의 운영 배치·모든 production API를 이 변경으로 완성한 것은 아니다. 기존 `indexing/data_pipeline/hf_client.py`의 HF metadata/arXiv 수집 자산은 유지하며, 아직 501인 서비스 API에 기대지 않고 독립적인 평가 경로를 제공한다. 저장소의 기존 vector/store 평가와 새 도구 agent 실행도 구분해 보고한다.

## 1. 설치·offline 실행

저장소 루트에서 Python 3.11+를 사용한다. PDF 파서 선택 의존성은 `acquire`이며 exact lock에는 pypdf 6.21.4가 들어 있다. 아래 명령은 모델 가중치를 내려받거나 GPU를 사용하지 않는다.

```bash
uv sync --project evaluation --frozen --extra dev --extra acquire --python 3.12

# 새 여섯 유형의 합성 계약 검증
uv run --project evaluation --frozen python -m linkpaper_eval.agent_bench validate \
  --corpus evaluation/fixtures/scholarly_qa/corpus.jsonl \
  --cases evaluation/fixtures/scholarly_qa/cases.jsonl

# 실제 정책: private cases는 evaluator에만, 모델에는 PublicTask와 관측만 전달
uv run --project evaluation --frozen python -m linkpaper_eval.agent_bench run \
  --policy my_agent:factory --corpus /path/to/frozen/corpus.jsonl \
  --cases /path/to/private/cases.jsonl --out evaluation/runs/offline-my-agent
```

`my_agent:factory`는 사용자가 작성하는 신뢰하는 policy plugin이다. 그 자체는 OS sandbox가 아니므로 실제 held-out 평가에서는 private gold와 public 모델 프로세스의 파일 권한도 분리한다. 현재 CLI가 받은 private 파일 경로·문헌 수·task 유형은 PublicTask로 전달하지 않는다.

## 2. Episode 안에서 실제 외부 논문 검색

`live_paper_bench.py`는 같은 `Policy.step(PublicTask, history) → Action | Answer` 계약을 쓴다. 최초 harness 전용 `tool_catalog`가 허용 도구·입력·예산을 알려 준다. source 수·정답·하위 task 태그는 알려주지 않는다.

```text
질문 → search_papers → 후보 metadata
     → fetch_paper → PDF·페이지 청크를 episode registry에 적재
     → search_local → open → 필요하면 외부 검색/수집을 다시 수행 → 답변
```

검색 결과 quota나 최대 fetch 수는 자원 상한이고 정답에 필요한 문헌 수가 아니다. `search_papers`의 제목·초록·URL과 `open`의 본문은 구분한다. 현재 인용 계약은 성공한 open의 document_id를 사용한다. 검색 metadata를 보았다는 사실만으로 본문 근거를 읽었다고 채점하지 않는다.

```bash
# 네트워크 없이 동적 검색→수집→열람→답변과 strict replay를 확인
bash scripts/run_live_paper_demo.sh /path/to/new/live-fixture-output

# 실제 외부 API/PDF 경로의 제한된 연결 확인
uv run --project evaluation --frozen --extra acquire python -m linkpaper_eval.live_paper_bench run-demo \
  --provider arxiv --question 'Batch normalization의 학습 조건과 성능 근거는 무엇인가?' \
  --query 'ti:"Batch Normalization"' --max-searches 1 --max-fetches 1 --max-calls 8 \
  --out evaluation/runs/live-paper-network-smoke-new

# 실제 모델/agent 정책 연결. 검색어와 추가 검색·수집은 policy가 선택
uv run --project evaluation --frozen --extra acquire python -m linkpaper_eval.live_paper_bench run \
  --provider arxiv --policy my_agent:factory --question '실제 연구 질문' \
  --out evaluation/runs/live-my-agent
```

`run-demo`의 query override와 scripted policy는 연결 검증용이다. 질문의 의미를 풀어낸 LLM 성능 결과가 아니다. `run --policy`에서 실제 adapter를 연결하고 model ID/revision·token·비용을 따로 기록한다. 기존 JSON subprocess/HF policy도 공개 task/history 계약을 쓰며, HF prompt는 최초 tool catalog가 있을 때 그 schema를 따른다. 모델·원격 서버의 GPU 배치와 운영 timeout은 [GPU 매뉴얼](GPU_EXECUTION_KO.md)을 따른다. 이번 변경의 실제 검증에는 모델/GPU를 새로 실행하지 않았다.

상위 CLI의 `linkpaper-eval live-paper ...`와 `python -m linkpaper_eval live-paper ...`도 같은 경로다.

## 3. Replay와 검수

```bash
uv run --project evaluation --frozen python -m linkpaper_eval.live_paper_bench replay \
  --run-dir evaluation/runs/live-paper-network-smoke-new

uv run --project evaluation --frozen python -m linkpaper_eval.live_paper_bench score \
  --run-dir /path/to/live-run --reviews /path/to/response-bound-reviews.jsonl
```

replay는 hash로 고정한 검색·수집 기록과 corpus timeline으로 당시 동적 자료를 복원하고 local search/open을 다시 계산한다. 네트워크와 PDF parser는 호출하지 않는다. 관측 변조·가짜 문헌/그룹·미열람 인용·다른 task/response hash의 검수는 거부하거나 실패로 처리한다. 외부 응답을 암호학적으로 공인한다는 뜻은 아니며 실행기·파일 저장소의 신뢰 경계를 별도로 관리한다.

이는 **기록된 episode의 도구 재검증**이며 새 모델을 실행하는 명령이 아니다. 다른 policy가 새로운 검색어를 내는 실험은 별도 live 실행이나 검수된 offline archive에서 수행한다. 기록하지 않은 전체 웹의 임의 질의를 이 cassette가 재현한다고 표현하지 않는다.

`manifest.json`, `task.json`, `trace.jsonl`, `prediction.json`, `corpus.jsonl`, `corpus_timeline.json`, `tool_metrics.json`, `response_reviews.jsonl`, `scores.json`과 하위 `acquisition/`의 API 원문·PDF·parser 정보가 남는다. 원문·실행 기록은 Git ignore 대상 `evaluation/runs/`에 보관한다. 질문·원문·실행 결과의 공개 범위는 권리·held-out 정책을 따로 검토한다.

**live score는 현재 도구·인용의 구조 검증과 응답 hash 검수 기록이다.** 내려받은 draft corpus에는 자동 gold가 없어서 `scientific_semantic_accuracy=null`, `gold_available=false`를 유지한다. 모델의 과학적 정답 성능으로 쓰려면 [수작업 절차](MANUAL_LABELING_KO.md)로 private gold·대안 근거와 응답 검수를 구축해야 한다. 실제 새로운 대안 근거를 source ID/locator만으로 자동 오답 처리하지 않고 사람이 검토·버전 갱신한다.

## 4. 실패·가용성·비용 비교

offline `Case.available_evidence_ids`는 `None`이면 전체 기준 archive, `[]`이면 전체 확보 실패, 일부 ID면 실제 확보 범위다. evaluator의 원래 gold·예정 문항·분모는 유지하고 모델의 도구에서만 접근을 제한한다. 충분한 대안 중 하나가 남아 있으면 그것으로 답할 수 있다. 수집 실패를 이유로 문제를 삭제하거나 원래 정답을 정보 부족으로 바꾸지 않는다.

이 mask는 private 기준 snapshot에 실제 획득한 source/locator를 검수해 연결한 경우에 쓴다. 이름·숫자·비슷한 제목만으로 서로 다른 버전/청크를 자동 동일시하지 않는다. live는 별도 동적 registry/scorer를 사용하므로 고정 archive의 replay에 동적 도구를 그대로 넣어 점수를 만들지 않는다.

tool call·검색·fetch·총 PDF bytes·페이지·추출문·관측 문자·elapsed 예산을 기록한다. acquisition의 시간 상한은 호출 전후의 cooperative 검사이며 강제 프로세스 deadline이 아니다. HTTP timeout과 policy/model timeout도 별도로 설정한다. cold/warm cache를 구분하고 warm cache는 provider별 namespace와 원문 hash를 검증한다. 사전 색인 비용과 질문별 발견+다운로드+파싱+LLM 비용을 분리해 합산 비교한다.

현재 warm cache는 주로 원본 PDF 재사용이며 모델 답변 cache가 아니다. `downloaded_pdf_bytes_including_cache`를 순수 네트워크 전송량이라고 읽지 않는다. paper attempt별 cache hit와 지연을 함께 보고하며, raw PDF 재사용과 이미 전처리·색인된 offline archive는 다른 조건이다.

## 5. 지원 범위·공식 출처

현재 built-in live provider는 **arXiv API와 arXiv PDF**다. 일반 웹 검색 엔진·GUI browser·모든 한국어 발행처를 지원한다고 하지 않는다. 다른 발행처에는 해당 metadata schema·discovery·허용된 PDF/HTML fetch·권리·rate-limit을 검증한 adapter가 필요하다. Offline archive는 영어·한국어 다분야 자료를 수용한다. HF Daily Papers가 AI 중심이라는 편향을 전체 학술 모집단으로 확대하지 않는다.

arXiv provider는 HTTPS host/identifier·redirect·byte 제한과 순차 요청 간 기본 3초 간격을 사용한다. 원문은 article/version별 권리를 확인하기 전 `draft`와 미검증 license로 둔다. [arXiv API 매뉴얼](https://info.arxiv.org/help/api/user-manual.html), [API 이용 조건](https://info.arxiv.org/help/api/tou.html), [pypdf 텍스트 추출](https://pypdf.readthedocs.io/en/stable/user/extract-text.html).

최종 실제 실행 수치와 source hash는 [VALIDATION_KO.md](VALIDATION_KO.md)에 기록한다. CPU protocol 검증·실제 HTTP 연결·실제 LLM 답변 성능을 분리한다.
