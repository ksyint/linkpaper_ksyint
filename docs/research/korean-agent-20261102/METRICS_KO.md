# GLRS: 근거계보 반응 점수 연구 후보

**핵심 과제 v2에서 이 문서는 `result_provenance` 하위 track 전용이다.** 전체 benchmark는 필요한 논문 수를 알려주지 않는 단일/다중 논문 근거 연결 QA이며, 비교·계산·상충/충분성 등을 함께 다룬다. 일반 QA에는 GLRS를 강요하거나 미적용을 0점으로 평균내지 않는다. 전체 평가와 적용 분모는 [TASK_SUITE_KO.md](TASK_SUITE_KO.md)를 따른다. 아래의 primary GLRS라는 표현은 이 하위 track 안에서의 후보 주 점수다.

작성일: 2026-11-02. **Grounded Lineage Response Score(GLRS)**는 이 브랜치에서 독립적으로 구현한 **연구 후보**다. 이미 알려진 cluster matching/precision–recall, count error, matched intervention과 보수적 결합을 사용한다. B-cubed는 비교용 보조 진단에만 사용한다. 이들의 수학적 최초 제안이나 과학적으로 검증된 새 지표라고 주장하지 않는다. 새로운 부분으로 검증할 대상은 “실제 결과 계보를 사람이 확인한 영어 다수·한국어 포함 실험 문헌과 한국어 중심 질문에서, 반복 보고에는 unit 수를 유지하고 새 보고 단위에는 반응하는가를 취득한 근거와 함께 측정한다”는 구성과 적용 범위다. 이 구성의 novelty와 타당성도 아래 비교·human meta-eval이 끝나야 주장할 수 있다.

**최종 primary GLRS는 C/A를 포함한 엄격한 certificate 후보 점수다. 부드러운 일반 품질 순위 점수가 아니며, 부분 unit-matching G와 각 gate를 함께 보고한다.**

코드: `evaluation/src/linkpaper_eval/lineage_metric.py`. 기존 `agent_bench/`를 변경하지 않는 독립 CPU scorer다. 합성 계산 예제로 지표 계약을 검증했으며 본 평가용 실제 gold corpus, 실제 agent의 과학적 성능 또는 사람 품질평가 결과를 만들지 않았다. 소량 원문 수집 예시는 독립 검수된 gold와 별개다.

주제는 AI에 한정하지 않는다. 영어·한국어의 자연과학·공학·환경·비임상 생명/농업 등에서도 같은 운영 정의를 사용할 수 있는지 pilot에서 검토하고, 실제 검수된 분야만 결과의 적용 범위로 주장한다. 영어 다수는 언어 구성의 목표이며 분야 비중을 정하지 않는다.

## 1. 무엇을 재고 무엇을 증명하지 않는가

하나의 episode에서 문서를 결과 unit별로 잘 묶는 것만으로는 반복 근거에 과민 반응하는지 알기 어렵다. 반대로 unit 수 변화만 맞히면 잘못된 문서를 인용하거나, 열지 않은 근거의 라벨을 추측해도 점수를 얻을 수 있다. GLRS는 한 base case의 **B/R/N 세 세계에서 취득·인용한 근거의 unit matching 품질**, **반복 보고에 대한 count 유지**, **새 reported unit에 대한 count 반응**을 함께 확인한다.

reported unit은 문헌에서 식별 가능한 실험/분석/측정 결과의 보고 단위다. 서로 다른 저자·논문·DOI를 통계적으로 독립인 실험으로 보지 않는다. 새 reported unit이어도 평가 데이터·시료·장비·연구과제를 공유할 수 있다. **GLRS는 통계적 독립성 점수가 아니다.** 원문으로 계보를 확인하지 못한 gold는 unknown으로 분리하며 독립/새 unit으로 추정하지 않는다.

점수가 1이어도 최종 결론의 진실성, claim–span entailment, 실험 타당성, 인과성 또는 사용자의 전체 연구 목표 달성을 증명하지 않는다. 올바른 그룹을 제출하면서 결론 문장은 틀릴 수 있다. 최종 답변/조건 적용/semantic correctness는 별도 사람 또는 검증된 채점 절차로 평가한다. 검색 비용·latency도 별도 보고한다.

## 2. evaluator-only matched triplet

### 2.0 입력 granularity: 논문 전체가 아닌 atomic evidence record

이 지표에서 `doc_id`/`publicdocument_id`와 `gold_units`의 key는 **원문 논문 전체의 ID가 아니라, 해당 질문/실험 조건에 관련된 결과 unit을 최대 하나만 담는 atomic result/evidence record ID**다. 기존 API의 document 명칭을 쓰더라도 아래 식의 item은 이 record다. core에는 record의 `paper_id`와 원본 page/table/row/column/span locator를 별도로 보존한다.

