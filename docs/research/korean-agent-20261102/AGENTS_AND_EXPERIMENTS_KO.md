# 평가할 에이전트·구성요소와 실험 계획

본 과제는 **필요한 논문 수를 알려주지 않고 하나 또는 여러 논문의 여러 근거를 연결해 답하는 것**이다. 결과 원천·재보고 판별은 6종 하위 과제 중 하나다. 원문은 영어 다수·한국어 포함, 주 질문은 한국어, 영어 질문은 같은 원문을 쓰는 대조 조건이다. 주제는 AI에 한정하지 않는다. 실제 본 데이터 모델 성능과 소형 LLM 연결 smoke·합성 fixture를 구분한다.

## 1. 에이전트 종류

| 종류 | 역할 | 공정 비교 조건 |
|---|---|---|
| closed-book LLM | 외부 근거 없이 답하는 사전지식 대조 | 근거를 읽은 agent와 같은 측정으로 포장하지 않음 |
| 단발 flat RAG | 같은 archive에서 상위 k개를 한 번 받아 답 | 필요 source 수는 제공하지 않고 검색 예산을 맞춤 |
| 반복 search/read agent | 질의 수정·근거 열람·답변/계속 탐색을 순차 결정 | 주 대상. 실제 종료 조건·prompt·retry 기록 |
| citation-graph agent | CITES를 따라 관련 논문·record 탐색 | 같은 LLM·검색 archive·총 budget |
| hybrid GraphRAG | lexical/dense와 graph 후보를 결합·재랭킹 | 검색기·생성기 차이를 동시에 바꾸지 않음 |
| 계획·근거표 memory agent | 질문을 분해하고 조건·읽은 근거·미해결 항목을 유지 | planner/memory만 추가한 대조 포함 |
| provenance-aware agent | 원천·버전·재사용 관계를 추론·기록 | 원천 과제의 후보 시스템. 일반 과제 전체에서 우승을 전제하지 않음 |
| verifier/반론 agent | 주장 지원·조건·계산·충분성을 재검토 | 같은 합산 budget에서 verifier 하나씩 추가 |
| multi-agent researcher/checker | 탐색과 검수 분업 | 모든 모델의 token·call·비용 합계로 비교 |
| 외부 deep-research 시스템 | 기존 framework 연결 | 같은 public 도구 권한이면 main, 독자 웹 권한이면 별도 track |
| oracle control | 충분근거 또는 검수한 source 범위 정보를 특권 제공 | main 순위와 분리하고 제공 정보·불완전성 명시 |

GUI browser·coding·실험 재현 agent는 인터페이스·비용·연구 목표가 달라 별도 확장이다. 기존 offline lexical/blind/oracle fixture는 계약 확인용이며 실제 학술 agent 순위가 아니다.

## 2. 중요한 내부 파트

| 파트 | 고정·기록 | ablation |
|---|---|---|
| LLM | exact ID/revision·provider·tokenizer·출력 길이·seed·generation | 같은 도구·prompt에서 계열/규모 변경 |
| 질문 해석·계획 | 목표 답 형식·조건·하위 질문·중단 기준 | 계획 없음/있음; 고정 단계/적응적 단계 |
| retriever/query rewriting | lexical/dense·embedding·index snapshot·query 언어 | 같은 budget의 lexical/dense/hybrid; KO/EN query |
| reranker | 버전·후보 수·최종 k | 동일 후보에서 on/off |
| parser/chunker | PDF·표 전사·chunk·locator·overlap | 실제 파서/사람 확인 oracle text |
| graph | CITES·version·방법/조건 관계와 정답 graph 구분 | no-graph/CITES-only/추론 graph/oracle |
| 근거 memory | 주장-근거 표·조건·단위·남은 질문·원천 | raw history/요약/구조 memory/원천 memory |
| verifier | claim support·조건 정렬·계산·상충·충분성 | 없음/self-check/독립 checker |
| 답변 구성 | 단답·수치·설명·판정에 맞는 출력·인용 | 답 정확성·근거 품질·형식 오류를 별도 집계 |
| 종료·예산 제어 | stop 기준·검색/읽기/token/시간·retry | 적응적 종료/고정 depth; 사전 등록 budget curve |
| 계측·채점 | 실제 관측·열린 근거·trace/응답 hash | gold·private task tag·known source count는 policy에 전달하지 않음 |

