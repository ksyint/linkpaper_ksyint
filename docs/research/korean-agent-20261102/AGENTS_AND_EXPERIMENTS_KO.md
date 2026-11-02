# 평가할 에이전트·구성요소와 실험 계획

이 문서의 목록은 본 데이터에서 평가할 대상이다. 현재 구현·실행한 것은 CPU 가상 fixture의 lexical/blind/oracle과 정책 plugin 계약이며, 아래의 본 데이터 LLM·multi-agent 성능을 측정했다고 주장하지 않는다. 별도의 소형 LLM smoke는 연결·출력 실패 계측이며 실제 corpus 성능과 구분한다.

원문은 **영어 다수·한국어 포함**, 주 질문은 **한국어**, 영어 질문은 같은 원문을 이용하는 대조 조건이다. 주제는 AI에 한정하지 않으며 컴퓨터·자연과학·공학·환경·비임상 생명/농업 등에서 판정 가능한 영어·한국어 문헌을 탐색한다. 영어 다수는 언어의 비중이지 특정 분야의 비중을 뜻하지 않는다. 원문 언어와 질문 언어를 하나의 `language`로 합쳐 해석하지 않는다.

## 1. 에이전트 종류

| 종류 | agent가 하는 일 | 이번 연구에서의 역할/공정 비교 |
|---|---|---|
| closed-book LLM | 외부 근거 없이 질문에 답 | 사전지식·형식 prior 대조. 탐색 agent와 같은 능력이라고 보지 않음 |
| 단발 flat RAG | 같은 검색기에서 상위 k개를 한 번 얻어 답 | 순차 탐색의 이득을 비교하는 필수 baseline |
| 반복 search/read agent | 검색어 수정·원문 열기·다음 행동을 순차 결정 | 핵심 main 대상. ReAct식 여부와 prompt 버전 고정 |
| citation-graph agent | 검색 + 원문 + CITES를 탐색 | 순차 탐색과 같은 LLM/코퍼스/예산으로 graph 접근 효과 분리 |
| hybrid GraphRAG agent | lexical/dense 후보와 그래프를 결합·재랭킹 | 검색기 차이와 생성기 차이를 동시에 바꾸지 않음 |
| provenance-aware agent | 결과 단위·버전·데이터 재사용을 working memory에 기록 | 연구 후보 baseline. 실제 계보 label을 제공하는 oracle과 구분 |
| 검증/반론 agent | 최종 전 원문 귀속·조건·새 결과 여부를 재확인 | 기존 agent에 verifier만 추가한 ablation |
| multi-agent researcher/checker | 탐색자와 검수자가 분업 | 두 모델 각각의 예산이 아닌 **합산 token/call/비용**으로 비교 |
| 외부 deep-research 시스템 | 기존 상용/공개 agent framework 사용 | 같은 public 도구로 연결할 수 있으면 main 비교, 고유 웹/검색 권한을 강제하면 별도 ecological track |
| 특권적 oracle | 충분 근거/계보를 evaluator가 제공 | reasoning upper control. agent 순위·SOTA 표에 합치지 않음 |

GUI browser agent는 같은 archive를 브라우저로 보여 주더라도 action cost와 접근 인터페이스가 다르므로 이번 API-tool main 순위에 섞지 않는다. coding/논문 재현/실험 수행 agent는 연구 질문이 달라 확장 과제다.

## 2. 에이전트 안의 중요한 파트