한 논문이 서로 다른 두 결과 단위를 보고하면 서로 다른 record로 나누고, 같은 parent `paper_id`에 연결한다. 하나의 논문 ID에 서로 다른 gold unit 두 개를 동시에 배정하거나, 논문의 모든 결과를 한 cluster 대상으로 취급하면 안 된다. 원문에서 같은 문단/표가 여러 unit을 언급하면 query-relevant 부분을 구분한 record와 정확한 locator를 만들고 주석으로 검증한다. 이런 record들은 같은 source/result family에 묶어 split 누출도 막는다. 여기서 record 하나의 unit ID는 논문 전체의 단일 실험 ID라는 뜻이 아니다.

`len(gold_units)`의 control은 **visible RECORD 수**다. 물리적인 원문 논문 수와 다르다. core bridge는 parent `paper_id`와 `source_language` metadata를 이용해 B/R/N의 unique parent-paper 수, record별 원문 언어 빈도, parent-paper별 언어 profile 빈도를 같게 검사하고 보고한다. profile은 그 paper_id의 visible record에 선언된 source_language의 정렬된 집합이다(예: `en+ko`; `mixed`는 별도 값). 이 독립 metric JSON schema에는 parent mapping이나 source_language가 없으므로 standalone scorer만으로 논문 수 또는 원문 언어 구성 control을 검사했다고 주장할 수 없다. episode의 `language`는 질문 언어다. source 논문 수, record 수, 텍스트 길이/정보량, 검색 rank와 노출 예산은 각각 구분하여 감사한다. atomic record 경계를 잘못 만든 경우 수식이 원문 의미를 자동 복구하지 못한다.


| 세계 | 의미 | curator가 확인할 조건 |
|---|---|---|
| B, base | 기준 문헌 bundle | 알려진 eligible unit과 실험 조건 |
| R, repeat | 같은 알려진 unit의 재보고/재서술 비중을 바꾼 bundle | B의 알려진 eligible unit 집합 자체를 유지 |
| N, new | 새 eligible reported unit을 추가한 bundle | B unit을 모두 유지하면서 새 unit 1개 이상 포함 |

세 세계는 질문 문장, 질문 언어, 조건 mapping, 전체 visible evidence RECORD 수가 같다. core 경로에서는 unique parent-paper 수, record별 source_language 빈도, parent-paper별 언어 profile 빈도도 같아야 한다. 새/반복 문서를 넣기 위해 기존 중복 문서 또는 적절한 padding 문서를 교체할 수 있지만, 그 때문에 기준 unit이 사라지면 유효한 new/repeat control이 아니다. 사람이 조건/문서 길이·형식·관련성·이용 가능성/도구 예산도 검토한다. **record 수나 source 논문 수를 같게 했다는 사실만으로 과학적으로 타당한 intervention이 완성되지는 않는다.**

에이전트 결과가 달라지는지, 특정 모델이 실패하는지를 보고 main case를 골라서는 안 된다. source와 gold 관계를 먼저 정하고 intervention 조건을 검증한다. 답변을 본 뒤 편리한 계보·eligible set으로 고치면 평가 누출이다.

### 2.1 입력 필드

입력은 triplet의 JSON list다. 각 triplet은 `triplet_id`, `group_id`, `family_id`, `B`, `R`, `N`을 가진다.

- `group_id`: 같은 base case의 언어 변형/반복 실행을 묶는 ID.
- `family_id`: source/version/study/result/task family가 공유되는 평가 cluster. 이는 보수적인 resampling 단위이며 통계적 독립성의 증명이 아니다.
- 각 episode의 gold: `question`, `language`(`ko`/`en`), `conditions`, `gold_units`(`atomic evidence record ID → curator unit ID 또는 null`), `eligible_ids`.
- `gold_units`에는 eligible 여부와 관계없이 **해당 episode에서 보이는 모든 evidence record ID**가 들어간다. 이 mapping 길이가 record 수 control이며 parent-paper 수는 별도다. `eligible_ids`는 이 지표가 평가하는 gold 문서 집합이다.
- `gold_units[d]=null`이면서 `d`가 eligible이면 계보 미확인이다. 해당 triplet은 GLRS의 eligible population에서 제외하고 이유/coverage를 보고한다. ineligible padding의 null은 알려진 eligible unit 판정을 대신하지 않는다.
- agent 결과: `study_groups`(`atomic evidence record ID → 임의의 cluster label 또는 null`), `opened_ids`, `cited_ids`, `error`.

