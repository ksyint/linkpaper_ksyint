# 연구 설계: 필요한 논문 수를 알려주지 않는 학술 근거 연결 agent

가제: **LinkPaper-KoEvidence: Scholarly Evidence Integration without Revealing Required Source Count**. 사용자 요청에 따라 핵심 과제를 확장했다. 이 문서는 연구 가설과 구현 계획이며, 새 성능·세계 최초·학회 채택을 선언하지 않는다.

## 1. 주력 연구 질문

**영어 논문이 다수이고 한국어 논문도 포함된 학술 코퍼스에서, 한국어 질문을 받은 agent는 필요한 논문 수를 미리 알려주지 않아도 하나 또는 여러 논문의 여러 근거를 찾아 연결하고, 조건에 맞는 정답과 인용을 제시하며 적절히 탐색을 종료할 수 있는가?**

정답은 한 논문 안의 방법·표·각주·본문을 연결해 얻을 수도 있고 여러 논문의 정의·조건·결과를 연결해야 할 수도 있다. '모든 문제는 여러 논문이 필요하다'고 정하지 않는다. 기존의 **논문 결과의 조건·원천을 추적해 재보고와 새 결과를 구별하는 과제는 여러 하위 과제 중 하나**로 유지한다.

검증할 가설은 다음과 같다. 방향·크기·모델 우승은 측정 전 미정이다.

- H1: 정답에 필요한 근거 범위를 스스로 판단할 때, agent가 한 논문에서 충분한데 불필요하게 확장하거나 여러 논문이 필요한데 일찍 종료할 수 있다.
- H2: 정답을 우연히 맞히는 것과 필요한 조건·근거를 연결해 정당화하는 것은 다를 수 있다.
- H3: 동일 질문에 충분한 대안 근거 조합이 여러 개 있을 수 있다. 하나의 출제 경로·논문 수를 강제하면 타당한 해결을 오답으로 처리할 수 있다.
- H4: 같은 원문에서 KO/EN 질문 차이는 발견·연결·계산·조건 해석 등 단계별로 다를 수 있다. 다른 원문 언어 집합끼리의 차이는 별도 관측 분석이다.
- H5: 결과 원천 하위 과제에서는 표현이 다른 재보고와 표현이 비슷한 새 결과가 단순 text/DOI dedup으로 모두 해결되지 않을 수 있다.

## 2. 이미 존재하는 연구와 기여 후보