문헌 paper_id와 근거 record ID는 다르다. 같은 논문의 여러 record를 결합하는 과제를 포함한다. 결과 원천 과제에서만 원자적 record 하나에 unit 최대 하나를 연결한다. CITES와 사람 gold result-unit edge를 혼용하지 않는다. 후보 검색을 할 수 있다는 사실과 충분근거를 연결했다는 사실도 구분한다.

### 2.1 offline·live interleaved·frozen replay와 staged 대조

저장 archive의 search/open/citations, **한 episode 안에서 발견·fetch·로컬 검색·읽기·답변을 교차하는 live interleaved**, 그리고 hash-bound artifact로 관측을 재구성하는 **frozen replay**를 구분한다. live는 같은 `Policy.step(PublicTask, history)`에 `search_papers/fetch_paper/search_local/open` 도구를 연결하며 agent가 행동을 선택한다. 최초 catalog의 search/fetch 한도는 자원 cap이며 필요한 논문 수가 아니다. public task는 질문·언어·opaque ID만 주고 gold/task tag/source 수는 숨긴다.

현재 기본 live provider는 arXiv이며 전체 인터넷·GUI·한국 발행처 전반을 지원한다고 하지 않는다. frozen replay는 저장한 action/관측을 검증하며 네트워크와 parser를 호출하지 않는다. 새 LLM 출력을 생성하는 run과 구분한다. 별도 획득 CLI의 **discover→fetch/parse→snapshot→offline QA**는 staged acquire-then-answer 통제 조건이다. 기존 production Neo4j/Qdrant API 완성을 주장하지 않는다.

live는 질의·후보·fetch/parse·원문 hash·coverage·cold/warm cache·오류·단계별 비용을 기록한다. 현재 live 점수는 구조 진단이며 과학적 의미 정확도는 항상 null이고, 응답 hash에 묶인 사람 review는 별도 필드다. 정적 gold를 live source에 자동 이식하지 않으며 실제 source ID·locator·답·권리의 사람 검수와 mapping이 필요하다. code/plugin·가상 fixture·실제 HTTP preflight 성공은 실제 LLM의 답변 성능을 뜻하지 않는다.

## 3. 하위 과제·source 범위 분석

6종 private primary task는 논문 내부 복합 근거, 논문 사이 연결, 조건 비교, 정량 추론, 상충/부족 판단, 결과 원천이다. secondary tag는 중복 가능하며 전체 N에 다시 더하지 않는다. 한 논문/여러 논문은 agent에게 주는 모드가 아니라 **검수한 충분근거 조합의 paper-family 수를 바탕으로 한 사후 분석 축**이다.

검수한 조합 중 한 paper로 충분한 대안이 있으면 그 해결을 인정한다. 알려진 조합이 모두 두 paper를 쓴다고 더 적은 대안이 절대로 없다고 증명한 것은 아니다. `known_alternative_paper_counts`는 알려진 대안들의 수이며 전역 최소 논문 수가 아니다. 미확정 범위는 unknown/coverage 한계를 남긴다. 이 값이나 task tag를 질문·도구·ID·manifest의 agent view에 넣지 않는다.

질문에 '논문 두 편을 사용하라' 같은 힌트를 넣지 않는다. 문항별 정답 source만 검색 가능한 작은 환경을 만들거나 single/multi에 따라 다른 도구 예산을 공개하는 우회 누출도 검사한다. 후보 archive는 background/distractor를 포함하고 archive 크기와 충분근거 논문 수를 구별한다.

## 4. main 비교와 실험 ID

파일럿 후 서로 다른 backbone 두 계열을 snapshot으로 고정하고 각 backbone의 **단발 RAG / 반복 agent / CITES-hybrid / 계획·근거 memory agent** 네 설정을 같은 archive·색인·권한·총 budget으로 비교한다. provenance-aware와 multi-agent는 전체 또는 공통 층화 subset에서 추가하고 분모를 명시한다. 실제 실행하지 않은 provider/model 점수는 만들지 않는다.