`study_groups` label은 agent가 붙인 불투명한 문자열이며 gold unit ID를 알려 주지 않는다. 같은 partition에 임의의 이름을 다시 붙여도 점수는 같다. 세계마다 다른 label 이름을 써도 된다. gold unit ID는 curator가 세 세계 사이의 동일 보고 단위를 일관되게 식별할 때만 공유한다.

`opened_ids`는 agent의 자기주장 대신 harness가 성공적으로 전달한 문서 ID에서 얻어야 한다. `cited_ids`도 실제 최종 출력의 인용에서 추출한다. 이 모듈은 전달받은 trace ID가 진실하다고 가정하므로, 거짓 opened log를 탐지하는 보안 도구는 아니다. gold mapping/eligible set은 agent prompt, retrieval index, 공개 tool 응답에 넣지 않는다.

## 3. primary grounding: supported result-unit matching

**주 grounding G는 문서 recall이 아니라 결과 unit의 취득·인용·일관된 매칭을 평가한다.** 같은 unit의 적절한 대안 witness가 여러 개라면 그중 하나만 인용해도 해당 unit의 근거를 확보할 수 있다. 같은 결과를 다른 문서에서 반복 인용했다고 더 많은 gold unit으로 보상하지 않는다.

한 세계 w에서 D는 사전에 정한 admissible gold witness evidence-record ID 집합이고, `gold_units[d]`는 evaluator가 확인한 unit ID다. U = {gold_units[d] : d∈D}, k=|U|다. D가 같은 unit의 대안 witness 여러 개를 포함할 수 있으며 **모든 D 문서를 인용할 의무는 없다.** 서로 다른 unit을 빠뜨리면 recall이 낮아진다.

agent의 `study_groups`에서 null이 아닌 label별로 문서를 모아 claimed cluster를 만든다. label의 이름은 비교하지 않고 partition만 사용한다. agent가 문서를 실제로 열거나 인용했는지와 관계없이 **주장한 모든 non-null cluster를 p에 센다.** 각 cluster가 unit u를 인증할 수 있는 조건은 다음과 같다.

1. cluster에 배정한 모든 문서가 harness `opened_ids`와 실제 `cited_ids` 모두에 있다.
2. 모든 배정 문서의 gold unit이 알려져 있고 모두 같은 u다. 미등록/unknown 문서를 섞거나 서로 다른 unit을 합치면 해당 cluster는 인증할 수 없다.
3. cluster 안에 D에 속하는 admissible witness가 하나 이상 있다. D 밖의 known-u 문서를 함께 묶을 수는 있지만, 그러한 문서만으로는 unit을 인증하지 못한다.

인증 가능한 cluster가 가리키는 **서로 다른 gold unit 수**를 m이라고 한다. 동일 unit을 여러 disjoint cluster로 주장해도 m은 한 번만 늘고 p는 cluster마다 늘어난다. 각 인증 cluster는 한 unit에만 연결되므로 모호한 최대-weight 매칭을 따로 추측하지 않는다.

```text
p = non-null claimed cluster 수 (invalid/unsupported cluster도 포함)
k = distinct known gold eligible result-unit 수
m = consistent + opened + cited + admissible-witness cluster로 매칭된 distinct unit 수

P_w = m / p                    (p=0이면 0)
R_w = m / k
G_w = 2·P_w·R_w / (P_w+R_w)    (분모=0이면 0)
    = 2m / (p+k)              (정의되는 경우)
```

agent 오류/누락은 G=0이다. eligible gold lineage가 unknown이거나 k를 정의할 수 없는 빈 gold는 G/GLRS=null과 제외 사유로 보고한다. 에이전트 실패를 이 unknown-gold exclusion으로 바꾸지 않는다.

`study_groups`에 없거나 null인 citation은 background/유보 인용이다. 그것은 새 unit 주장이 아니므로 p를 늘리지 않으며 background citation 수와 unopened citation 수를 별도 보고한다. 반대로 non-null group을 주장했다면 그 안에 unopened/uncited 문서가 하나만 있어도 해당 cluster는 invalid이고 p에 남는다. 근거 없이 unit count만 적는 방식은 m을 늘리지 못한다. 이 지표는 background citation 문장의 사실성이나 미주장 문헌 사용을 평가하지 않으므로 그것은 별도 semantic/citation 평가의 몫이다.

### 3.1 필수 회귀 사례: 적절한 대안 witness 불변성

```text
gold: a→u, b→u, D={a,b}
agent 1: a를 열고 인용하여 한 cluster로 주장          → m=1,p=1,k=1,G=1
agent 2: a,b를 열고 인용하여 같은 cluster로 주장       → m=1,p=1,k=1,G=1
agent 3: a,b를 각각 별도 unit cluster로 주장           → m=1,p=2,k=1,G=2/3
```

