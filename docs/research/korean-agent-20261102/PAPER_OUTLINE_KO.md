# 논문 구성 초안

가제: **한국어 학술 에이전트는 인용 수와 실험 근거 수를 구별하는가?**

영문 working title: *Tracing Results, Not Counting Citations: Evaluating Provenance Reasoning in Korean Scholarly Agents*. 확정 제목이나 성능 결론이 아니다. 여기서 Korean은 주 질문 언어를 가리키며 원문은 영어 다수·한국어 포함이고, 논문 주제는 AI에 한정하지 않는다.

저자 계획: 김수용 1저자. 정상헌·남두현·오창원·이상민의 순위는 미정이다. 아래는 연구 수행을 위한 초안이며 실제 기여·동의에 따라 최종 저자와 기여문을 확인한다.

## 초록을 쓰기 위한 골격

학술 agent가 여러 문헌을 인용하더라도 그 인용이 몇 개의 원 실험 결과에 근거하는지는 별도 문제다. 본 연구는 영어 논문을 더 많이 포함하고 한국어 논문도 포함한 원천 코퍼스에서 결과의 재보고와 새 실험·분석을 구분하는 전문가 주석 자료와 제한된 도구 탐색 환경을 제안한다. record 수·paper 수·원문 언어 구성과 표현 유사도를 통제한 묶음, 같은 원문을 사용하는 한국어/영어 질문 대조, 실제로 획득한 출처에 연결한 GLRS 후보 지표로 이 능력을 평가한다. **[실제 데이터 수·검수 일치·모델 결과·효과 크기는 측정 후 기입]**. 결과가 뒷받침하는 범위에서 기존 답변/인용 점수의 한계를 설명한다.

대괄호 부분을 예상 숫자로 채우지 않는다. 본문과 표도 실제 run ID·data version·source hash에 연결한다.

## 1. Introduction

한국어 연구자의 실제 원천 탐색 사례로 문제를 보이되, 유명 선행연구 사례를 새 발견처럼 재사용하지 않는다. 문서 중복, 인용 정확성, 결과 계보의 차이를 정의한다. 기여는 검수된 새 자료·측정 타당성·실증 결과 중 완료된 항목에만 둔다.

## 2. Related Work

영어 학술 corpus를 다루는 scholarly retrieval/SciNet·ScholarGym·AgentHop, 한국어 agent/K-BrowseComp, 과학 validity/SciValidityBench, 인용 및 중복/Greenberg·CONFPROP·CUE-R·RARE, 과학 lineage/IdeaGene 순으로 비교한다. [충돌표](RELATED_WORK_KO.md)의 더 가까운 연구를 빠뜨리지 않는다.

## 3. Task and Data

bounded corpus, 결과 unit/버전/분석/데이터 재사용/unknown의 운영 정의, 질문 수집과 제외, 원문 권리·hash·span, 독립 주석, 조정 전 일치, 대체 충분 근거, 영어 다수·한국어 포함 원문 구성(중복 버전을 합친 source-paper family 분모), 별도의 KO/EN 질문 의미 대조 검수, source-family split을 설명한다. 자연 과제와 구성한 통제 묶음의 통계를 나눈다.

## 4. Evaluation Protocol and Metric

agent public/private 경계, 도구 접근·예산·격리, 실패 분모, 실제 읽은 인용 규칙, 표준 지표, GLRS 식과 component, unknown coverage를 제시한다. 후보 지표의 공리 테스트와 사람이 매긴 평가 순위의 관계를 따로 보인다.

## 5. Experimental Setup

동일 backbone의 단발 RAG/반복 도구/graph/계보 baseline, 모델 계열별 반복, 동일 총 예산의 multi-agent, oracle 상한, 형식·query language·parse oracle ablation을 사전 등록한다. model snapshot, parser/embedding/reranker/code commit, seed와 비용을 기록한다.

## 6. Results

실행 전에는 결과 절을 빈 가설 표로 둔다. 실행 후 main 표는 실패 포함 평균과 family-cluster CI, 각 stage 지표, 동일 원문 KO/EN 질문 paired gap, EN-only/KO-only/mixed source strata의 관측 분석, 자연/통제/unknown strata를 포함한다. 기존 citation 점수와 GLRS가 다른 시스템 순위를 만드는 사례를 전문가 검토와 연결한다. 통계적으로 불확실한 차이를 순위 우열로 단정하지 않는다.

## 7. Analysis and Metric Validation

표현이 다른 재보고/표현이 유사한 새 결과, oracle-read 대비 실제 탐색, 그래프 출처와 의사결정, shortcut agent, 근거 몰아 인용하기, 항상 유보하기, cluster 무조건 합치기/나누기를 분석한다. 정성 예시는 사전에 정한 층화 표본과 실패 사례에서 고르고 성공만 전시하지 않는다.

## 8. Limitations and Ethics

영어 논문 다수 구성과 실제 확보한 AI·비AI 분야의 제한된 coverage, venue 선택 편향과 source 언어/질문 언어 효과의 구별, 원문 접근 편향, 불완전한 provenance와 unknown, 표/그림 제외 비율, 통계 독립성과 결과 단위의 차이, 주석자의 전문성, 모델 학습 오염의 불확실성, 공개/holdout 관리, 원문 권리와 인간 작업 시간을 명시한다.

## 부록·공개 artifact

전체 schema와 도구 spec, annotation manual/IAA, split graph audit, 제외 사유, budget/cost logs, 모든 모델·실패 run, GLRS 반례 battery, baseline commands, license/provenance ledger를 제공한다. 내부 저자명·공개 GitHub 링크는 익명 심사본의 허용 범위에 맞춰 처리하고, 실제 저장소의 원 기여자 고지는 유지한다.