| 파트 | 고정/기록할 것 | 하나씩 바꿀 ablation |
|---|---|---|
| LLM backbone | provider·정확 model ID/revision·날짜·tokenizer/chat template·출력 길이·temperature·seed | 같은 도구와 prompt에서 모델 계열/규모 변경 |
| 질의 해석·계획 | 질문 분해, 조건 추출, 한국어 query rewriting | 계획 없음/있음, 한국어 query/영어 query |
| retriever | BM25/keyword/dense, embedding revision, 색인 snapshot | 같은 k/budget의 lexical/dense/hybrid |
| reranker | model/version·후보 수·최종 k | 동일 후보에서 reranker on/off |
| parser/chunker | PDF parser·table 전사·chunk rule·overlap·locator | 실제 추출/사람 확인 oracle text. 본 main에는 검수된 텍스트만 |
| graph | CITES와 version/result/data 관계를 구분한 edge schema | no-graph/CITES-only/주석 없는 추론 계보/oracle 계보 |
| 도구 router | search/open/citations allowlist·입력 schema·오류 규칙 | citation traversal만 제거; 전체 corpus 접근권은 동일 |
| working memory | 읽은 근거·조건·버전·출처 그룹과 갱신 규칙 | raw history/요약/DOI dedup/내용 dedup/결과 계보 memory |
| verifier | 주장-근거, 조건, 원 실험 출처 확인 | verifier 없음/같은 budget 안의 self-check/독립 checker |
| 답변·인용 구성 | structured Answer, claim별 source ID, unknown 처리 | 최종 점수와 분리한 형식 오류/인용 trace 분석 |
| 예산·스케줄러 | call·observation chars·LLM token·시간·실비·재시도 | 6/12/24 calls 등 사전 등록 곡선. 실제 가능한 범위 사용 |
| 계측·채점 | tool trace hash, 원문 열람 집합, 지표/검수 버전 | scorer가 알고 있는 gold는 policy에 전달하지 않음 |

현재 public document_id는 원문 locator를 가진 근거 record ID다. paper_id와 분리하고 같은 논문의 여러 결과를 서로 다른 record로 나타낸다. 통제 실험에서 source-paper 수와 record 수, record별 source_language 구성과 parent paper별 언어 profile 구성을 각각 기록하고 B/R/N에서 맞춘다.

일반 CITES와 인간 gold result-unit edge는 같은 정보가 아니다. 실제 LinkPaper graph를 연결할 때도 정답 chunk를 알려 주는 edge를 만들지 않고 원래 paper CITES와 중립적인 record 선택 절차를 고정한다. gold graph를 쓴 시스템은 oracle로 표시한다. `search`와 `open`을 하지 않은 최종 답변의 인용을 도구 성공으로 채점하지 않는다.

## 3. 최소 main 비교표

파일럿 통과 후 backbone 두 계열(예: 정확한 hosted snapshot 하나와 할당받은 GPU 메모리에서 감당 가능한 open-weight snapshot 하나)을 고정한다. 특정 최신 모델명을 미리 만들어 쓰지 않고 freeze 시점의 공식 model card와 실행 가능한 ID를 기록한다.

각 backbone에서 **단발 RAG / 반복 도구 / CITES-hybrid / provenance-aware** 네 설정을 같은 generator·색인·예산으로 비교한다. 핵심 8개 설정이다. 더 강한 third backbone과 multi-agent/checker는 공통 층화 subset 또는 전체에서 추가하고, 서로 다른 문제 집합의 평균을 직접 순위로 비교하지 않는다.

필수 저비용 대조군은 다음과 같다.