앞서 검토한 문서별 B-cubed-style recall 변형은 agent 1을 0.4로 낮추는 구성이었다. 이는 적절한 primary witness 하나를 골라 인용한 답을 부당하게 낮추므로 **primary G에서 제거했다.** 현재 코드의 `document_bcubed_diagnostic`은 그 문서 기준 계산을 비교/실패 분석용으로만 남긴 것이며 GLRS에 들어가지 않는다. 인용 ID를 반복하거나 같은 unit의 올바른 witness를 같은 cluster에 더해도 primary G가 변하지 않는 회귀 검증을 포함한다.

### 3.2 남아 있는 한계

strict cluster 인증은 작은 mixed-unit 오류나 잘못 끼어든 문서 하나로 해당 cluster 전체 매칭을 잃을 수 있다. valid alternative가 D에 빠져 있으면 주석이 보수적으로 agent를 감점할 수 있으므로 D를 source 검토 단계에서 충분히 확인하고 이견을 기록해야 한다. 새 unit의 중요도·실험 신뢰성·claim entailment는 m에 반영되지 않는다. 같은 unit 안의 여러 조건/하위 결과를 하나로 볼지의 codebook이 잘못되면 점수도 잘못된다. 이러한 한계 때문에 사람이 보는 결과 계보 품질과의 meta-eval이 필요하다.

## 4. 유지 I, 반응 S와 GLRS

알려진 eligible gold unit의 수와, agent가 주장한 모든 non-null cluster 수를 다음과 같이 둔다.

```text
K_w     = k_w
hatK_w  = p_w   # invalid/unsupported claimed cluster도 포함

I = 1 - min(1, |(hatK_R - hatK_B) - (K_R - K_B)|)
S = 1 - min(1, |(hatK_N - hatK_B) - (K_N - K_B)|
              / max(1, |K_N - K_B|))
C = Π[w∈{B,R,N}] 1[invalid_claimed_clusters_w=0
                     AND duplicate_supported_clusters_w=0 AND agent_error_w 없음]
A = |matched_N_units ∩ (U_N − U_B)| / |U_N − U_B|
GLRS_i = C · min(G_B, G_R, G_N) · I · S · A
```

검증된 repeat에서는 `K_R-K_B=0`, new에서는 `K_N-K_B≥1`이다. 잘못된 citation이나 unopened/uncited 문서로 만든 claimed cluster도 hatK에 남고 grounding에서 false positive가 된다. 실제 근거 없는 수 변화로 I/S만 맞추면 아래 C/A가 primary 점수를 차단하고 G는 부분 진단으로 남는다. episode 자체가 실패하면 G=0이며, 제출한 cluster 수는 진단용으로 남긴다. 분류 오류가 서로 상쇄되어 count delta만 맞는 경우도 G가 이를 제한한다.

각 episode의 P/R/G, gold K, predicted K, matched unit 수, supported/invalid/duplicate cluster 수, 배경·unopened 인용 수, missing gold unit 수, agent error/missing 상태를 출력한다. triplet에는 gold/predicted delta, I, S, C, A, min G, GLRS와 certificate 실패 사유를 각각 남긴다. matched unit identity는 evaluator 전용 상세 출력에만 있으며 agent에 노출하면 안 된다. 단일 숫자만 보고 실패 원인을 숨기지 않는다.

### 4.1 가짜 count 보정과 old-unit 재취득을 막는 C/A

C는 세 세계에서 주장한 unit cluster가 모두 인증 가능하고, 같은 unit을 여러 cluster로 중복 주장하지 않았는지 확인한다. error가 있으면 C=0이다. source가 unknown이라 인증하지 못하는 cluster는 “거짓으로 증명됨”이 아니라 “certify할 수 없음”을 뜻한다. null/background 인용은 unit 주장이 아니므로 C를 깨지 않는다. C=1이면 각 claimed cluster가 서로 다른 known eligible unit 하나에 매칭되어 p=m이다. 따라서 근거 없는 cluster나 duplicate cluster를 추가해 count delta만 맞추면 C=0이 되어 primary GLRS를 높일 수 없다. 이때도 G의 부분 점수와 실패 사유를 출력해 문제를 분석한다.

A는 단순한 count 증가가 아니라 **실제로 N에서 취득·인용해 매칭한 새 gold unit identity의 coverage**다. B에서 누락했던 OLD unit을 N에서 새로 발견해 p가 1 늘었다고 해도, 실제 `U_N−U_B`에 속한 unit을 못 찾았다면 A=0이다. 예를 들어 B/R이 old A만 찾고 N이 old A/B만 찾은 경우 I=S=1일 수 있지만 새 C를 취득하지 않았으므로 A=0이다. 새 unit이 여럿이면 확인한 새 unit의 비율을 사용한다.