한국어 웹 멀티홉·근거 경로는 [K-BrowseComp](https://arxiv.org/abs/2606.02404), 학술 관계 탐색은 [SciNet](https://proceedings.mlr.press/v306/shao26h.html)·[AgentHop](https://arxiv.org/abs/2609.34428), 학술 검색 workflow는 [ScholarGym](https://arxiv.org/abs/2601.21654), 교차 논문 도구 추론은 [PaperArena](https://arxiv.org/abs/2510.10909), 과학적 validity 대조는 [SciValidityBench](https://arxiv.org/abs/2610.34767)가 다룬다. 한국어·논문 QA·멀티홉·도구 사용·필요 source 수 비공개 자체를 세계 최초로 주장하지 않는다.

기여 후보는 **실제 학술 정보 요구에서 독립 작성한 영어 다수·한국어 포함 다분야 자료**, **한 논문/여러 논문과 대안 충분근거가 공존하는 탐색 평가**, **조건·근거 연결·종료 판단의 실패를 분리하는 분석**이다. 결과 계보는 이 자료의 특수 능력 진단이며 전체 벤치마크의 유일 목적이 아니다. 어떤 추가 발견이 기존 benchmark와 구별되는지는 실제 파일럿과 가까운 연구의 schema·코드·부록으로 확인한다. [관련 연구](RELATED_WORK_KO.md), [실험 계획](AGENTS_AND_EXPERIMENTS_KO.md).

## 3. 하위 과제 6종

| 비공개 과제 분류 | 요구하는 근거 연결 | 예시 형태 |
|---|---|---|
| 논문 내부 복합 근거 | 같은 논문의 방법·표·각주·본문을 결합 | 특정 수치가 어느 조건·단위·범위의 값인지 설명 |
| 논문 사이 근거 연결 | 서로 다른 논문의 정의·방법·관측을 연결 | 한 문헌의 설정을 다른 문헌의 평가 조건과 연결해 답 |
| 조건을 맞춘 비교 | 대상·데이터·분할·지표·처리 조건을 정렬 | 겉보기 개선이 같은 조건의 비교인지 판정 |
| 정량 추론 | 여러 보고값과 단위·분모를 확인하고 계산 | 비율·차이·범위 계산과 원문 값/계산식 제시 |
| 상충·근거 부족 판단 | 지지·반박·범위 차이와 미보고 정보를 구별 | 충돌이 실제인지 조건 차이인지, 답을 확정할 수 있는지 설명 |
| 결과 원천·재보고 판별 | 실험·분석 결과의 출처와 재사용 관계를 확인 | 같은 원 결과의 재서술과 새 reported unit을 구별 |

분류는 서로 배타적인 실제 능력이라고 가정하지 않는다. 한 문항에 private primary tag 하나와 secondary tag 여러 개를 둘 수 있다. 태그는 출제·층화·사후 분석용이며 agent에게 정답 단서로 제공하지 않는다. 한 논문 내부 과제도 복수 근거 연결이 필요해야 하며, 모든 문항을 단일 셀 복사나 숫자 세기로 만들지 않는다.

## 4. 논문 수와 충분 근거를 다루는 규칙

agent 입력에는 질문과 공통 도구만 제공한다. '논문 2개를 찾아라', single-paper/multi-paper 정답 태그, 필요한 source/근거 개수, 정답 논문 목록·그룹은 주지 않는다. 자연 질문에 실질적으로 필요한 고유명·조건은 유지하되, 출제자가 넣은 요구 문헌 수 힌트는 제거한다. 검색 결과에서 발견한 논문의 제목·paper_id·인용 관계는 정상 관측이다.

- 후보 archive에는 관련 원문과 background/distractor를 함께 둔다. 정답용 source packet만 case별로 잘라 제공해 source 수를 쉽게 추측하게 만들지 않는다.
- `한 논문에서 충분함`은 최소 하나의 충분근거 조합이 한 paper family 안에서 완성된다는 뜻이다. 한 개 record만 읽으면 된다는 뜻이 아니다.
- `알려진 복수 논문 대안만 있음`은 현재 검수한 충분근거 조합들이 복수 paper family를 쓴다는 뜻이다. 미발견된 더 짧은 대안의 부재를 증명한 `여러 논문이 반드시 필요함` 라벨과 구분한다.
- 대안 조합에 1논문 해결과 2논문 해결이 함께 있으면 둘 다 허용한다. 2논문을 사용했다는 이유만으로 틀리거나 비효율이라고 자동 판정하지 않는다.
- 검수한 조합별 고유 paper family 수는 `known_alternative_paper_counts`, record 수는 `known_alternative_evidence_counts`로 private 집계한다. `global_minimum_certified=false`를 기본으로 하고 전역 최소를 인증하지 않는다. 대안 탐색이 미완료면 범위는 unknown으로 남긴다. agent가 실제 읽은 논문 수는 정답에 필요한 최소 수와 다르다.
- 후보 corpus 크기·문항 순서·태그·ID·예산이 single/multi/정답을 누출하지 않는지 점검한다. 답을 얻을 수 없는 사례는 단순한 source 누락 버그와 구별한다.

## 5. 정답·근거와 출력

출력은 질문의 형식에 맞는 답과 주장별 원문 인용·필수 조건이다. 단답·수치·목록·설명·판정 질문을 구분하고 각각 허용 답·단위/오차·rubric을 검수한다. 설명형 질문을 전부 `supported`로 찍지 않는다. `supported/refuted/mixed/insufficient` 네 판정은 명제가 분명한 판정 과제에 적용한다. `insufficient`는 고정된 코퍼스에서 결정할 수 없다는 뜻이며 학계 전체에 근거가 없다는 뜻이 아니다.

정답을 얻는 순서나 출제자가 사용한 source 조합 하나를 강요하지 않는다. 최소 충분근거와 타당한 대안, 각 claim을 지지하는 locator·조건·계산식을 evaluator 쪽에 남긴다. 결과 그룹 출력은 원천 하위 과제에만 요구한다. 다른 과제에서 원천 그룹을 제출하지 않았다고 감점하지 않는다.

현재 public document_id는 원문 locator를 가진 근거 record를 가리키고 paper_id와 구분된다. 일반 근거는 방법·정의·조건·각주·결과를 담을 수 있다. 결과 계보 하위 track에서만 atomic record 하나에 query-relevant unit 최대 하나를 연결한다. 같은 논문에 여러 record가 있을 수 있다. 자동 chunk가 곧 과학적 결과 단위는 아니다.

## 6. agent 환경과 주 평가

agent는 질문을 받고 `search`, `open`, `citations`로 문헌을 순차 탐색한다. 공통 archive·ID·도구 권한·예산을 사용한다. 충분한 근거가 모였는지 스스로 판단하고 답한다. 처음부터 gold 근거를 모두 넣는 packet 실험은 별도 상한 대조다.

정답·과제 태그·single/multi strata·필요 논문 수·충분근거 집합·result unit·통제 arm·split은 private evaluator에 둔다. 실제로 읽은 근거의 인용을 검증한다. Python plugin 자체는 OS sandbox가 아니므로 본 평가에서는 public 관측 server와 private evaluator의 저장소·권한도 분리한다.

주 결과는 **답 정확성/의미 품질, 근거 지원·조건 일치, 필요한 근거 연결 성공, 실패 포함 비용·종료 행동**을 함께 보고한다. '많이 읽을수록 좋음'이나 '적게 읽을수록 좋음'을 정답 대신 목적화하지 않는다. 오류·누락·timeout도 분모에 남긴다. 구조 검사가 과학적 entailment를 인증하지 않으므로 사람 또는 사람과 검증한 judge를 병행한다.

### 6.1 저장 archive·live interleaved·frozen replay

- **offline archive:** 이미 저장·색인된 고정 문헌을 search/open/citations로 탐색한다. 필요한 source 수와 task tag는 숨긴다.
- **live interleaved:** `live_paper_bench.py`에서 같은 `Policy.step(PublicTask, history)`가 한 episode 안에서 `search_papers`→`fetch_paper`→`search_local`→`open`을 필요한 순서와 횟수로 반복하고 `Answer`로 종료한다. 최초 tool catalog는 기능과 자원 cap만 알리며 gold·task type·정답 source 수를 주지 않는다. 현재 기본 외부 provider는 **arXiv**다. 전체 웹·GUI browser·한국 학술 발행처 전반의 live 지원을 주장하지 않는다.
- **frozen replay:** 저장한 hash-bound 원문·관측·action 기록으로 같은 episode의 관측을 재구성한다. replay 중 네트워크나 parser를 다시 호출하지 않는다. 이는 재현 모드이며 새로운 LLM 생성·독립 성능 실험이 아니다.
- **staged acquire-then-answer 대조:** 외부 발견·fetch/parse 후 snapshot을 고정하고 offline QA를 수행하는 별도 통제 조건도 유지한다. 이것과 live interleaved episode를 구분한다.

실험은 같은 질문과 기록된 권한·도구/시간/token budget에서 모드별 discovery·fetch·parse 실패, cold/warm cache·실제 source coverage·비용을 나누어 보고한다. live 정보는 변하므로 동일한 정보 조건이라는 주장은 frozen replay로 확인한 범위에 한정한다. 기본 arXiv provider나 연구용 adapter가 기존 LinkPaper Neo4j/Qdrant production API를 완성한 것은 아니다.

현재 live runner의 점수는 열람 인용·그룹 ID·도구 오류 등 **구조 진단**이며 `scientific_semantic_accuracy=null`, `gold_available=false`를 유지한다. 응답 hash에 묶인 사람 review는 별도 `human_response_review`로 기록한다. 실제 획득한 source/locator·정답·권리를 사람이 검수·매핑하기 전에는 과학적 정답 점수나 정적 GLRS를 붙이지 않는다. 파싱된 source는 draft이고 개별 버전의 권리는 미확인 상태로 남긴다. 동작하는 policy plugin 경로와 가상 protocol/HTTP preflight를 실제 LLM의 학술 능력 검증으로 소개하지 않는다.

## 7. 결과 계보 하위 track과 GLRS

원천 과제에서 paper/version/result/data 재사용과 `unknown`을 분리한다. 다른 DOI·저자·숫자·문장 유사도만으로 같은/새 결과를 결정하지 않는다. 새 reported unit도 같은 데이터·평가·장비를 공유할 수 있으며 통계 독립성의 인증이 아니다.

이 하위 track에서만 B/R/N 자료를 구성한다. B는 기본 자료, R은 같은 알려진 unit의 재보고가 늘어난 자료, N은 새 unit이 추가된 자료다. 질문·조건·record 수·paper 수·원천 언어 구성을 맞추고 길이·검색 순위·관련성도 검토한다. N이 항상 최종 verdict를 뒤집는다고 가정하지 않는다.

**GLRS는 이 원천 하위 track의 후보 지표다. 전체 benchmark의 primary 점수나 다른 과제의 필수 지표로 사용하지 않는다.** 일반 B-cubed·F1·중복 개입을 발명했다고 하지 않는다. [CUE-R](https://arxiv.org/abs/2604.05467)·[RARE](https://aclanthology.org/2026.acl-long.923/)·[CONFPROP](https://doi.org/10.1007/s44163-026-02245-5)와의 추가 식별력, 전문가 평가와의 타당성을 검증한다. 정의·반례·미확인 계보 제외율은 [METRICS_KO.md](METRICS_KO.md)를 따른다.

## 8. 언어·분야·멀티모달

원문은 영어 다수·한국어 포함이고 AI에 한정하지 않는다. 컴퓨터·자연과학·공학·환경·비임상 생명/농업 등 판정 역량과 이용 조건을 확보한 분야를 수집한다. 유명 venue는 탐색 층화 기준이며 원문 내용·권리·정답을 인증하지 않는다.

임시 수집 목표 영어 약80%/한국어 약20%는 사용자 확정 quota가 아니다. 분모는 중복 버전을 통합한 source-paper family이며 혼합 언어는 별도 집계한다. 같은 원문에 대한 KO/EN 질문 쌍을 검수해 질문 언어 효과를 따로 비교한다. 서로 다른 영어/한국어 원문의 성능 차이는 내용·분야 등이 섞인 관측 분석이다.

본 main 입력은 텍스트와 사람이 확인한 구조화 표다. PDF 페이지·표·행·열·캡션 locator를 보존하고 수치·단위·각주를 원문과 대조한다. 그림 인식이 핵심인 후보는 제외율을 기록하고 향후 image/oracle-text 별도 track으로 검토한다. 현재 멀티모달 benchmark가 구현됐다고 주장하지 않는다.

## 9. 데이터·split·파일럿

5인이 각 8개씩 작성하는 **40개 기본 문항 파일럿**을 유지한다. 모든 사람이 여러 과제 유형을 탐색하고, 자신의 주제나 특정 task 하나에만 고정되지 않게 한다. private primary/secondary tag·단일/복수/unknown source strata별 분포를 검토하되 확보하지 못한 사례를 만들지 않는다. 240/300개 확장은 파일럿 이후 검수 신뢰도·단가·power를 보고 결정할 계획치다. [팀·데이터 문서](TEAM_AND_DATA_KO.md).

같은 질문의 번역·반복·통제 arm·원문 버전·공유 결정적 근거와 결과 unit을 연결한 component 전체를 한 split에 둔다. component가 너무 크면 문항이나 평가 범위를 줄이고 보고한다. 모델이 실패한 문항만 골라 일반 난도를 주장하지 않는다.

## 10. 메인 논문 기여로 주장하기 위한 조건

- 한 논문/여러 논문 필요성, 대안 충분근거, 조건·계산·상충 등의 라벨이 사람 사이에서 안정적인가.
- 필요한 source 수를 주지 않았을 때의 조기 종료·불필요 탐색과 근거 연결 실패를 기존 점수보다 구체적으로 설명하는가.
- 단순 검색/RAG·일반 학술 agent·graph baseline과 같은 모델·권한·예산으로 비교해 일반화 가능한 발견이 있는가.
- 원천 하위 과제에서는 DOI/text/common-parent 규칙으로 설명되지 않는 실패와 GLRS의 추가 타당성이 있는가.
- 여러 모델·새 source family·private strata에서 효과와 비용을 확인하고 실패·unknown·제외율을 공개하는가.

한국어·다국어·agent·resource 연구로 main track 적합성을 검토하되 어떤 학회 채택도 보장하지 않는다. [ACL 2027 공식 main CFP](https://2027.aclweb.org/calls/main/) 등 해당 회차 원문은 제출 시 다시 확인한다. 기존 가상 fixture·실제 tiny-model smoke·교육용 CSV는 소프트웨어/작성법 검증이며, 이 확장 과제의 본 데이터 성능이나 신규성 증거가 아니다.
