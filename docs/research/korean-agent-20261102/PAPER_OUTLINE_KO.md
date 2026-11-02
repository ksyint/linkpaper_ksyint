# 논문 구성 초안

가제: **필요한 논문 수를 알려주지 않았을 때 한국어 학술 에이전트는 근거를 연결해 답할 수 있는가?**

영문 working title: *How Much Evidence Is Enough? Evaluating Scholarly Evidence Integration in Korean Agents*. 원문은 영어 다수·한국어 포함이며 AI에 한정하지 않는다. 제목은 제안이며 최초·우승·성능 결론을 암시하지 않는다.

연구 참여자: 김수용·정상헌·남두현·오창원·이상민. 기여문은 실제 작업 내용과 참여자 동의를 확인해 작성한다.

## 초록 골격

학술 정보 요구에 답하려면 한 논문 안의 여러 위치로 충분할 수도 있고 여러 논문의 결과·정의·조건을 연결해야 할 수도 있다. 본 연구는 필요한 논문 수를 agent에게 알려주지 않는 환경에서 한국어 질문에 답하는 탐색·근거 연결·조건 적용·종료 판단을 평가한다. 영어 다수·한국어 포함 다분야 원문과 대안 충분근거를 독립 주석하고, 동일 모델·도구·예산의 agent 설정을 비교한다. 원천 재보고 판별은 여러 하위 과제 중 하나이며 GLRS는 해당 하위 track에만 적용한다. **[실제 데이터 수·조정 전 일치·모델 결과·효과 크기는 측정 후 기입]**.

대괄호를 예상 숫자로 채우지 않는다. 표와 주장은 run ID·data version·source hash에 연결한다.

## 1. Introduction

실제 연구자의 질문으로 시작해 필요한 evidence scope를 스스로 찾고 결합하는 문제를 설명한다. 단일 논문도 여러 근거를 요구할 수 있고, 여러 논문을 읽었어도 답에 충분하지 않을 수 있다. 논문 수 비공개나 멀티홉 자체를 최초라고 하지 않는다. 기여는 완료된 새 자료·분석·측정 타당성에 한정한다.

## 2. Related Work

한국어 웹/도구 agent인 K-BrowseComp·KoTAU, 학술 검색/종합/관계 추론인 ScholarGym·ScholarQABench·PaperArena·SciNet·AgentHop, 과학 validity와 근거 개입을 비교한다. 결과 계보 관련 Greenberg·CONFPROP·CUE-R·RARE·IdeaGene는 원천 하위 track의 선행연구로 설명한다. [충돌표](RELATED_WORK_KO.md)를 유지한다.

## 3. Task and Data

저장 archive·live interleaved·frozen replay와 staged acquire-then-answer 대조의 구분, bounded shared corpus, 6종 하위 과제와 private primary/secondary tag, 실제 한 논문/여러 논문/unknown source strata, 여러 충분근거 집합과 출제 경로 비강제, 답 형식별 rubric을 정의한다. 검수한 대안의 paper 수와 전역 최소 미인증·private 유지, 조건·숫자·계산·locator, 독립 주석/조정 전 일치, 영어 다수·한국어 원문·KO/EN 질문 대조, 권리·split 연결을 설명한다.

## 4. Evaluation Protocol

공개 질문/도구와 private 정답·태그·source 수의 경계, 같은 archive·권한·예산, 실패 분모, 실제 열린 인용, 답 의미 품질·근거 지원·조건·연결·종료 행동·비용을 분리한다. 답 형식별 채점과 사람 검증을 먼저 설명하고, GLRS는 결과 원천 하위 track의 별도 절에 둔다. 전체 benchmark를 GLRS 하나로 순위 매기지 않는다.

## 5. Experimental Setup

closed-book, 단발 RAG, 반복 search/read, CITES/hybrid, planner/verifier, provenance-aware, 합산 예산 multi-agent를 비교한다. hidden-cardinality와 cardinality-oracle 대조, 충분근거 oracle-read, 같은 원문 KO/EN 대조, 구성요소·종료 기준 ablation을 사전 등록한다. oracle은 main 순위에서 분리한다. 획득 모드의 provider·네트워크/fetch/parse 실패·coverage·cold/warm cache와 QA 비용을 별도로 기록한다. live는 한 episode 안의 Policy.step과 search_papers/fetch_paper/search_local/open 교차를 지원한다. 현재 기본 provider는 arXiv이며 전체 웹·GUI·한국 발행처나 기존 production API 완성을 주장하지 않는다. frozen replay는 네트워크/parser 없이 hash-bound 관측을 검증한다. 모델 snapshot·도구·parser·색인·code·seed·비용을 고정한다.

## 6. Results

실행 전 수치를 채우지 않는다. main 결과는 실패 포함 답·근거·조건 품질과 비용, private task/source-scope strata별 점수·N·family CI다. 최소 source 수가 미확정인 자료를 임의로 single/multi에 넣지 않는다. GLRS와 B/R/N은 해당 하위 track에서만 N·적용률·component와 함께 보고한다. live는 구조 진단·semantic null과 별도 hash-bound 사람 review를 보고하며, source/gold·권리 mapping 전에는 과학적 정확도를 만들지 않는다. 가상/HTTP preflight를 실제 LLM run이라고 쓰지 않는다.

## 7. Analysis

한 논문의 충분한 근거를 놓치고 과탐색하는 경우, 여러 논문이 필요한데 조기 종료하는 경우, 대안 근거를 정당하게 사용한 경우, 조건이 다른 숫자의 잘못된 결합, 상충과 정보 부족을 혼동한 경우를 분리한다. 결과 원천 실패와 단순 text dedup의 한계는 여러 분석 중 하나다. source-count oracle의 이득을 전체 능력으로 오해하지 않는다.

## 8. Limitations and Ethics

넓어진 과제 정의가 기존 학술 QA·agent 연구와 겹친다는 한계, 제한된 외부 발견 provider와 획득·파싱 범위 및 live 변동성·정적 gold 매핑 한계, 실제 확보한 분야/언어/venue의 coverage, 대안 충분근거의 미발견 가능성·최소 source 수 불확실성, 정답성·인용·연결 채점의 타당성, 주석 전문성·시간, 원문 이용 조건·모델 오염·holdout 관리를 기록한다.

## 부록·공개 artifact

과제 정의·private metadata schema, 도구 spec, CSV annotation manual, 원래 두 검수자의 IAA/조정 로그, 대안 근거·scope audit, split graph, 제외 사유, budget/cost logs, 모든 run·오류·baseline 명령과 원천 출처를 제공한다. 교육용 예시를 실제 test gold로 발표하지 않는다. 익명 심사본은 해당 정책에 맞추되 원 저장소의 기여자 고지는 유지한다.