두 수정은 원래 `minG·I·S`만 쓰던 draft의 구체적인 gaming 반례를 막기 위해 추가했다. 당시 B/R=2 unit, N이 old 2개만 찾은 예측에 unsupported 세 번째 cluster를 추가하면 S가 0에서 1로 바뀌어 G=2/3 수준의 점수를 얻는 문제가 있었다. 최종 C는 이 cluster를 인증하지 못해 0이며 A도 실제 새 unit이 없으므로 0이다. 이 draft 식을 primary metric으로 소개하지 않는다.

C가 엄격해도 coherent한 부분 coverage는 가능하다. gold가 B/R={old A,B}, N={old A,B,new C}이고, agent가 B/R에서 old A만, N에서 old A+new C만 정확히 주장한다면 C=I=S=A=1이다. old B의 일관된 누락은 G에서 감점되어 GLRS=2/3이다. 모든 문서나 모든 old unit을 반드시 인용해야만 점수를 얻는 완전-성공 전용 지표는 아니다.

**정수 count를 쓰므로 I는 사실상 0/1 gate다.** 새 unit이 정확히 1개 추가되면 S도 0/1이다. 새 unit이 2개 이상일 때만 이 식의 S가 부분 점수를 줄 수 있다. 그래서 작은 오류에도 0으로 포화되거나 여러 시스템이 동점이 되는 문제가 있을 수 있다. C도 하나의 미인증/중복 주장을 primary 0으로 만드는 hard gate이고, A는 실제 새 unit을 찾지 못하면 0이다. min G와 곱 결합도 보수적이라 하나의 약한 세계가 점수를 제한한다. 이 brittleness를 숨기거나 부드러운 새 지표라고 표현하지 않는다. 평균/soft retention 등은 사전 등록한 ablation으로 비교하고, held-out 결과를 본 뒤 유리한 조합을 골라 main 지표로 바꾸지 않는다.

## 5. control 검증과 eligibility

standalone 구현은 질문·조건·질문 언어·record 수 불일치, repeat의 unit 집합 변경, new의 기준 unit 누락/새 unit 미증가를 `ValueError`로 거절한다. repeat의 count만 같고 기존 unit을 다른 unit으로 바꾼 경우도 repeat이라고 볼 수 없어 거절한다. new의 총 count가 증가해도 기존 unit을 잃었다면 거절한다. 이는 요청된 count 검사보다 강한 구성 검증이다.

unknown gold가 있는 triplet은 잘못된 control이라고 단정할 수 없으므로 공통 형식 control은 검사하되, 미확인 unit 집합 비교를 추정으로 수행하지 않고 metric ineligible로 보고한다. 다만 B와 N 등 비교 가능한 known 세계 사이에서 이미 확인되는 control 위반은 다른 세계의 unknown으로 가리지 않고 거절한다. empty eligible gold도 별도 사유로 보고한다. 이 처리는 unknown을 독립 unit으로 세지 않기 위한 적용 범위 정의이며, unknown 인지/유보 능력을 잘 측정했다는 뜻은 아니다. 그 능력은 별도의 사람 평가 또는 검증된 유보 task로 평가해야 한다.

standalone scorer에는 parent-paper mapping/source_language가 없으므로 물리 논문 수와 원문 언어 구성이 같다는 검증은 하지 못한다. core bridge가 `record_count`, `source_paper_count`, `record_source_language_counts`, `source_paper_language_profile_counts`를 따로 대조하고 manifest에 남긴다. 이 검사는 사람이 선언한 본문 언어 metadata를 이용하며 언어 판정을 자동 인증하지 않는다. 단순 형식 검사로 새 reported unit의 진실성, 같은 조건, 문헌 권리, corpus family 독립성을 증명할 수는 없다. 이 부분은 `TEAM_AND_DATA_KO.md`의 원문 locator/hash·독립 주석·조정 절차가 필요하다.

### 5.1 실패/누락 분모

agent의 optional 결과 필드가 없으면 빈 예측으로 처리한다. 해당 episode의 G=0이므로 known-gold triplet의 GLRS도 0이다. 잘못된 타입/빈 cluster label 등 malformed optional agent payload는 명시적 `invalid_agent_prediction` 실패로 바꿔 0으로 남긴다. gold/question/control 자체의 구조 오류는 조용히 0이나 제외로 삼키지 않고 실행 오류로 돌려준다.

JSON list의 동일 triplet ID 중복도 분모 중복 위험이므로 거절한다. 같은 group을 서로 다른 family로 지정한 경우도 거절한다. 수집된 gold나 예측이 없는 사례를 scorer 호출 전에 삭제하면 이 scorer가 원래 분모를 복원할 수 없으므로, 외부 harness는 사전 등록한 모든 triplet을 제출해야 한다.