- blind/항상 같은 verdict/항상 유보: 환경 이름·개수·형식 shortcut 확인.
- DOI/version dedup: 서지 중복만 제거.
- text dedup/near-duplicate: 표현 중복만 제거.
- CITES/common-parent discount: 인용 상위 출처만 사용한 단순 계보 대조. [CONFPROP](https://doi.org/10.1007/s44163-026-02245-5)의 문제 설정을 새 발명으로 부르지 않음.
- always-merge/always-separate group: 새 지표의 퇴화 해법 점검.
- oracle-read: 같은 LLM에 충분 근거만 제공하고 정답 verdict/unit ID는 숨겨 검색 병목 측정.
- demo oracle: 현재 fixture에서 gold 답까지 아는 소프트웨어 양성 대조이며 위 oracle-read LLM 결과와 다름.

## 4. 실험 ID와 결정할 질문

| ID | 실험 | 필수 해석 |
|---|---|---|
| E0 | fixture·형식·hash·격리·budget·오류 분모 | 소프트웨어 검증. 실제 모델 능력 결과 아님 |
| E1 | 자연 문헌 test에서 8설정 비교 | 최종 의미 판단·획득·인용·unit grouping·비용을 분리 |
| E2 | 같은 결과의 반복 / 새 결과 triplet | record 수·paper 수·원문 언어 구성·질문·조건·질문 언어 고정, GLRS와 각 component |
| E3 | 표현 유사성 높음/낮음 × 결과 단위 같음/다름 | 일반 중복 제거로 설명되는지 검증하는 핵심 novelty gate |
| E4 | 같은 bundle의 KO/EN 질문 대조 + query rewriting; 원문 언어 strata | KO/EN 질문은 같은 원문·조건을 유지한 paired 대조. EN-only/KO-only/mixed source bundle 비교는 내용·분야가 다른 관측 층화 분석 |
| E5 | 실제 검색 / oracle-read / oracle lineage | 발견·해석·출처 복원의 병목 분리. 상한 대조는 main 순위에서 분리 |
| E6 | graph·reranker·memory·verifier 각각 제거 | 한 번에 하나만 변경, 동일 backbone과 총 예산 |
| E7 | budget·단일/다중 agent | 실패 포함 성능-비용 Pareto, tool·LLM 합산 지출 |
| E8 | metric meta-eval | 전문가 품질 순위·반례·기존 지표와의 추가 식별력 |
| E9 | source-family heldout, 문서 순서·opaque ID·제목 대조 | 과적합/순위·형식 shortcut/주제 전이 |

E4의 source strata는 family/venue/연도/분야/길이/권리 확보율과 유효 표본 수를 함께 보고한다. 서로 다른 영어·한국어 논문에서 생긴 차이를 원문 언어의 인과 효과라고 해석하지 않는다. source language를 바꾸려면 별도의 내용 대응·권리·번역 검수가 필요하며, 원문의 자연 번역본과 같은 의미 질문 대조도 서로 다른 실험이다.

E3에서 효과가 DOI/text dedup 또는 공통 부모 규칙만으로 설명되면 새 계보 이해 기여를 축소한다. metric의 성능 순위가 전문가의 판단과 맞지 않으면 metric을 수정하고 새로운 잠금 자료에서 검증한다.

## 5. 표준 지표와 새 지표

최종 의미 판단: expert-adjudicated accuracy/F1 및 불확실/혼합 라벨 분포. 출력 오류도 분모다. 원문 획득: admissible result-unit recall과 읽기/검색 budget. 인용: 실제 open한 source, 주장 지원·귀속·조건 일치. 계보: unit coverage, grouping, unknown 처리. 실행: 성공 종료·오류/재시도·token·시간·실비.

새 [GLRS](METRICS_KO.md)는 재보고 불변성과 새 결과 반응을 유효한 결과 단위 근거에 연결한다. 일반 B-cubed나 pair F1을 발명했다고 하지 않는다. 같은 결과의 대체 witness를 모두 강제하지 않고 적절한 1차 witness 하나로 unit coverage를 충족할 수 있어야 한다. 최종 verdict 정확도와도 분리한다.

도구 replay나 조건 문자열 일치는 구조 진단이다. 과학적 entailment·출처 판정의 타당성은 사람이 확인하거나 사람과 검증한 judge를 쓴다. 두 검수자의 원래 평가는 별도 ledger에 보관하고, 조정된 최종 review만 response hash에 묶어 scorer로 전달한다.

## 6. 통계와 표본 수

독립 표본 단위는 기본 문항/공유 결과 source family다. 번역·triplet arm·반복 run·같은 원문 버전을 새 N으로 세지 않는다. primary estimand와 가중법을 사전 등록하고 family cluster bootstrap/paired 차이를 사용한다. source-family가 하나면 유효한 family CI를 보고하지 않는다.

핵심 단일 비교/지표를 정하고 다중 ablation은 교정하거나 탐색 분석으로 표시한다. 평균·95% CI·실패율·class 분포·자료형별 coverage를 함께 보고한다. 결과를 보고 유리한 subset이나 임계값을 바꾸지 않는다. unit label이 미확정인 자료의 GLRS 적용률과 제외 이유도 공개한다.

표본 수는 pilot에서 family 내 상관과 실제 disagreement, 유효 triplet 비율을 관측한 뒤 최소효과에 대한 simulation으로 정한다. 240/300이라는 숫자 자체가 power 증거는 아니다.

## 7. 단계별 실행량과 비용

처음 model preflight는 8개 기본 문항×2언어×2모델×2설정×1회=64 episodes 정도로 작게 시작한다. triplet을 추가하면 arm 수를 곱한다. pilot 전체를 여러 번 실행하기 전에 p50/p90 token·latency·실비·오류를 기록한다.

확장 예시는 [팀 계획](TEAM_AND_DATA_KO.md)의 240그룹 중 개발40/calibration40/test160을 따른다. test160×2언어×8설정×2회=5,120 natural episodes다. 그 안의 60그룹을 유효 triplet으로 추가 검증하면 60×3arm×2언어×8설정×2회=5,760이며, 동일한 B run 1,920개를 재사용할 수 있는 정확히 같은 조건이면 총8,960개다. 이는 계획 산식이지 실행·확보한 수가 아니다. semantic review와 metric validation 비용은 별도다.

비용은 각 run의 실제 input/output token에 freeze 시점 공식 단가를 곱하고 검색·저장·GPU 시간을 더한다. 모델과 단가가 정해지지 않은 현재 단계에서 총 비용을 확정하지 않는다. multi-agent 내부 호출과 verifier 비용도 모두 더한다. 반복과 번역을 문제 수로 부풀려 효율이 좋아 보이게 하지 않는다.

## 8. 재현성과 GPU

모든 run은 data/case/source hash, parser·embedding·reranker·prompt·policy source hash, exact model snapshot, generation 옵션, code commit/dirty 상태, seed, budget, error/retry, 사용량을 보존한다. provider가 요청한 alias와 다른 resolved model을 반환하면 기록한다. 동작하지 않은 모델을 성공 denominator에서 제거하지 않는다.

수집·fixture·unit test는 CPU다. 로컬 단일 모델 backend는 사용자가 선택한 물리 GPU UUID 하나로 격리하고 logical cuda:0에 배치한다. 공개 저장소는 특정 GPU 번호를 강제하지 않는다. 여러 실험의 병렬 worker와 큰 모델 하나의 tensor parallel은 별개이며 [GPU_EXECUTION_KO.md](GPU_EXECUTION_KO.md)의 방식·한계를 따른다. GPU 수·GPU시간·token·총 호출량을 모두 기록한다.

이 세션의 실제 GPU 실행은 사용자에게 지정받은 물리3에서만 허용한다. 실제 LLM smoke는 연결·오류 계측 확인용으로 본 데이터 성능과 분리하며 [검증 기록](VALIDATION_KO.md)에 실행 여부를 남긴다.

## 9. 본 논문 결과표 틀

- Main: setting/model/snapshot, N과 family 수, failure-inclusive semantic score, citation support, unit coverage, GLRS/component, 비용·CI.
- Control: repetition invariance/new-unit response, high/low lexical similarity, DOI/text/CITES baseline.
- Language: 같은 원문을 사용한 KO/EN 질문 paired gap과 oracle-read gap. 원문은 EN-only/KO-only/mixed strata의 N·family 수·분야·venue·접근성 구성을 함께 보고하고 관측 차이로 제한.
- Metric: 전문가 순위 일치·기존 점수와의 불일치·공격 baseline·적용률/unknown.
- Appendix: 모든 실패·exclusion·raw disagreement·budget curve·split component와 전체 hyperparameters.

실험 전에는 이 표에 예상 성능을 채우지 않는다.
