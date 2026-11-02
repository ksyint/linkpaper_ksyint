# LinkPaper 한국어 연구 에이전트 벤치마크: 선행연구 검토와 연구 질문

조사일: 2026-11-02. 이 문서는 연구 설계 제안이며, 모델 실험 결과·학회 채택·세계 최초라는 사실을 주장하지 않는다. 논문 원문, 저자 저장소, 공식 학회·데이터 카드에서 확인한 내용과 아래의 제안을 구분한다. 웹 전체를 완전히 조사했다는 뜻은 아니다. 가까운 연구를 찾는 방향으로 검색했고, 특히 2026년 9–10월의 새 연구를 기존 제안과 비교했다.

## 1. 먼저 바꿔야 하는 주장

기존 포크의 `research/neurips-2027-benchmark-proposal` 브랜치에는 LINK-DELTA라는 조건 적합성·근거 삭제 후 결론 수정 제안이 이미 있다. 이를 새 기여라고 다시 내세우기 전에, 후속 선행연구와 겹치는 부분을 갱신해야 한다. [기존 제안](https://github.com/ksyint/linkpaper_ksyint/blob/research/neurips-2027-benchmark-proposal/docs/research/neurips-2027/PROPOSAL_KO.md)

한국어, 인용 그래프, 멀티홉, 도구 sandbox, frozen search, evidence checklist, counterfactual pair, validity ledger는 각각 이미 연구된 요소다. 특히 **SciValidityBench(2026-10-26)**는 과학적 증거의 사용 적격성, 실행 가능한 과제 생성, 반사실 쌍, 손상·복구 진단까지 제공한다. 일반적인 “과학 근거가 현재 결론을 정당화하는가”를 처음 측정한다는 주장은 피해야 한다. [논문](https://arxiv.org/abs/2610.34767), [본문](https://arxiv.org/html/2610.34767v1)

인용 수가 독립적인 증거 수와 같지 않다는 문제 역시 새 발견이 아니다. Greenberg는 2009년에 과학 인용망에서 새 데이터를 제공하지 않는 논문들이 주장의 권위를 증폭하는 과정을 분석했다. 최근 CONFPROP 연구도 공통 상위 출처와 복제 연쇄를 가진 증거를 독립적으로 합산하는 문제를 직접 다룬다. [Greenberg](https://doi.org/10.1136/bmj.b2680), [CONFPROP](https://doi.org/10.1007/s44163-026-02245-5)

사용자 요청으로 핵심 과제는 **필요한 논문 수를 알리지 않은 상태에서 하나 또는 여러 논문의 여러 근거를 연결해 정답을 찾는 것**으로 확장했다. 결과 원천·재보고 판별은 하위 과제 하나로 둔다. 영어 다수·한국어 포함 다분야 자료의 실제 정보 요구, 대안 충분근거, 조건·정량·상충·종료 실패 분석을 기여 후보로 검증한다. 넓은 학술 QA·멀티홉·source 수 비공개 자체는 이미 있는 연구 설정과 겹치므로 최초라고 하지 않는다. 특히 ScholarGym·ScholarQABench·PaperArena·AgentHop·SciNet과 더 직접적으로 비교해야 한다.

## 2. 중심 연구 질문과 하위 과제

> 한국어 질문을 받은 학술 agent는 필요한 논문 수를 미리 알려주지 않아도 한 논문 내부 또는 여러 논문에 분산된 근거를 찾아 연결하고, 조건에 맞는 답·인용을 제시하며 탐색을 적절히 종료할 수 있는가?

하위 과제는 논문 내부 복합 근거, 논문 사이 연결, 조건 비교, 정량 추론, 상충/정보 부족, 결과 원천의 6종이다. 태그는 private primary/secondary 분류이며 실제 능력이 서로 배타적이라고 가정하지 않는다. 알려진 충분근거 조합의 paper 수는 비공개 분석 metadata다. 가장 짧은 검수 대안이 전역 최소를 증명하지 않으며 미발견 대안과 unknown을 인정한다. 한 논문 대안과 여러 논문 대안이 모두 타당하면 둘 다 허용한다. 질문·ID·도구 응답에 정답 source 수를 넣지 않는다.

저장 archive의 offline, 같은 Policy.step이 한 episode에서 search_papers/fetch_paper/search_local/open과 답변을 교차하는 live interleaved, hash-bound 관측을 네트워크·parser 없이 재구성하는 frozen replay를 구분한다. staged acquire-then-answer는 별도 대조다. 현재 기본 외부 provider는 arXiv이고 전체 웹·GUI·한국 발행처 live 지원이나 기존 Neo4j/Qdrant production API 완성을 주장하지 않는다. source coverage·비용·실패·권리·정답 mapping을 사람이 확인해야 하며, live 구조 진단/semantic null과 별도 응답 review를 구분한다. [원 저장소](https://github.com/linkmind-ai/linkpaper)

아래 2.1–2.2는 **결과 원천 하위 과제**의 기존 운영 정의다. 전체 benchmark의 주 목적이나 모든 질문의 필수 답 형식으로 사용하지 않는다.

### 2.1 무엇을 세는가

`paper_id`, `version_family_id`, `empirical_study_family_id`, `analysis_id`, `evidence_span`을 구분한다. 한 연구가 preprint와 출판본 두 개로 발표되거나 여러 review에서 소개되어도 1차 데이터 수집 단위가 자동으로 늘어나지 않는다. 반대로 서로 다른 연구가 비슷한 문장을 사용했다고 같은 실험이 되는 것도 아니다.

- **논문 단위:** 출판물의 수. DOI가 다르다는 사실만으로 실험 독립성이 보장되지 않는다.
- **버전 단위:** 동일 논문의 preprint·학회·저널 확장판 관계. 버전 판정과 실험 판정은 다르다.
- **실증 연구 단위:** 대상·수집 절차·데이터 식별자·실험 설정을 근거로 주석한 단위. 한 논문이 여러 단위를 담을 수 있다.
- **분석 단위:** 같은 데이터에 다른 분석을 수행한 경우. 새로운 분석의 가치를 부정하지 않되 독립적인 데이터 수집과 구별한다.
- **계보 불명:** 공개 본문만으로 관계를 판정할 수 없는 경우. 이를 “독립”으로 채우지 않는다.

저자 중복이나 인용 연결만으로 `same study`를 판정하지 않는다. 서로 다른 저자도 같은 데이터에 의존할 수 있고, 같은 저자도 별도 실험을 수행할 수 있다. `cites`와 `reuses_data`, `reports_same_experiment`, `summarizes`, `extends` 같은 관계는 별도로 주석해야 한다.

이 하위 track의 채점 대상은 **명시적으로 정의한 실험·결과 단위의 비중복성**이다. 이것을 통계적 독립성이나 인과적 독립성으로 부르지 않는다. 데이터 수집의 공유 여부는 별도 속성으로 기록한다. 표준 공개 데이터셋을 이용한 ML 비교에서는 “새 연구”와 “새 데이터”를 따로 기록하고, 어떤 기준을 채점하는지 문제에 명시한다.

### 2.2 결과 원천 하위 과제와 단순 중복 제거의 차이

핵심 대조는 다음 네 경우다. 문서 수와 길이를 가능한 범위에서 맞추고, 배치 순서를 교차한다.

| 경우 | 텍스트 유사성 | 1차 실증 계보 | 바람직한 판정 |
|---|---|---|---|
| 동일 연구의 직역·재인용 | 높음 | 같은 단위 | 새 실증 근거로 중복 계산하지 않음 |
| 동일 연구를 서로 다른 표현으로 소개한 review들 | 낮음 | 같은 단위 | 표현이 달라도 중복 계산하지 않음 |
| 별도로 수집된 연구들의 유사한 결과 보고 | 높을 수 있음 | 분리된 단위 | 문장 중복만으로 합치지 않음 |
| 관계를 확인할 정보가 부족한 보고 | 임의 | 불명 | 독립성을 단정하지 않음 |

이를 충분히 확보하지 못하면 원천 하위 track은 일반적인 RAG 중복 제거 실험으로 설명될 수 있다. 그 경우 이 하위 기여의 “새 계보 이해 능력” 주장을 낮추며, 전체 과제의 다른 발견과 구분한다.

## 3. 중복 위험이 큰 선행연구 지도

아래 표는 각 연구가 이미 무엇을 측정하는지와 이번 후보 질문의 경계를 정리한다. “차이 후보”는 그 논문에 해당 기능이 전혀 없다는 보편적 부정이 아니다. 후속 버전과 부록도 제출 전에 다시 대조한다.

| 연구·최초 공개/확인 상태 | 이미 제공하는 것 | 이번 연구의 차이 후보와 충돌 위험 |
|---|---|---|
| [K-BrowseComp](https://arxiv.org/abs/2606.02404), 2026-06-01 | 한국 맥락 400문항, 사람 검증 300 + 합성 진단 100. 멀티홉·병렬 제약, 예상 경로와 중간 증거 checklist. | 한국어·다중 근거·경로 진단·source 수 비공개만으로 차별화하지 않는다. 실제 학술 자료의 조건·충분근거·종료 실패 분석과 원천 하위 과제의 추가 식별력을 검증한다. 매우 높음. |
| [AgentHop](https://arxiv.org/abs/2609.34428), 2026-09-28 | 1,011개 과학 MCQ, 7개 도구, 예산 제한. 검색·합성·도구·자원 진단. [공식 데이터 카드](https://huggingface.co/datasets/nlpai-lab/agenthop) | seed paper의 인용망 탐색·과학 멀티홉·실패 분해와 직접 겹친다. 한 논문/여러 논문 대안, 조건·계산·종료 진단과 원천 subset의 추가 가치를 검증해야 한다. 매우 높음. |
| [IdeaGene-Bench](https://arxiv.org/abs/2607.08758), 2026-07-09 preprint | 아이디어의 상속·변형·재조합 계보와 새 아이디어 생성 평가. [공식 코드](https://github.com/VisionXLab/IdeasHaveGenomes) | “과학 계보 추론 최초”는 주장할 수 없다. 아이디어 상속과 실험 결과 재보고 계보를 구분하고, 후자를 실제로 새롭게 측정하는지 검증한다. 매우 높음. |
| [SciNet](https://proceedings.mlr.press/v306/shao26h.html), ICML 2026 main | 논문 관계를 ego/pair/path 수준에서 검색하는 8,940과제. 상충 연구·기술 계보 등. | 인용 관계·연구 흐름 탐색 자체로 새롭지 않다. 주 과제의 연결·충분성 분석을 직접 비교하고 원천 subset에서는 bibliographic/empirical lineage를 구분한다. 매우 높음. |
| [SciValidityBench](https://arxiv.org/abs/2610.34767), 2026-10-26 preprint | 64 TaskSpec, 다섯 validity 모듈과 여섯 과학 영역. 결정의 유효성, 쌍 조건과 손상·복구. | 일반 조건 적합성·과학 상태 ledger·counterfactual은 선행연구로 인정한다. 실제 영어·한국어 문헌의 reported-result 계보 감사와 취득 trace가 별도 측정 대상을 만드는지 검증한다. 원문 언어 변경만으로 차별화하지 않는다. 매우 높음. |
| [SciConBench](https://arxiv.org/abs/2606.11337), 2026-06-09 | 체계적 문헌고찰 기반 9.11K 질문·결론, clean-room 도구, 원자 사실 precision/recall. | 과학 결론 종합·상충 근거 해소·답안 누출 차단은 기존이다. 전문 임상 결론의 진위를 새로 판정하는 범위까지 확대하지 않는다. 높음. |
| [ScholarGym](https://arxiv.org/abs/2601.21654), 2026-01-29 | 570K 논문, 2,536 전문가 주석 질의, 결정적 검색, 계획·도구·관련성 분해. | frozen academic tool environment 자체는 새 기여가 아니다. 매우 높음. |
| [PaperArena](https://arxiv.org/abs/2510.10909), 2025-10-13 | 여러 논문의 다양한 형식을 통합하고 parsing·retrieval·computation 도구로 답하는 플랫폼. | 학술 도구 orchestration·cross-paper QA 자체는 새롭지 않다. 매우 높음. |
| [AstaBench](https://arxiv.org/abs/2510.21652), 2025-10-24, ICLR 2026 | 2,400+ 과학 과제, 재현 가능한 검색 도구, 비용·도구 접근 통제, 여러 agent class. | 공정한 도구·예산 통제와 과학 agent suite는 선행 방법이다. 넓은 전주기 벤치마크를 새로 만드는 방향은 피한다. 높음. |
| [ScholarQABench/OpenScholar](https://doi.org/10.1038/s41586-025-10072-4), 논문·공식 코드 확인 | 분야별 문헌 종합과 인용 평가. [공식 저장소](https://github.com/AkariAsai/ScholarQABench) | 학술 답변 종합과 인용 품질을 이미 다루므로 확장된 주 과제의 가까운 비교 대상이다. 충분근거·조건·탐색 종료와 원천 subset의 추가 발견을 검증한다. 높음. |
| [ScholarBench](https://arxiv.org/abs/2505.16566), 2025-05-22 / EMNLP Findings 2025 | 한국어 5,031·영어 5,309 academic reasoning 사례. | “한국어 과학 문제” 자체도 차별점이 아니다. 도구 탐색·근거 연결·충분성의 추가 실증을 검증한다. 높음. |
| [BrowseComp](https://arxiv.org/abs/2504.12516), 2025-04-16 | 찾기 어려운 웹 정보에 대한 1,266개 짧고 검증 가능한 답. | 장시간 검색 난도만 늘리는 설계는 배제한다. |
| [BrowseComp-Plus](https://arxiv.org/abs/2508.06600), 2025-08-08; 공식 저장소 ACL 2026 main 표기 | 고정 corpus, 사람이 확인한 지지 문서, retriever와 agent 분리 실험. [코드](https://github.com/texttron/BrowseComp-Plus) | 고정 검색·인용 정확도·retrieval 분리 자체는 이미 있다. 높음. |
| [LitSearch](https://arxiv.org/abs/2407.18940), 2024-07-10 / EMNLP 2024 | 597개 현실적인 논문 검색 질의, 전문가 확인. | 논문 검색 성능 비교에 해당하면 기존 benchmark를 보조로 사용하면 된다. |
| [Researchy Questions](https://arxiv.org/abs/2402.17896), 2024-02-27 | 약 100K 복합·다관점 검색 질의와 클릭 URL. | 복합적 research question 수집이라는 방향 자체는 기존이다. |
| [DeepResearchGym](https://arxiv.org/abs/2505.19253), 2025-05-25 | 재현 가능한 public-web corpus 검색과 보고서 평가. | live API의 비결정성을 없앤다는 논리는 기존이다. |
| [DeepResearch Bench — Du 등](https://arxiv.org/abs/2506.11763), 2025-06-13 | 22분야·100 전문가 과제, RACE 보고서 품질과 FACT 인용 평가. [코드](https://github.com/Ayanami0730/deep_research_bench) | 인용 개수/정확도 점수가 독립 연구 수를 직접 측정하는지는 별도 실험으로 확인한다. judge 버전이 바뀌므로 고정해야 한다. |
| [Deep Research Bench — FutureSearch](https://arxiv.org/abs/2506.06287), 원문 이력 2025-05-06 | 원문 89개 과제와 frozen RetroSearch, trace 진단. | 위의 100과제 벤치마크와 다른 연구다. 이름을 혼동해서 통계·평가 코드를 섞지 않는다. |
| [GAIA](https://arxiv.org/abs/2311.12983), 2023-11-21 / ICLR 2024 | 466개 도구·웹·멀티모달 assistant 문제. | 일반 agent robustness가 기존 연구 대상임을 설명하는 배경이다. |
| [WebArena](https://github.com/web-arena-x/webarena), ICLR 2024; [WorkArena](https://arxiv.org/abs/2403.07718), 2024-03-12; [BrowserGym](https://github.com/ServiceNow/BrowserGym) | 실행 가능한 환경, 관측·행동 interface와 작업 완료 평가. | 상태 변화나 action trace라는 표현만으로 새롭지 않다. LinkPaper API agent와 GUI agent 성능은 별도 트랙으로 둔다. |
| [PaperBench](https://arxiv.org/abs/2504.01848), 2025-04 | 20개 ICML 논문 재현, 8,316 rubric leaf, 실행과 judge 검증. | 논문 재현은 다른 연구 질문이다. 여기에 실험 재현까지 추가하면 범위와 annotation 비용이 과도해진다. |
| [ALCE](https://arxiv.org/abs/2305.14627), 2023-05-24 / EMNLP 2023 | 사실성·유창성·인용 품질을 분리한 평가. | 인용 지원 평가는 이미 확립된 축이다. 계보 측정과 상관·불일치를 분석하는 보조 지표로 둔다. |
| [FORCEBENCH](https://arxiv.org/abs/2605.28044), 2026-05-27 | 같은 인용문에 비례한 주장과 과도한 주장을 대조, 시간·범위 등 다섯 force축. | “인용은 있는데 주장이 과도하다”는 발견을 새롭다고 쓰지 않는다. 단일 passage의 warrant와 연구들 사이의 데이터 계보를 구분한다. 높음. |
| [CUE-R](https://arxiv.org/abs/2604.05467), 2026-04-07 | REMOVE/REPLACE/DUPLICATE와 정확도·grounding·confidence·trace 진단. | 문서 복제 후 점수 변화만 보면 기존 intervention 평가와 충돌한다. 높음. |
| [RARE](https://aclanthology.org/2026.acl-long.923/), ACL 2026 main | 원자 사실 단위 중복을 추적하는 검색 평가. | 텍스트 중복과 실증 계보의 차이를 실험으로 보여야 한다. 높음. |
| [Ross 등](https://arxiv.org/abs/2608.13956), 2026-08-14 | duplicate/paraphrase/diverse 문서를 통제한 RAG 실험. | 단순 paraphrase 반복은 기존 대조다. 새로운 데이터 수집 단위의 추가와 분리한다. 높음. |
| [One Fact, Many Places](https://arxiv.org/abs/2610.26401), 2026-10-19 | 같은 사실의 여러 위치·양식을 주석해 single-gold 인용과 masking 평가의 오류 분석. | 유효한 대체 citation을 오답 처리하지 않아야 한다. 지지 위치가 여러 곳인 것과 실증 연구가 여러 개인 것은 다르다. 높음. |
| [CONFPROP](https://doi.org/10.1007/s44163-026-02245-5), 2026-10-24 | 공통 출처·복제 연쇄의 synthetic scenario, FEVER 사례, 의존성 할인과 confidence 집계. | 독립성 할인 원리나 합성 공통부모 그래프를 발명했다고 할 수 없다. 실제 학술 연구 계보와 agent의 정보 취득을 검증하는 차이가 필요하다. 매우 높음. |
| [Greenberg](https://doi.org/10.1136/bmj.b2680), 2009-07-21 | 과학 인용망의 amplification·invention으로 권위가 만들어지는 현상 분석. | 문제 정의의 필수 선행연구다. 같은 유명 사례나 표·문제 구조를 가져와 새 데이터처럼 발표하지 않는다. |

KoTAU는 로컬 main과 별도 label proposal에서 여행용 offline tool·DB 사본·관측/private 정보 분리·최종 상태/경로 제안을 확인했다. 공개 웹 조회 실패로 프로젝트나 평가 설계의 부재를 단정하지 않는다. main의 미합의 채점 상태와 proposal을 구분하고, 그 성숙도 차이를 우리 신규성으로 삼지 않는다. [버전·파일 감사](audits/local/LOCAL_BENCHMARK_AUDIT_KO.md)를 따른다.

## 4. 주장할 수 있는 차이와 주장하면 안 되는 차이

가능한 기여 후보는 다음을 **실제 자료와 실험으로 검증했을 때** 주장한다.

1. 영어 다수·한국어 포함 다분야의 실제 질문과 한 논문 내부/교차 논문 근거·조건·정량·상충·대안 충분근거의 새 주석 자료.
2. 정답 source 수를 알리지 않은 공통 탐색 환경에서 발견·연결·조건 적용·종료를 분리한 실증 분석. source 수 비공개 그 자체를 최초라 부르지 않는다.
3. offline archive·live interleaved·staged 획득 대조와 frozen replay를 구분한 비용·coverage·실패 분석. 발견/획득 도구의 구현 자체를 새로운 능력의 발명으로 포장하지 않는다.
4. 결과 원천 subset에서 텍스트 유사도와 reported-unit 관계를 교차한 통제 자료·GLRS 타당성. 이 하위 기여가 전체 task 정의를 대신하지 않는다.

아래 표현은 근거가 부족하다.

- “한국어 최초 agent benchmark”: K-BrowseComp, 한국어 도구 평가 등과 충돌한다.
- “최초 인용 그래프/과학 멀티홉 agent benchmark”: AgentHop·SciNet·PaperArena와 충돌한다.
- “최초 과학 evidence validity/counterfactual benchmark”: SciValidityBench 등과 충돌한다.
- “최초 citation laundering 발견”: Greenberg·FORCEBENCH 등과 충돌한다.
- “인용 그래프가 끊겼으므로 증거가 없다”: retrieval miss·출판 metadata 누락·대체 근거 미주석일 수 있다.
- “다른 DOI/기관/저자이므로 독립적이다”: 실증적 계보 확인 없이 선언할 수 없다.
- “모델 확신도를 낮췄으므로 더 과학적으로 정확하다”: 적절한 확률 모형과 검증 자료가 없으면 confidence의 정답을 임의로 만들게 된다.

## 5. 실행 가능한 평가 설계

### 5.1 과제의 출력과 gold

단답·수치·설명·판정 등 질문에 맞는 답 형식과 rubric을 검수한다. 명제가 분명한 판정 과제에만 `supported/refuted/mixed/insufficient`를 적용하고, 다른 답 형식을 일괄 supported로 바꾸지 않는다. 각 claim의 조건·원문 근거·계산식·대안 충분근거를 기록한다. 모범 문자열 일치는 의미 정확성 인증이 아니다.

private gold에는 알려진 충분근거 조합과 `known_alternative_paper_counts`·`known_alternative_evidence_counts`를 두되 `global_minimum_certified=false`를 기본으로 한다. 검수한 대안의 최솟값이 전역 최적의 증명이 아니다. 한 논문으로 충분한 대안과 여러 논문 대안이 함께 있으면 둘 다 인정한다. 필요한 paper 수·task tag·정답 source/경로를 agent에게 주지 않는다.

결과 원천 과제에서만 unit grouping·재사용·unknown을 추가한다. 원문으로 관계를 판정할 수 없는 사례는 확인 불가로 남긴다. agent가 숨겨진 unit ID를 출력하게 하지 않고 공개 record ID로 답하게 한다. oracle 조건은 특권 정보의 범위를 명시해 main과 분리한다.

### 5.2 권장 조건 행렬

| 축 | 조건 | 분리하려는 설명 |
|---|---|---|
| 정보 처리 | closed-book / flat RAG / iterative retrieval agent / graph-enabled agent | parametric prior, 검색 이득, 순차 탐색, 그래프 접근을 분리 |
| 실행/수집 모드 | offline archive / live interleaved / staged 획득 대조 / frozen replay | 발견·파싱·읽기·종료의 이득/실패/비용과 관측 재현을 분리. arXiv provider 범위 명시 |
| source 범위 | 요구 논문 수 미제공 / 검수 대안 범위 oracle | 숨겨진 범위에서의 탐색·종료와 특권 힌트의 효과. oracle이 전역 최소를 안다고 하지 않음 |
| task | 내부 연결 / 교차 논문 / 조건 비교 / 정량 / 상충·부족 / 원천 | private primary+secondary 층화. 중복 태그를 독립 N에 더하지 않음 |
| 계보 정보 — 원천 subset | 본문·기본 인용 / bibliographic graph / 사람이 검증한 계보 oracle | 그래프 존재와 올바른 계보 이해를 분리 |
| 문서 집합 — 원천 subset | 실증 단위 유지하며 secondary report 증가 / 실제 별도 1차 실험 추가 | 문서 수와 실증 수 분리 |
| 표면 형태 — 원천 subset | exact copy / 낮은 유사도 paraphrase·review / 유사한 표현의 별도 실험 | 텍스트 dedup shortcut 점검 |
| 질문 언어 | 같은 영어·한국어·혼합 원문 bundle에 한국어 질문 / 의미 대응 영어 질문 | source를 고정하고 질문 언어 대조 |
| 원문 언어 | 영어 다수의 corpus 내 EN-only / KO-only / mixed bundle strata | 분야·venue·시기·내용 차이가 섞인 관측 분석. 언어의 인과 효과를 주장하지 않음 |
| 예산 | 동일 tool call cap + 기록된 input/output token·시간·비용 | 더 많은 compute를 능력 향상으로 오해하지 않음 |
| 난도 | 검수한 대안 paper/record 수·근거 연결 단계·archive 크기·조건/계산·미상 관계 | 모두 private 분석용. 정답 source 수와 후보 corpus 크기를 구분 |

모든 모델에 같은 검색 corpus·ranking cache·tool schema·문서 순서 seed를 제공한다. 한 모델의 검색 결과를 다른 모델에게만 주는 비교는 피한다. 여러 agent scaffold를 사용할 경우 backbone을 고정한 비교와 scaffold를 고정한 비교를 각각 둔다. GUI 사용 능력을 핵심 가설과 섞지 말고 API 도구 agent를 1차 실험으로 둔다.

### 5.3 필수 baseline

- closed-book·항상 유보·고정 depth 종료 대조: 사전지식·형식 shortcut·종료의 하한선.
- citation/document 개수만 세는 규칙 baseline: 원천 하위 과제의 shortcut 하한선.
- DOI·제목·버전 exact dedup: 단순 서지 중복이 해결하는 부분.
- 텍스트 near-duplicate/embedding clustering: 표현 중복이 해결하는 부분.
- 인용 공통 조상 또는 source-discounted heuristic: 구조만 이용하는 baseline. 실제 연구 재사용 관계와 같다고 가정하지 않는다.
- BM25/dense flat RAG + 같은 generator.
- 같은 generator의 iterative search, citation-graph search.
- 충분근거 oracle-read와 검수 source 범위 oracle: 발견·연결·종료의 병목을 분리하고 특권 정보의 범위를 기록.
- 사람이 확인한 study lineage를 제공한 oracle: 원천 subset의 진단이며 main 순위에 합치지 않음.
- full evidence를 읽는 전문가 upper bound와 초급 연구자 baseline: 인간에게도 모호한 task를 구별.

CONFPROP를 구현·이식한다면 원 구현과 라이선스를 먼저 확인하고 attribution과 차이를 명시한다. 이 문서는 해당 코드 복제를 권하지 않으며, 독립적으로 명세한 source-discounted baseline만으로도 첫 실험을 시작할 수 있다.

### 5.4 측정 항목

전체 benchmark는 실패 포함 답 형식별 정확성/의미 품질, 인용 지원·조건 일치, 충분근거 연결, 미확인·유보·종료 행동, token/시간/실비를 보고한다. private primary task별 분포와 검수한 대안 source 범위를 함께 분석한다. 조건을 무시한 숫자 결합이나 답을 맞히고도 필요한 근거를 잘못 연결한 경우를 분리한다.

적은 논문만 읽을수록 무조건 좋은 점수나 모든 대안 source를 읽어야 하는 recall을 primary로 두지 않는다. 새로운 타당한 대안을 발견하면 blind 원문 검토·수정·재채점 규칙을 적용한다. 알려진 최소와 전역 최소를 혼동하지 않는다. 정답 source 수 비공개·adaptive stop·근거 연결 측정 자체도 기존 연구와 비교해 타당성을 검증한다.

[GLRS](METRICS_KO.md)는 **결과 원천 하위 track의 후보 지표**다. B/R/N의 취득·그룹 정합성과 재보고 불변성·새 unit 반응에만 사용하며 전체 task의 primary로 평균하지 않는다. 새 unit이 생겨도 최종 verdict가 반드시 바뀌지 않는다. unknown 계보의 coverage와 metric 0점·동점률·대안 witness 감점 여부를 보고한다. DOI/text dedup·일반 graph와 사람 meta-eval을 통과하기 전 새 지표의 타당성을 확정하지 않는다.

live interleaved는 한 episode 안의 발견·fetch·로컬 검색·열람·종료 순서와 검색/fetch/parse 실패·매칭 불가·cold/warm cache·coverage·비용을 기록한다. 현재 live 점수는 구조 진단이며 scientific semantic accuracy는 null이다. 응답 hash에 묶인 사람 review를 별도 기록하고, source·gold·권리 매핑 전에는 정적 gold를 자동 적용하지 않는다. frozen replay는 네트워크·parser 없는 관측 재현이며 새 모델 생성이 아니다. 가상 fixture와 실제 HTTP preflight를 본 모델 성능으로 발표하지 않는다.

통계 단위는 기본 문항/source family다. 번역·재실행·통제 arm·중복 secondary tag를 새 N으로 세지 않는다. 같은 모델/도구/언어 조건의 paired 분석과 cluster CI를 사전 명세하고 모든 실패를 남긴다. 최고 성능 run만 골라 보고하지 않는다.

## 6. 어떤 데이터를 모으고 어떤 것을 사람이 라벨해야 하는가

### 6.1 반드시 남길 원본 provenance

각 문헌의 URL/DOI, 버전, 접근일, 원문 hash, 언어, 공개 라이선스, 사용 허용 범위, section/page/표 식별자를 남긴다. 문제·번역·태그·label도 작성자와 검수 이력을 분리한다. 기존 benchmark 문제나 예상 경로를 seed로 삼지 않는다.

공개 metadata의 이용 조건과 PDF 본문·번역문의 재배포 조건은 다르다. 코드가 MIT/Apache여도 논문 원문까지 같은 조건으로 배포 가능한 것은 아니다. 영어·한국어 논문 모두 학회·기관 사이트에 보인다는 이유만으로 수집·재배포가 허용되었다고 간주하지 않는다. 허용 조건이 확인된 원문을 우선하고, 나머지는 URL·서지 정보·직접 작성한 annotation을 분리해 다룬다.

### 6.2 수작업이 필요한 핵심 주석

자동 DOI 정규화·해시·출판일 수집은 보조할 수 있지만 다음은 이 프로젝트의 실제 노동이다.

- 질문에 맞는 단답/수치/설명/판정 정답과 허용 alias·단위/오차·핵심 주장 rubric, 직접 근거 span.
- 한 논문 내부 또는 여러 논문의 근거 연결·충분 조합·대안, 조건/계산·source 범위의 미확인 이유. 필요한 논문 수는 private로 두고 알려진 대안 수를 전역 최소로 단정하지 않음.
- 실험/대상/평가 데이터/조건 tuple; 원천 subset에서 같은 연구의 재보고 여부.
- review의 인용이 어느 1차 결과로 연결되는지. 연결이 없거나 모호하면 불명으로 표시.
- 번역·학술 용어 alias가 qualifier와 방향을 보존하는지.
- 알려진 충분근거와 타당한 대안이 주석되었는지, 아직 놓쳤을 가능성이 있는 범위를 기록. 모든 대안을 완전히 발견했다고 임의 주장하지 않음.
- pair가 목표 정보만 바꿨는지, 문서 수·길이·어휘·검색 순서 같은 단서가 label을 누출하지 않는지.

각 base case는 서로 독립적으로 작업한 두 명이 라벨하고, 근거 span과 불일치 이유를 남긴다. 최초 작성자가 자기 문제의 최종 합의를 단독 결정하지 않는다. 분야 전문성이 부족하면 외부 전문가 검수 표본을 확보하고, 충분한 판정 근거를 만들지 못한 분야는 본 평가에서 제외한다. agreement는 adjudication 전 수치와 사후 합의 수치를 분리해 기록한다.

### 6.3 5인 저자 체계에서의 pilot 분담 예시

연구 참여자는 김수용·정상헌·남두현·오창원·이상민이다. 기존 프로젝트의 직함은 이 배분에 사용하지 않는다. 아래는 **실행 가능한 첫 40 base case pilot**의 균등 수집·교차검수 예시다.

| 출제·수집 담당 | base case | 독립 reviewer R1 / R2 | 불일치 조정자 |
|---|---:|---|---|
| 김수용 | 8 | 정상헌 / 남두현 | 오창원 |
| 정상헌 | 8 | 남두현 / 오창원 | 이상민 |
| 남두현 | 8 | 오창원 / 이상민 | 김수용 |
| 오창원 | 8 | 이상민 / 김수용 | 정상헌 |
| 이상민 | 8 | 김수용 / 정상헌 | 남두현 |

정확한 source 탐색 배분·32개씩 후보 screening·공동 산출물·독립 감사자는 [단일 운영 기준 문서](TEAM_AND_DATA_KO.md)와 [assignments.csv](collection_templates/assignments.csv)를 따른다. R1/R2는 잠정 gold와 서로의 라벨을 보지 않고 작성하고, 출제자·두 reviewer와 다른 사람이 조정한다. 다섯 사람 모두 영어 다수·한국어 포함 source pool과 실제 수작업 주석에 참여한다.

김수용이 원자료 전문 판정을 혼자 대신하지 않는다. 대규모 확장 전에 40건에서 유효 case 수·수집 탈락률·검수 시간·agreement·모델 cost를 측정한다. 40건이나 그 파생 수백 world를 최종 논문 benchmark 크기로 포장하지 않는다. 본 데이터 크기와 인력은 pilot 측정 후 조정하고, 나머지 공저자도 실험·분석·집필 기여를 맡아 학술적 기여가 수집 건수에만 묶이지 않게 한다.

## 7. 표절·오염을 줄이는 개발 절차

- 관련 연구에서 문제를 먼저 읽고 비슷하게 바꾸는 방식으로 task를 만들지 않는다. corpus의 원문 사실에서 시작해 독립적으로 질문을 작성하고, 이후 별도 검수자가 benchmark 질문 중복을 확인한다.
- 차용한 데이터·코드·그림·수식·평가 항목과 독립 작성물을 `source / license / copied files / changes / citation` 단위로 기록한다. 원래 LinkPaper MIT 파일을 발전시킬 때 저작권 고지와 기존 기여를 보존한다.
- 논문의 중심 아이디어가 선행연구와 겹치면 “기존 원리를 영어·한국어 실제 문헌과 한국어 질문에 적용한 검증”처럼 범위를 정확히 쓴다. attribution은 중요하지만 인용 하나가 독창성 증명을 대신하지는 않는다.
- task text·답·gold graph·예상 경로·adjudication note는 agent에게 제공하는 corpus/tool view와 분리한다. test split의 base family를 dev에 공유하지 않는다.
- 수집 문헌 자체에 benchmark 답안·review·프로젝트 설명이 섞였는지 검사한다. 논문 hash·DOI·근거 span·주장 embedding 등을 보조로 쓰고 사람이 false positive를 확인한다.
- 새로운 문헌·버전의 시간 holdout, 저자/연구/데이터 단위 cluster holdout을 각각 평가한다. “모델 지식 cutoff 이후 자료”만으로 오염이 없다고 단정하지 않는다.
- 완전한 표절 부재나 인터넷 전체의 독창성을 자동 보장할 수는 없다. 검색 로그·원자료 추적·코드 출처·검수 기록을 남겨 검토 가능한 주장을 한다.

## 8. 메인 학회 수준을 판단할 중단·확장 기준

메인 학회 목표의 근거는 코드 분량이나 문제 수보다 **새롭고 일반화 가능한 발견**이어야 한다. 아래 조건을 만족하지 못하면 제목을 키우기보다 먼저 연구 질문을 좁히거나 바꾼다.

1. **측정 유효성:** 전문가가 정답·조건·근거 연결·충분한 대안을 안정적으로 검수할 수 있다. 원천 subset은 동일/별도/불명 관계도 확인한다. source 범위가 미확정이면 이를 확정 라벨로 만들지 않는다.
2. **차별적 발견:** 발견·연결·조건·계산·종료 실패 분석이 기존 scholarly QA/agent 평가에 추가 설명력을 주는지 검증한다. 원천 subset의 GLRS가 추가 가치를 주지 못하면 그 기여를 낮춘다.
3. **원인 분리:** 문서 길이·source 언어 구성·검색 order·더 많은 token·질문 번역 품질·도구 차이가 효과를 설명하지 않는지 matched control로 본다.
4. **일반화:** 여러 모델 family·새 corpus family·동일 원문 KO/EN 질문 대응 조건 및 원문 언어 strata에서 결과를 확인한다. 한 모델·한 분야만의 현상은 그 범위로 쓴다.
5. **방법의 가치:** 새 정책을 제안한다면 단순 RAG·iterative agent·planner·graph와 동일 budget으로 이점/비용을 확인한다. 원천 subset에서는 DOI/text/common-parent 대조도 사용한다. 이득이 없어도 결과를 숨기지 않는다.
6. **재현 가능성:** snapshot·schema·도구 trace·실패·채점 규칙과 실행 명령이 독립 환경에서 돌아가야 한다. 유료 모델의 실제 실행 없이 점수 표를 만들어 두지 않는다.

2026 NeurIPS 공식 CFP는 main과 Evaluations & Datasets를 별도 트랙으로 명시하며, main도 기존 방법의 한계를 새롭게 분석하는 연구를 환영한다. E&D의 채택도 본 학회 proceedings에 실리지만 main track과 동일한 트랙이라고 표현하면 안 된다. NeurIPS 2027 트랙·마감은 현재 문서에서 확정하지 않는다. 한국어 agent에 대한 실증 분석이 중심이면 향후 ACL/EMNLP main의 해당 연도 CFP도 확인해 적합성을 판단한다. [Main CFP](https://neurips.cc/Conferences/2026/CallForPapers), [E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)

## 9. 조사·권한 확인 범위

검색 묶음은 한국어 agent benchmark, scientific multi-hop/citation-graph agent, reproducible scholarly tool environment, temporal validity/counterfactual evidence, citation laundering, dependent-source aggregation, text redundancy vs empirical independence였다. 검색 중 2차 요약에서 찾은 후보도 아래 표의 최종 근거는 arXiv·ACL Anthology·PMLR·저자 GitHub·저널 원문 등으로 다시 확인했다. 최근 preprint는 peer-reviewed 채택 논문으로 격상하지 않았다.

직접 확인한 코드/데이터 라이선스 예: K-BrowseComp 저장소와 공식 데이터 카드 MIT, AgentHop 공식 데이터 카드 CC-BY 4.0, ScholarQABench 저장소 MIT, AstaBench 저장소 Apache-2.0, WebArena 저장소 Apache-2.0, DeepResearch Bench 저장소 Apache-2.0, ScholarGym 공식 데이터 카드 Apache-2.0. 이 정보는 각 benchmark의 모든 입력 PDF·원본 웹페이지에 일괄 적용되지 않는다. 나머지 논문·artifact는 별도 license field를 확인하기 전 재사용하지 않는다.

이 보고서는 외부 benchmark 질문·답·gold trajectory·프롬프트·구현을 가져오지 않았다. 기존 포크의 아이디어도 선행 설계로 명시하고, 다른 논문과의 비교를 통해 주장 경계를 바꾸는 제안이다.