## 6. 집계와 family bootstrap

기본 출력은 세 가지다.

1. triplet macro: eligible triplet별 평균. 반복/언어 variant가 많은 group에 가중치가 더 실릴 수 있어 진단용으로 함께만 보고한다.
2. group macro: 같은 base group의 eligible 언어/반복 triplet을 평균한 뒤 group을 같은 가중치로 평균한다.
3. family macro: group 평균을 같은 family 안에서 평균한 뒤 family를 같은 가중치로 평균한다. source/result family의 큰 덩어리가 점수를 지배하지 않도록 **주요 후보 요약**으로 사용한다.

known-gold agent 오류/누락의 0도 이 평균에 포함된다. unknown-gold ineligible은 main GLRS 분모에 넣지 않지만, 전체/eligible triplet·group·family 수, coverage, 제외 사유, 실패/누락 수를 함께 보고한다. main 결과는 **known eligible population에 조건부인 점수**다. unknown을 많이 제외한 모델/데이터가 더 일반적인 문제를 잘 푼다고 주장할 수 없다. gold eligibility는 모델별로 바뀌면 안 된다.

`--bootstrap-samples`를 지정하면 eligible family 평균을 family 단위로 복원 추출해 percentile 95% 구간을 계산한다. eligible family가 2개 미만이면 CI는 null이며 사유를 기록한다. 반복/언어 variant를 독립 sample로 bootstrap하지 않는다. 2개 family만으로 신뢰성 높은 추정을 보장하지 않으며, 실제 분석에는 충분한 family와 사전 정한 반복 수(예: 2,000회 이상), 비교 모델 간 같은 family의 paired 분석이 필요하다. 이 단일 scorer의 CI는 모델 차이에 대한 paired bootstrap을 대신하지 않는다.

## 7. 원래 합성 예제와 손계산

`fixtures/lineage_metric/synthetic_triplets.json`은 이 구현에서 새로 만든 **가상의 계산용 자료**다. 문서·unit·조건·질문은 실제 논문이 아니고 모델 실행 결과도 아니다. 각 세계에는 atomic evidence record 4개가 있다. 이 standalone fixture에는 parent-paper mapping이 없으며 물리 논문 수 control을 검증한 예제가 아니다.

```text
B gold units: A, A, B, B      K_B=2
R gold units: A, A, A, B      K_R=2
N gold units: A, A, B, C      K_N=3
```

| 예측 정책/문제 | predicted K (B/R/N) | I | S | GLRS (C/A도 적용) |
|---|---:|---:|---:|---:|
| 모두 열고 인용하며 정확한 partition | 2/2/3 | 1 | 1 | 1 |
| 모든 문서를 항상 하나로 합침 | 1/1/1 | 1 | 0 | 0 |
| 모든 문서를 항상 별도 unit으로 구별 | 4/4/4 | 1 | 0 | 0 |
| R에서 반복 A 하나를 새 unit으로 오인, 나머지 정확 | 2/3/3 | 0 | 1 | 0 |
| N의 새 C를 기존 B로 합침, 나머지 정확 | 2/2/2 | 1 | 0 | 0 |
| R 응답 누락 또는 아무 문서도 열지 않음 | R valid assertion 없음 | 별도 출력 | 별도 출력 | 0 (G_R=0) |
| eligible gold에 unknown 존재 | 확정하지 않음 | null | null | null + coverage 사유 |
| N의 실제 새 unit 없이 unsupported group으로 delta만 맞춤 | 2/2/3 | 1 | 1 | 0 (C=0,A=0) |
| N에서 놓쳤던 OLD unit만 새로 취득 | 1/1/2 | 1 | 1 | 0 (C=1,A=0) |
| coherent한 old A만 B/R, old A+new C만 N에 주장 | 1/1/2 | 1 | 1 | 2/3 (C=A=1) |

always-merge/separate는 보조 document-B-cubed 점수가 0보다 클 수 있지만 새 unit에 반응하지 않아 GLRS가 0이다. primary unit-matching G에서는 서로 다른 unit을 하나로 합친 cluster도 인증되지 않는다. 이는 이 후보가 겨냥한 실패에 대한 계산상 성질이지 모든 사람 품질 순위에서 우월하다는 실증이 아니다.

작은 grounding 손계산도 검증한다. 서로 다른 두 gold unit 문서 a/b를 각각 올바르게 열고 인용해 두 cluster로 주장하고, unknown/ineligible x를 세 번째 unit cluster로 추가 주장하면 m=2,p=3,k=2여서 P=2/3, R=1, G=0.8이다. a만 한 unit으로 주장하면 P=1, R=1/2, G=2/3이다. x를 background/null group으로만 인용하면 새 unit 주장이 아니므로 이 precision 분모에는 넣지 않는다. 일반적인 precision/recall 원리를 사용한 것으로, 이 계산 자체가 새로운 지표의 근거는 아니다.