| ID | 실험 | 확인할 것 |
|---|---|---|
| E0 | 계약·fixture·replay·hash·출력/오류 분모 | 소프트웨어 검증. 과학 성능 아님 |
| E1 | 6종 자연 과제에서 같은 8개 설정 비교 | 답·조건·근거 지원·연결·종료·비용; private primary task와 source 범위별 분포 |
| E2 | required-source-count 미제공 vs oracle 대조 | main은 미제공. oracle은 검수한 범위 정보의 이득과 한계를 보는 별도 특권 조건 |
| E3 | 실제 검색 vs 충분근거 oracle-read | 발견 실패와 근거 연결/추론 실패 분리. 답·private rubric은 숨김 |
| E4 | 같은 원문 KO/EN 질문 대조·query rewriting | 질문 언어 효과. 원문 EN/KO/mixed 차이는 관측 층화 분석 |
| E5 | 조건·단위·수치·상충 근거 대조 | 정보 하나를 무시한 shortcut과 계산/조건 적용 오류 |
| E6 | planner·graph·reranker·memory·verifier 제거 | 한 번에 하나, 동일 backbone과 총 budget |
| E7 | 적응적 종료·고정 depth·budget·multi-agent | 조기 종료·불필요 탐색과 실패 포함 성능-비용 curve |
| E8 | 채점·후보 지표 meta-eval | 전문가 블라인드 품질·기존 점수·0점/동점·대안 근거 감점 여부 |
| E9 | source-family holdout·archive 크기·순서·opaque ID 대조 | 누출·주제 전이·source 수 힌트·정답 source만 노출하는 shortcut |
| E10 | offline archive vs live interleaved vs staged 획득 대조; frozen replay 검증 | 같은 질문·기록 예산에서 발견/fetch/parse·읽기·종료·cache·실패·비용을 분리. live는 구조 진단/null semantic; replay는 네트워크·parser 없는 관측 검증 |
| L1 | 원천 하위 track B/R/N | 같은 record/paper 수·원천 언어 구성·질문·조건·예산에서 재보고/새 unit 반응 |
| L2 | 표현 유사도×동일/별도 원천 | DOI/text/common-parent 규칙으로 설명되지 않는 계보 판단 |

L1/L2와 [GLRS](METRICS_KO.md)는 원천 과제에만 적용한다. 다른 task의 primary 결과에 GLRS=0을 넣거나, 전 task 평균 GLRS로 순위를 만들지 않는다. L2가 단순 dedup으로 해결되면 원천 하위 기여를 줄이되 나머지 과제의 정답·근거 결과를 그대로 보고한다.

필수 저비용 대조는 blind·항상 유보, DOI/version dedup, text/embedding dedup, 단순 CITES/common-parent grouping이다. always-merge/separate는 원천 지표 퇴화 대조다. gold 답을 아는 demo oracle과 충분근거만 받는 실제 LLM oracle-read는 서로 다른 역할이다.

## 5. 지표와 해석

주 평가는 **답 형식별 정확성/의미 품질 + 실제 근거 지원·조건 일치 + 연결 실패 분석 + 실패 포함 비용**이다. 단답의 허용 alias, 수치의 단위·허용오차·계산식, 설명의 핵심 주장 rubric을 고정한다. 명제가 있는 decision task에만 네 verdict를 평가하고, 단답·수치·설명을 일괄 supported로 채점하지 않는다. reference 문자열 일치는 구조 진단이며 과학적 의미 정확성 인증이 아니다.

충분근거 조합은 대안들을 허용한다. 가능한 모든 source를 읽게 강제하는 recall이나 논문 수를 무조건 줄이는 점수를 primary로 두지 않는다. 알려진 충분 조합을 놓친 비율·불필요 열람·종료 행동을 보고하되 더 짧은 유효 대안을 발견하면 검수·재채점 규칙을 적용한다. 미검수 최소 source 수를 정답으로 만들지 않는다.

