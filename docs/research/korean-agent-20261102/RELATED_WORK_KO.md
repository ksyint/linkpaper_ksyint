# LinkPaper 한국어 연구 에이전트 벤치마크: 선행연구 검토와 연구 질문

조사일: 2026-11-02. 이 문서는 연구 설계 제안이며, 모델 실험 결과·학회 채택·세계 최초라는 사실을 주장하지 않는다. 논문 원문, 저자 저장소, 공식 학회·데이터 카드에서 확인한 내용과 아래의 제안을 구분한다. 웹 전체를 완전히 조사했다는 뜻은 아니다. 가까운 연구를 찾는 방향으로 검색했고, 특히 2026년 9–10월의 새 연구를 기존 제안과 비교했다.

## 1. 먼저 바꿔야 하는 주장

기존 포크의 `research/neurips-2027-benchmark-proposal` 브랜치에는 LINK-DELTA라는 조건 적합성·근거 삭제 후 결론 수정 제안이 이미 있다. 이를 새 기여라고 다시 내세우기 전에, 후속 선행연구와 겹치는 부분을 갱신해야 한다. [기존 제안](https://github.com/ksyint/linkpaper_ksyint/blob/research/neurips-2027-benchmark-proposal/docs/research/neurips-2027/PROPOSAL_KO.md)

한국어, 인용 그래프, 멀티홉, 도구 sandbox, frozen search, evidence checklist, counterfactual pair, validity ledger는 각각 이미 연구된 요소다. 특히 **SciValidityBench(2026-10-26)**는 과학적 증거의 사용 적격성, 실행 가능한 과제 생성, 반사실 쌍, 손상·복구 진단까지 제공한다. 일반적인 “과학 근거가 현재 결론을 정당화하는가”를 처음 측정한다는 주장은 피해야 한다. [논문](https://arxiv.org/abs/2610.34767), [본문](https://arxiv.org/html/2610.34767v1)

인용 수가 독립적인 증거 수와 같지 않다는 문제 역시 새 발견이 아니다. Greenberg는 2009년에 과학 인용망에서 새 데이터를 제공하지 않는 논문들이 주장의 권위를 증폭하는 과정을 분석했다. 최근 CONFPROP 연구도 공통 상위 출처와 복제 연쇄를 가진 증거를 독립적으로 합산하는 문제를 직접 다룬다. [Greenberg](https://doi.org/10.1136/bmj.b2680), [CONFPROP](https://doi.org/10.1007/s44163-026-02245-5)

따라서 새 이름이나 요소 조합 자체를 기여로 삼으면 약하다. **한국어 1차 문헌의 실제 실험·데이터 계보를 사람이 확인한 평가 자료**, **에이전트가 그 계보를 탐색하는 과정**, **텍스트 중복과 실증적 독립성의 혼동을 분리하는 대조 실험**을 제공하고, 이것이 기존 점수에서 보이지 않는 실패를 드러내는지 검증하는 쪽이 더 방어 가능하다. 이 차이도 아직 입증된 독창성이 아니라 검증할 후보 경계다.

## 2. 추천하는 중심 연구 질문 하나

> 문서 수·주장의 표면적 지지·검색 예산을 통제했을 때, 한국어 연구 에이전트는 **한 실험의 결과를 재인용한 여러 문헌**과 **원문으로 확인되는 서로 다른 실험·결과 단위의 증거**를 구별하는가? 반복 인용이 늘 때는 결론을 유지하고, 조건에 맞는 새 실험·결과 단위가 추가될 때는 결론을 적절히 바꾸는가?

가제는 **“한국어 학술 에이전트의 실증 근거 계보 추적 평가”** 정도로 두자. 이름에 “first”, “causal”, “independent truth”, “complete scientific verification”를 넣지 않는다. 기존 LinkPaper의 논문 검색·본문·인용 연결 기능은 평가 환경으로 활용할 수 있다. 서비스 UI를 개선했다는 사실과 새 평가가 유효하다는 사실은 각각 확인한다. [LinkPaper 소개](https://github.com/linkmind-ai/linkpaper)

### 2.1 무엇을 세는가

`paper_id`, `version_family_id`, `empirical_study_family_id`, `analysis_id`, `evidence_span`을 구분한다. 한 연구가 preprint와 출판본 두 개로 발표되거나 여러 review에서 소개되어도 1차 데이터 수집 단위가 자동으로 늘어나지 않는다. 반대로 서로 다른 연구가 비슷한 문장을 사용했다고 같은 실험이 되는 것도 아니다.

- **논문 단위:** 출판물의 수. DOI가 다르다는 사실만으로 실험 독립성이 보장되지 않는다.
- **버전 단위:** 동일 논문의 preprint·학회·저널 확장판 관계. 버전 판정과 실험 판정은 다르다.
- **실증 연구 단위:** 대상·수집 절차·데이터 식별자·실험 설정을 근거로 주석한 단위. 한 논문이 여러 단위를 담을 수 있다.
- **분석 단위:** 같은 데이터에 다른 분석을 수행한 경우. 새로운 분석의 가치를 부정하지 않되 독립적인 데이터 수집과 구별한다.
- **계보 불명:** 공개 본문만으로 관계를 판정할 수 없는 경우. 이를 “독립”으로 채우지 않는다.

저자 중복이나 인용 연결만으로 `same study`를 판정하지 않는다. 서로 다른 저자도 같은 데이터에 의존할 수 있고, 같은 저자도 별도 실험을 수행할 수 있다. `cites`와 `reuses_data`, `reports_same_experiment`, `summarizes`, `extends` 같은 관계는 별도로 주석해야 한다.

주요 채점 대상은 **명시적으로 정의한 실험·결과 단위의 비중복성**이다. 이것을 통계적 독립성이나 인과적 독립성으로 부르지 않는다. 데이터 수집의 공유 여부는 별도 속성으로 기록한다. 표준 공개 데이터셋을 이용한 ML 비교에서는 “새 연구”와 “새 데이터”를 따로 기록하고, 어떤 기준을 채점하는지 문제에 명시한다.

### 2.2 왜 단순한 중복 문서 제거와 다른가

핵심 대조는 다음 네 경우다. 문서 수와 길이를 가능한 범위에서 맞추고, 배치 순서를 교차한다.

| 경우 | 텍스트 유사성 | 1차 실증 계보 | 바람직한 판정 |
|---|---|---|---|
| 동일 연구의 직역·재인용 | 높음 | 같은 단위 | 새 실증 근거로 중복 계산하지 않음 |
| 동일 연구를 서로 다른 표현으로 소개한 review들 | 낮음 | 같은 단위 | 표현이 달라도 중복 계산하지 않음 |
| 별도로 수집된 연구들의 유사한 결과 보고 | 높을 수 있음 | 분리된 단위 | 문장 중복만으로 합치지 않음 |
| 관계를 확인할 정보가 부족한 보고 | 임의 | 불명 | 독립성을 단정하지 않음 |

이를 충분히 확보하지 못하면 이 프로젝트는 일반적인 RAG 중복 제거 실험으로 축소될 수 있다. 그 경우 “새 계보 이해 능력을 평가한다”는 주장을 내려놓아야 한다.

## 3. 중복 위험이 큰 선행연구 지도

아래 표는 각 연구가 이미 무엇을 측정하는지와 이번 후보 질문의 경계를 정리한다. “차이 후보”는 그 논문에 해당 기능이 전혀 없다는 보편적 부정이 아니다. 후속 버전과 부록도 제출 전에 다시 대조한다.

| 연구·최초 공개/확인 상태 | 이미 제공하는 것 | 이번 연구의 차이 후보와 충돌 위험 |
|---|---|---|
| [K-BrowseComp](https://arxiv.org/abs/2606.02404), 2026-06-01 | 한국 맥락 400문항, 사람 검증 300 + 합성 진단 100. 멀티홉·병렬 제약, 예상 경로와 중간 증거 checklist. | 한국어·다중 근거·경로 진단 자체는 차별점이 아니다. 실제 학술 연구 단위 계보가 중심이어야 한다. 매우 높음. |
| [AgentHop](https://arxiv.org/abs/2609.34428), 2026-09-28 | 1,011개 과학 MCQ, 7개 도구, 예산 제한. 검색·합성·도구·자원 진단. [공식 데이터 카드](https://huggingface.co/datasets/nlpai-lab/agenthop) | seed paper의 인용망 탐색과 실패 분해는 기존 작업이다. 실험 계보 단위의 과제와 평가가 추가로 필요하다. 매우 높음. |
| [IdeaGene-Bench](https://arxiv.org/abs/2607.08758), 2026-07-09 preprint | 아이디어의 상속·변형·재조합 계보와 새 아이디어 생성 평가. [공식 코드](https://github.com/VisionXLab/IdeasHaveGenomes) | “과학 계보 추론 최초”는 주장할 수 없다. 아이디어 상속과 실험 결과 재보고 계보를 구분하고, 후자를 실제로 새롭게 측정하는지 검증한다. 매우 높음. |
| [SciNet](https://proceedings.mlr.press/v306/shao26h.html), ICML 2026 main | 논문 관계를 ego/pair/path 수준에서 검색하는 8,940과제. 상충 연구·기술 계보 등. | 인용 관계·연구 흐름을 찾는 것만으로 새롭지 않다. bibliographic lineage와 empirical study lineage를 분리해야 한다. 매우 높음. |
| [SciValidityBench](https://arxiv.org/abs/2610.34767), 2026-10-26 preprint | 64 TaskSpec, 다섯 validity 모듈과 여섯 과학 영역. 결정의 유효성, 쌍 조건과 손상·복구. | 일반 조건 적합성·과학 상태 ledger·counterfactual은 선행연구로 인정한다. 실제 한국어 문헌의 데이터 계보 감사가 별도 측정 대상을 만드는지 검증한다. 매우 높음. |
| [SciConBench](https://arxiv.org/abs/2606.11337), 2026-06-09 | 체계적 문헌고찰 기반 9.11K 질문·결론, clean-room 도구, 원자 사실 precision/recall. | 과학 결론 종합·상충 근거 해소·답안 누출 차단은 기존이다. 전문 임상 결론의 진위를 새로 판정하는 범위까지 확대하지 않는다. 높음. |
| [ScholarGym](https://arxiv.org/abs/2601.21654), 2026-01-29 | 570K 논문, 2,536 전문가 주석 질의, 결정적 검색, 계획·도구·관련성 분해. | frozen academic tool environment 자체는 새 기여가 아니다. 매우 높음. |
| [PaperArena](https://arxiv.org/abs/2510.10909), 2025-10-13 | 여러 논문의 다양한 형식을 통합하고 parsing·retrieval·computation 도구로 답하는 플랫폼. | 학술 도구 orchestration·cross-paper QA 자체는 새롭지 않다. 매우 높음. |
| [AstaBench](https://arxiv.org/abs/2510.21652), 2025-10-24, ICLR 2026 | 2,400+ 과학 과제, 재현 가능한 검색 도구, 비용·도구 접근 통제, 여러 agent class. | 공정한 도구·예산 통제와 과학 agent suite는 선행 방법이다. 넓은 전주기 벤치마크를 새로 만드는 방향은 피한다. 높음. |
| [ScholarQABench/OpenScholar](https://doi.org/10.1038/s41586-025-10072-4), 논문·공식 코드 확인 | 분야별 문헌 종합과 인용 평가. [공식 저장소](https://github.com/AkariAsai/ScholarQABench) | “논문을 찾아 인용한 긴 답변”을 평가하는 것만으로 부족하다. 개별 연구의 중복 집계 실패를 분리해야 한다. 높음. |
| [ScholarBench](https://arxiv.org/abs/2505.16566), 2025-05-22 / EMNLP Findings 2025 | 한국어 5,031·영어 5,309 academic reasoning 사례. | “한국어 과학 문제” 자체도 차별점이 아니다. 도구 탐색과 실제 근거 계보에 초점을 둔다. 높음. |
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

KoTAU는 로컬 `README.md`에서 한국 여행용 offline tool 환경과 DB 사본, 합성 열 provenance를 확인했다. 공개 GitHub URL은 이번 web 조회에서 404여서 공개 논문으로 취급하지 않는다. 로컬 main은 label과 grading이 미정이라고 명시한다. 내부 설계 참고와 공개된 평가 결과를 구분한다. 전체 브랜치·파일 감사는 별도 로컬 조사 보고서를 따른다.

## 4. 주장할 수 있는 차이와 주장하면 안 되는 차이

가능한 기여 후보는 다음 네 가지를 **함께 검증했을 때** 성립한다.

1. 한국어 원문을 포함한 실제 학술 자료에서 `publication ↔ study ↔ data/experiment`의 관계를 근거 span까지 확인한 새 주석 자료.
2. agent가 제한된 관측과 도구 예산으로 원문·참조·방법을 찾아 그 관계를 복원하는 과제.
3. 문서 개수·텍스트 유사도·주장 지지·독립 실험 개수를 분리하는 matched intervention. 인위적인 예시는 controlled split으로 명확히 표시하고 실제 관찰 문헌과 합쳐 하나의 자연 분포라고 주장하지 않는다.
4. 최종답·개별 citation 점수가 높은 agent도 study-family 중복 집계나 잘못된 독립성 선언을 하는지에 관한 사전 등록된 실증 분석.

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

1차 과제는 장문의 자유 보고서보다 닫힌 평가가 가능한 **근거 집합 판단**으로 시작한다. 예: “지정한 조건에서 서로 다른 실험·결과 단위가 두 개 이상 이 주장을 직접 지지하는가?” 문제에는 독립성의 운영 정의와 기준 시점을 명시한다. agent는 `supported_threshold / below_threshold / indeterminate` 중 하나와 1차 보고 문헌·근거 span·문헌 사이의 계보 설명을 반환한다.

gold는 판단·적격한 연구 단위 집합·허용 가능한 대체 지지 span·알려진 의존성 관계를 가진다. `indeterminate`는 annotation 누락을 숨기는 답이 아니라 공개된 입력에서 필요한 계보를 판별할 수 없다는 전문가 합의여야 한다. 실제 세계 전체에서 연구가 없다고 말하지 않고 **버전 고정된 bounded corpus 안에서의 판정**으로 한정한다.

agent가 study-family의 숨겨진 gold ID를 그대로 출력하게 하지 않는다. 공개 문헌 ID와 span을 제출하게 하고 grader가 비공개 mapping으로 평가한다. 대조 pair의 이름·파일명·도구 응답에 `independent=true` 같은 정답 단서를 노출하지 않는다. oracle graph를 제공하는 조건은 upper bound 실험으로 따로 둔다.

### 5.2 권장 조건 행렬

| 축 | 조건 | 분리하려는 설명 |
|---|---|---|
| 정보 처리 | closed-book / flat RAG / iterative retrieval agent / graph-enabled agent | parametric prior, 검색 이득, 순차 탐색, 그래프 접근을 분리 |
| 계보 정보 | 본문·기본 인용 / bibliographic graph / 사람이 검증한 계보 oracle | 그래프 존재와 올바른 계보 이해를 분리 |
| 문서 집합 | 실증 단위 유지하며 secondary report 증가 / 실제 별도 1차 실험 추가 | 문서 수와 실증 수 분리 |
| 표면 형태 | exact copy / 낮은 유사도 paraphrase·review / 유사한 표현의 별도 실험 | 텍스트 dedup shortcut 점검 |
| 언어 | 한국어 질문·원문 / 같은 원문의 영어 질문 / 검토된 bilingual 대응 자료 | 질문 언어와 evidence 언어를 분리 |
| 예산 | 동일 tool call cap + 기록된 input/output token·시간·비용 | 더 많은 compute를 능력 향상으로 오해하지 않음 |
| 난도 | 문헌 수·계보 깊이·대체 근거 수·미상 관계 비율 | 쉬운 metadata shortcut과 진짜 복합 판정 분리 |

모든 모델에 같은 검색 corpus·ranking cache·tool schema·문서 순서 seed를 제공한다. 한 모델의 검색 결과를 다른 모델에게만 주는 비교는 피한다. 여러 agent scaffold를 사용할 경우 backbone을 고정한 비교와 scaffold를 고정한 비교를 각각 둔다. GUI 사용 능력을 핵심 가설과 섞지 말고 API 도구 agent를 1차 실험으로 둔다.

### 5.3 필수 baseline

- citation/document 개수만 세는 규칙 baseline: 우리가 겨냥한 shortcut의 하한선.
- DOI·제목·버전 exact dedup: 단순 서지 중복이 해결하는 부분.
- 텍스트 near-duplicate/embedding clustering: 표현 중복이 해결하는 부분.
- 인용 공통 조상 또는 source-discounted heuristic: 구조만 이용하는 baseline. 실제 연구 재사용 관계와 같다고 가정하지 않는다.
- BM25/dense flat RAG + 같은 generator.
- 같은 generator의 iterative search, citation-graph search.
- 사람이 확인한 study lineage를 제공한 oracle: retrieval과 판정의 병목 분리.
- full evidence를 읽는 전문가 upper bound와 초급 연구자 baseline: 인간에게도 모호한 task를 구별.

CONFPROP를 구현·이식한다면 원 구현과 라이선스를 먼저 확인하고 attribution과 차이를 명시한다. 이 문서는 해당 코드 복제를 권하지 않으며, 독립적으로 명세한 source-discounted baseline만으로도 첫 실험을 시작할 수 있다.

### 5.4 측정 항목

1차 지표는 **같은 base claim에서 만들어진 두 조건을 모두 맞히는 비율**과 계보 변화에 대한 올바른 `유지/변경`이다. “무조건 답을 바꾸는 agent”와 “무조건 유보하는 agent”가 통과하지 못해야 한다. primary metric·분모·parse 실패 처리·재시도 규칙을 pilot 이전에 고정한다.

보조 지표는 다음을 분리한다.

- 적격 1차 연구 집합의 precision/recall, 중복 집계 오차, explicit false-independence rate.
- 문헌 사이 같은 연구 단위 판정의 pairwise precision/recall. 불명 관계를 강제로 이분하지 않는다.
- 인용 span 지지 정확도와 허용 대체 span 회수율.
- trace에서 실제로 읽은 문헌에 근거를 연결했는지, 핵심 method/provenance span을 취득했는지.
- 답의 유보율과 올바른 유보율. 항상 `indeterminate`를 내는 baseline을 함께 둔다.
- 모델별 비용·시간·검색량과 정확도의 Pareto 관계.

외부의 citation evaluator 점수와 새 계보 점수가 얼마나 일치·불일치하는지 보고한다. 일반 점수의 약점을 미리 확정하지 말고 **상관이 높고 순위가 같을 경우**도 결과로 받아들인다.

통계 단위는 파생 world/번역문의 개수가 아닌 **base claim 또는 공유 연구 계보 cluster**다. split도 그 단위로 한다. cluster bootstrap이나 그에 준하는 paired 분석을 사전 명세한다. 여러 seed를 돌려 평균·분산·모든 실패를 남기고, best-of만 보고하지 않는다. model×tool×language×world 전체를 처음부터 거대 행렬로 돌리지 말고 pilot에서 표본 분산·실행 비용을 추정한 뒤 표본 수와 반복 수를 정한다.

## 6. 어떤 데이터를 모으고 어떤 것을 사람이 라벨해야 하는가

### 6.1 반드시 남길 원본 provenance

각 문헌의 URL/DOI, 버전, 접근일, 원문 hash, 언어, 공개 라이선스, 사용 허용 범위, section/page/표 식별자를 남긴다. 문제·번역·태그·label도 작성자와 검수 이력을 분리한다. 기존 benchmark 문제나 예상 경로를 seed로 삼지 않는다.

공개 metadata의 이용 조건과 PDF 본문·번역문의 재배포 조건은 다르다. 코드가 MIT/Apache여도 논문 원문까지 같은 조건으로 배포 가능한 것은 아니다. 한국어 논문은 기관 사이트에 보인다는 이유만으로 수집·재배포가 허용되었다고 간주하지 않는다. 허용 조건이 확인된 원문을 우선하고, 나머지는 URL·서지 정보·직접 작성한 annotation을 분리해 다룬다.

### 6.2 수작업이 필요한 핵심 주석

자동 DOI 정규화·해시·출판일 수집은 보조할 수 있지만 다음은 이 프로젝트의 실제 노동이다.

- 문서별 주장의 지지·반박·단순 소개 여부와 직접 근거 span.
- 실험/대상/평가 데이터/조건 tuple 및 같은 연구의 재보고 여부.
- review의 인용이 어느 1차 결과로 연결되는지. 연결이 없거나 모호하면 불명으로 표시.
- 번역·학술 용어 alias가 qualifier와 방향을 보존하는지.
- 모든 허용 대체 1차 근거가 corpus 안에서 주석되었는지.
- pair가 목표 정보만 바꿨는지, 문서 수·길이·어휘·검색 순서 같은 단서가 label을 누출하지 않는지.

각 base case는 서로 독립적으로 작업한 두 명이 라벨하고, 근거 span과 불일치 이유를 남긴다. 최초 작성자가 자기 문제의 최종 합의를 단독 결정하지 않는다. 분야 전문성이 부족하면 외부 전문가 검수 표본을 확보하고, 충분한 판정 근거를 만들지 못한 분야는 본 평가에서 제외한다. agreement는 adjudication 전 수치와 사후 합의 수치를 분리해 기록한다.

### 6.3 5인 저자 체계에서의 pilot 분담 예시

확정된 저자는 김수용(1저자), 정상헌·남두현·오창원·이상민(순위 미정)이다. 기존 프로젝트의 직함은 이 배분에 사용하지 않는다. 아래는 **실행 가능한 첫 40 base case pilot**의 균등 수집·교차검수 예시이며 저자 순위를 정하는 규칙이 아니다.

| 담당 | 1차 수집·주석 | 독립 2차 검수 | 공동 산출물 |
|---|---:|---|---|
| 정상헌 | 10 base case | 남두현의 10건 | case manifest·원문 권한·study mapping |
| 남두현 | 10 base case | 오창원의 10건 | 동일 |
| 오창원 | 10 base case | 이상민의 10건 | 동일 |
| 이상민 | 10 base case | 정상헌의 10건 | 동일 |
| 김수용 | pilot 규약·harness·통계 설계 | 불일치 adjudication을 조율하고 일부 독립 재검수 | protocol freeze, baseline 실행, 오류 분석·논문 통합 |

김수용이 원자료 전문 판정을 혼자 대신하지 않는다. 대규모 확장 전에 40건에서 유효 case 수·수집 탈락률·검수 시간·agreement·모델 cost를 측정한다. 40건이나 그 파생 수백 world를 최종 논문 benchmark 크기로 포장하지 않는다. 본 데이터 크기와 인력은 pilot 측정 후 조정하고, 나머지 공저자도 실험·분석·집필 기여를 맡아 학술적 기여가 수집 건수에만 묶이지 않게 한다.

## 7. 표절·오염을 줄이는 개발 절차

- 관련 연구에서 문제를 먼저 읽고 비슷하게 바꾸는 방식으로 task를 만들지 않는다. corpus의 원문 사실에서 시작해 독립적으로 질문을 작성하고, 이후 별도 검수자가 benchmark 질문 중복을 확인한다.
- 차용한 데이터·코드·그림·수식·평가 항목과 독립 작성물을 `source / license / copied files / changes / citation` 단위로 기록한다. 원래 LinkPaper MIT 파일을 발전시킬 때 저작권 고지와 기존 기여를 보존한다.
- 논문의 중심 아이디어가 선행연구와 겹치면 “동일 원리의 한국어 실제 문헌 검증”처럼 범위를 정확히 쓴다. attribution은 중요하지만 인용 하나가 독창성 증명을 대신하지는 않는다.
- task text·답·gold graph·예상 경로·adjudication note는 agent에게 제공하는 corpus/tool view와 분리한다. test split의 base family를 dev에 공유하지 않는다.
- 수집 문헌 자체에 benchmark 답안·review·프로젝트 설명이 섞였는지 검사한다. 논문 hash·DOI·근거 span·주장 embedding 등을 보조로 쓰고 사람이 false positive를 확인한다.
- 새로운 문헌·버전의 시간 holdout, 저자/연구/데이터 단위 cluster holdout을 각각 평가한다. “모델 지식 cutoff 이후 자료”만으로 오염이 없다고 단정하지 않는다.
- 완전한 표절 부재나 인터넷 전체의 독창성을 자동 보장할 수는 없다. 검색 로그·원자료 추적·코드 출처·검수 기록을 남겨 검토 가능한 주장을 한다.

## 8. 메인 학회 수준을 판단할 중단·확장 기준

메인 학회 목표의 근거는 코드 분량이나 문제 수보다 **새롭고 일반화 가능한 발견**이어야 한다. 아래 조건을 만족하지 못하면 제목을 키우기보다 먼저 연구 질문을 좁히거나 바꾼다.

1. **측정 유효성:** 전문가가 동일 연구·별도 연구·불명을 안정적으로 구별하며, task의 정답을 강한 텍스트/DOI shortcut만으로 대부분 맞히지 못한다.
2. **차별적 발견:** 기존 final-answer/citation 점수와 계보 실패의 차이를 통계적으로 검증한다. 차이가 없으면 새 지표 필요성 주장을 약화한다.
3. **원인 분리:** 문서 길이·검색 order·더 많은 token·번역 품질·도구 차이가 효과를 설명하지 않는지 matched control로 본다.
4. **일반화:** 여러 모델 family·새 corpus family·한국어/영어 대응 조건에서 결과를 확인한다. 한 모델·한 분야만의 현상은 그 범위로 쓴다.
5. **방법의 가치:** 새 agent 정책을 제안한다면 단순 DOI dedup·near-duplicate clustering·source-discounting을 넘어서는 이점과 비용을 확인한다. 이득이 없다면 benchmark 결과를 숨기지 않는다.
6. **재현 가능성:** snapshot·schema·도구 trace·실패·채점 규칙과 실행 명령이 독립 환경에서 돌아가야 한다. 유료 모델의 실제 실행 없이 점수 표를 만들어 두지 않는다.

2026 NeurIPS 공식 CFP는 main과 Evaluations & Datasets를 별도 트랙으로 명시하며, main도 기존 방법의 한계를 새롭게 분석하는 연구를 환영한다. E&D의 채택도 본 학회 proceedings에 실리지만 main track과 동일한 트랙이라고 표현하면 안 된다. 2027 트랙·마감은 현재 문서에서 확정하지 않는다. 한국어 agent에 대한 실증 분석이 중심이면 향후 ACL/EMNLP main의 해당 연도 CFP도 확인해 적합성을 판단한다. [Main CFP](https://neurips.cc/Conferences/2026/CallForPapers), [E&D CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets)

## 9. 조사·권한 확인 범위

검색 묶음은 한국어 agent benchmark, scientific multi-hop/citation-graph agent, reproducible scholarly tool environment, temporal validity/counterfactual evidence, citation laundering, dependent-source aggregation, text redundancy vs empirical independence였다. 검색 중 2차 요약에서 찾은 후보도 아래 표의 최종 근거는 arXiv·ACL Anthology·PMLR·저자 GitHub·저널 원문 등으로 다시 확인했다. 최근 preprint는 peer-reviewed 채택 논문으로 격상하지 않았다.

직접 확인한 코드/데이터 라이선스 예: K-BrowseComp 저장소와 공식 데이터 카드 MIT, AgentHop 공식 데이터 카드 CC-BY 4.0, ScholarQABench 저장소 MIT, AstaBench 저장소 Apache-2.0, WebArena 저장소 Apache-2.0, DeepResearch Bench 저장소 Apache-2.0, ScholarGym 공식 데이터 카드 Apache-2.0. 이 정보는 각 benchmark의 모든 입력 PDF·원본 웹페이지에 일괄 적용되지 않는다. 나머지 논문·artifact는 별도 license field를 확인하기 전 재사용하지 않는다.

이 보고서는 외부 benchmark 질문·답·gold trajectory·프롬프트·구현을 가져오지 않았다. 기존 포크의 아이디어도 선행 설계로 명시하고, 다른 논문과의 비교를 통해 주장 경계를 바꾸는 제안이다.