fixture 두 번째 triplet은 R의 agent 결과를 의도적으로 비워 알려진 gold의 누락 실패를 남긴다. 첫 예제 1, 둘째 0, 서로 다른 두 합성 family의 macro는 0.5다. 합성 예제의 0.5를 실제 benchmark 성능으로 인용하면 안 된다.

## 8. 비교해야 하는 단순 지표와 관련 연구

| 비교 | 그 지표/방법이 보는 것 | GLRS 후보에서 추가로 검증할 차이/한계 |
|---|---|---|
| raw citation/document count | 인용/문서 개수 | record 수와 source 논문 수를 따로 통제한 B/R/N에서 재서술과 새 reported unit의 차이를 구별하는지. 인용 수가 많다고 결과 unit이 많지는 않음 |
| DOI exact dedup / 텍스트 near-dedup | 문서/표현의 중복 | 서로 다른 문서의 같은 원래 결과, 같은 문서의 여러 새 조건 결과를 구별하는 실제 라벨에 필요한지. similarity를 scientific lineage로 간주하지 않음 |
| 일반 B-cubed/episode grouping | 한 세계의 partition 일치 | 대안 witness를 허용하는 unit matching과 acquisition/citation 인증 및 세 세계의 반응을 결합할 필요가 실제로 있는지. GLRS가 더 많은 0/동점을 만들어 유용한 차이를 잃는지도 검토 |
| unit count delta만 평가 | 반복/new 조건의 수 변화 | 잘못된 문서/그룹을 이용한 count 상쇄를 G가 제한하는지. 반대로 문서 누락의 과도한 감점 문제도 검토 |
| [중복/다양성 RAG 실험](https://arxiv.org/abs/2608.13956) (Duplicate-RAG 대조) | exact duplicate/paraphrase/diverse evidence 조건에서 RAG 효과 | 인공 텍스트 중복과 사람이 확인한 실제 reported-result 계보를 구분. 기존 control의 이름을 바꾼 기여가 되지 않게 동일 setting 대조 |
| [CUE-R](https://arxiv.org/abs/2604.05467) | REMOVE/REPLACE/DUPLICATE로 evidence utility·grounding·confidence·trace 변화를 평가 | intervention 자체의 선행연구를 인정. GLRS가 추가하는 partition/count 조건이 독립적 인간 판단과 더 맞는지 비교 |
| [RARE](https://aclanthology.org/2026.acl-long.923/) | 원자 사실 중복을 고려하는 검색 평가 | fact/문서 중복을 reported experimental unit 계보와 혼동하지 않음. RARE류 점수로 충분하면 새 composite 필요성이 약해짐 |

보조 document-B-cubed는 Bagga와 Baldwin의 1998년 coreference 평가 계열을 따른다. 주 G의 cluster–unit matching과 precision/recall 역시 일반적인 평가 구성 요소를 task에 맞게 적용한 것이다. 역사와 구현 대조는 [공식 coreference reference scorers](https://conll.github.io/reference-coreference-scorers/)도 확인한다. B-cubed, F1, clipping, min/product 결합, intervention을 새 원리로 주장하지 않는다. 관련 자료의 추가 요약·확인 범위는 `RELATED_WORK_KO.md`와 `sources.json`에 있다. 이 모듈에 기존 프로젝트 코드나 질문을 복사하지 않았다.

## 9. 반드시 필요한 HUMAN meta-eval

unit test는 손계산·분모·불변성·schema 오류를 검증할 뿐 지표의 구성/내용/준거 타당성을 검증하지 않는다. 다음을 pilot 이후 별도 실험으로 수행해야 한다.

### 9.1 독립 전문가 품질 순위

1. source/unit gold를 독립적으로 확인한 전문가가 agent의 B/R/N 출력과 취득 trace를 검토한다. 지표 이름/값·모델 이름을 가리고, 자신의 출제 문항은 유일한 judge로 맡기지 않는다.
2. 적어도 두 명이 case별 여러 시스템 출력을 순위 또는 pairwise 선호로 평가하고, 불일치는 제3자가 조정한다. **조정 전 agreement**를 남긴다.
3. rubric은 잘못된 합침/분리, 원문 조건 추적, 실제 취득한 근거, 반복에 대한 과잉 반응, 새 unit 누락, 정보 부족에 대한 유보를 각각 평가한다. 결론의 semantic correctness는 별도 항목으로 둔다.
4. GLRS/component(C/A 포함), ordinary B-cubed, count delta, citation precision/recall, dedup/RARE류 기준, CUE-R류 intervention diagnostics가 사람 순위와 얼마나 맞는지 Spearman/Kendall·pairwise agreement·family-cluster CI로 비교한다. 모델·질문 언어·원문 언어 profile·분야 strata와 동점률도 보고한다. 같은 원문의 KO/EN 질문 비교와 서로 다른 원문의 EN/KO 관측 비교를 구별하고 후자를 언어의 인과 효과로 해석하지 않는다.
5. evaluator gold의 오류와 metric의 오류를 구분한다. 사람이 인정한 alternate evidence subset을 GLRS가 부당하게 낮추는 사례, unknown-heavy 사례를 반드시 별도 분석한다.

40 pilot base group으로 rubric·동점·비용을 점검하고, 사람이 검토 가능한 출력 수와 사전 최소효과/검정력에 따라 별도의 held-out meta-eval family 수를 정한다. pilot의 상관이 유리하다는 이유로 40개를 확정 검증으로 포장하지 않는다.

### 9.2 오류 challenge와 ablation

사전 작성한 challenge에는 perfect, always-merge, always-separate, repeat overcount, no-new response, 틀린 문서지만 맞는 count, unopened citation, 효율적인 unit 대표 인용, partially correct grouping, 정당한 alternate source, unknown에 대한 과확신, 최종 결론만 틀린 경우를 포함한다. 합성 challenge와 실제 agent output을 구분하고 새로운 독립 실제 사례 수에 합산하지 않는다.

min G 대 mean G, C의 hard certificate 대 사전 정한 soft 보조 변형, A/claimed-delta의 기여, product 대 사전 정한 soft 결합, document 대 unit macro weighting, eligible anchor 정의와 alternate-evidence-set 처리의 ablation을 dev에서 비교한다. 특히 C의 strict certificate와 단일 unit 추가 시 I/S/A gate 때문에 GLRS가 모두 0이 되는 비율과 사람이 유용하다고 보는 partial improvement를 놓치는 비율을 보고한다. 덜 보수적인 변형을 나중에 선택하면 새 version과 변경 이유를 기록하고 잠근 test의 과거 점수를 그대로 비교하지 않는다.

지표가 사람 순위와 맞지 않거나 단순 지표보다 이점이 없으면 그 결과를 공개하고 GLRS를 보조 진단 또는 폐기 후보로 낮춘다. **지표를 구현하고 unit test를 통과했다는 사실만으로 새로운 과학적 지표가 검증됐다고 쓰지 않는다.**

## 10. CPU로 재현하는 명령과 현재 검증 범위

저장소의 `evaluation` 디렉터리에서 실행한다. 모델·GPU·네트워크·유료 API 호출은 없다. 외부 baseline이나 사람이 읽을 실제 corpus를 내려받는 명령도 아니다.

```bash
.venv/bin/python -m pytest tests/test_lineage_metric.py -q
.venv/bin/python -m linkpaper_eval.lineage_metric \
  --input fixtures/lineage_metric/synthetic_triplets.json \
  --output fixtures/lineage_metric/demo_scores.json \
  --bootstrap-samples 1000 --seed 0
```

검증 항목은 adequate duplicate witness 선택/같은 cluster의 반복 witness 불변성, 중복 unit 분리 감점, 서로 다른 unit 합침의 인증 실패, background 인용과 unit 주장 구분, unsupported claimed cluster 분모 보존, unsupported fake-count/OLD-unit 재취득 gaming 차단(C/A), coherent partial coverage, perfect=1, constant merge/separate=0, repeat overcount와 new 무반응 감점, cluster/gold unit 이름 불변성, 실제 열지 않은/누락/실패 응답의 0 및 분모 보존, wrong/ineligible 인용·누락 손계산, unknown gold coverage, control 불일치 오류, group/family macro, CLI roundtrip다. 이들은 보고 숫자가 잘못되어 연구 결론이 바뀌는 오류를 방지하기 위한 계산 검증이다.

실제 agent integration은 `evaluation/src/linkpaper_eval/agent_lineage.py`가 원래 episode/trace/private gold registry를 검증해 이 schema로 변환한다. 실제 읽은 근거는 frozen tool replay로 확인하며, source paper 수와 record 수, record별 원문 언어 빈도, paper별 언어 profile 빈도도 대조한다. 실제 과학 자료의 unit·eligible witness와 사람 타당성 검증은 추가로 필요하다. 합성 end-to-end smoke는 실제 model/science benchmark의 검증을 대체하지 않는다. 이 scorer는 CPU 전용이며 GPU 의존성이 없다. GPU 모델 실행은 [GPU 매뉴얼](GPU_EXECUTION_KO.md)의 할당 장치 설정을 따른다.