GLRS는 획득·인용한 근거의 원천 그룹·반복 불변성·새 unit 반응에 관한 별도 후보 지표다. 최종 답이나 인용의 과학적 정확성을 보증하지 않는다. 일반 연결/충분성의 새 지표를 추가하면 식·반례·shortcut·사람 meta-eval과 독립 validation을 먼저 정의하고 검증 전 세계 최초/primary 확정을 하지 않는다.

사람 R1/R2 원본은 보존하고 조정된 의미 review를 응답 hash와 연결한다. task마다 독립 reviewer·조건·대안 근거·미확인 정보를 확인하며, 자동 replay가 의미 truth를 판정했다고 하지 않는다.

## 6. 통계·파일럿·비용

기본 문항/source family를 resampling 단위로 삼고 번역·반복·통제 arm을 새 독립 N으로 세지 않는다. primary task tag 기반 집계와 전체 평균 가중법을 사전 등록하고 overlapping secondary tag 점수는 별도 분석으로 표시한다. unknown source 범위를 임의로 single/multi에 넣지 않는다. class/task/source-scope 분포와 실패·미확인·제외율을 함께 보고한다.

5인×8문항=40 pilot는 유지한다. 모든 사람이 여러 task를 탐색하고, 충분근거 검수 시간·대안 발견률·초기 IAA·source 연결 component·실제 token/latency로 확장을 결정한다. 240/300은 계획치이며 power의 증거가 아니다.

첫 preflight 예시는 8문항×2질문언어×2모델×2설정×1회=64 episodes다. pilot 전체 40×2×3반복×4모델×2설정=1,920은 1,920개 독립 문제라는 뜻이 아니다. 계보 triplet은 해당 subset에만 arm 수를 곱한다. 각 run의 input/output token·검색·저장·GPU 시간과 multi-agent 내부 호출을 합산한다. 실행·단가가 정해지지 않은 현재 총액을 확정하지 않는다.

## 7. 재현성과 GPU

data/case/source hash, parser·색인·embedding·reranker·prompt·policy/code hash, exact model snapshot, seed·예산·retry·비용·오류를 기록한다. provider alias와 resolved model을 구분한다. 숨겨진 test를 프롬프트·중단 기준 선택에 반복 사용하지 않는다.

단위·fixture 검증은 CPU다. 공개 코드는 할당받은 GPU index/UUID를 명시하고 한 장·여러 worker·외부 tensor parallel은 [GPU 매뉴얼](GPU_EXECUTION_KO.md)을 따른다. 이 호스트의 실제 GPU 실행은 사용자 지시대로 물리3만 허용한다. GPU를 새로 실행하지 않은 문서/fixture 작업을 모델 실험이라고 쓰지 않는다. 과거 [실제 smoke](REAL_LLM_SMOKE_KO.md)와 [검증 기록](VALIDATION_KO.md)은 당시 hash의 사실로 보존한다.

## 8. 본 논문 결과표

- Main: model/setting/snapshot, 전체 및 private primary task별 N/family, 답·근거·조건 품질, 오류·종료·token/비용·CI.
- Evidence scope: 검수한 충분근거의 paper-count 분포, 한 paper 대안 있음/알려진 복수 paper 대안만 있음/unknown, source-count oracle gap과 archive 크기 민감도.
- Task diagnostics: 내부/교차 논문 연결, 조건 비교·정량 계산·상충/부족, 필요한 근거 누락·조기 종료·불필요 탐색.
- Acquisition: offline/live interleaved/staged, cold/warm, 별도 frozen replay, 질의·fetch·parse·로컬 검색·읽기·종료의 성공/실패·coverage·source 매핑·단계별 비용. live 구조 진단과 hash-bound 사람 응답 review를 구분.
- Lineage subset: GLRS/component·유효 triplet N·unknown coverage, B/R/N·표현 유사도·dedup 대조.
- Language/appendix: 같은 원문 KO/EN paired gap, 원문 언어 strata 관측 분석, 모든 실패·미확인·라벨/권리/split 감사와 hyperparameters.

실험 전에는 예상 성능을 결과표에 기입하지 않는다.
