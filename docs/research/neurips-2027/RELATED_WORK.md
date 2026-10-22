# 관련 연구와 독창성 검토

조사 기준일: **2026-10-22**. 제목과 내용은 아래 논문 원문·공식 학회 페이지·저자 공개 자료에서 확인했다. 아래 “차이”는 제안의 포지셔닝이며, 해당 논문에 그 기능이 전혀 없다는 전수 검증 결과가 아니다. 초록 중심으로 확인한 연구는 그렇게 표시했다. 채택 여부가 확인되지 않은 arXiv 자료를 채택 논문으로 표기하지 않는다.

## 1. 가장 위험한 중복부터

| 연구·확인 범위 | 이미 제공하는 것 | LINK-DELTA에서 새로 입증해야 할 차이 | 중복 위험 |
|---|---|---|---|
| **AgentHop** — 2026 arXiv, HTML 본문의 과제·진단 축·한계 확인 | 인용 연결을 통한 멀티홉 과학 QA, 도구 sandbox, 검색·합성·도구·자원 진단 | 단순 멀티홉 대신 동일 질문의 조건 적합성·대체 근거 차단을 주석한 환경 변화 평가 | 매우 높음 |
| **SciNet** — v2 초록·공개 정보 확인, 초기 명칭 SciNetBench | 논문 간 관계, 관련·상충 연구, 연구 발전 경로의 검색 평가 | 관계를 찾아내는 것을 넘어, 그 근거가 목표 조건의 결론을 정당화하는지 검증 | 매우 높음 |
| **OpenScholar / ScholarQABench** — Nature 본문·arXiv 확인 | 여러 분야의 문헌 합성과 장문 답변·인용·전문가 평가 | 새로운 문헌 합성 QA 자체를 기여로 삼지 않고 정적 평가와 근거 변화 대응을 대조 | 매우 높음 |
| **ResearchQA** — 2026 초록 확인 | 단일 논문의 citation-grounded QA, 복수 지지 passage, 근거 있는 유보 | 복수 근거·유보 자체는 새롭지 않음. 논문 간 조건 일치와 환경 묶음이 추가하는 정보 필요 | 높음 |
| **Correctness is not Faithfulness** — 초록·저자 공개 논문 확인 | 인용의 내용적 정당성과 실제 의존성의 차이, post-rationalization 실험 | “인용이 맞아도 근거를 안 쓸 수 있다”는 발견을 새 발견으로 주장하지 않음 | 매우 높음 |
| **RAGONITE / ConfQuestions** — 초록 확인 | 근거 문맥화, 근거 제거를 통한 counterfactual attribution | 단순 근거 제거·답변 변경 비교는 독창성 근거가 아님. 충분 근거와 조건 검증 필요 | 매우 높음 |
| **RGB / ClashEval** — 초록·공식 proceedings 확인 | 잡음, 유보, 정보 통합, 틀린 문맥과 모델 사전 지식의 충돌 | 조작된 사실을 따라가는 능력 대신 실제 논문의 조건 적격성과 필수 전제 평가 | 높음 |
| **SURE-RAG** — v2 초록 확인 | 근거 충분성, support/refute/insufficient 판정, multi-hop 및 swap 대조 | 충분성·3-way 판정도 독창성 아님. 실제 과학적 조건·대안 근거 주석의 가치 입증 | 높음 |
| **CLAIM-BENCH / SciFact** — 초록·공식 페이지 확인 | 과학 주장과 근거 추출·검증 | 주장–근거 매칭 단독이 아니라 조건 보존과 환경 간 판정 변화가 대상 | 높음 |
| **SciConBench** — 2026 초록·저자 소개 확인 | 실제 체계적 문헌고찰의 결론 합성, atomic facts, clean-room 평가 | 새 “과학 결론 합성”이나 단순 live benchmark로 포장하지 않음 | 높음 |

핵심 판단: **“과학 논문 + GraphRAG + 멀티홉 + 인용 평가”는 이미 혼잡한 조합**이다. 이 조사에서 제안한 모든 부품이 새로운 것은 아니다. 본 연구의 가치가 생기려면 조건 호환성을 주석한 근거 환경이 기존 점수와 다른, 전문가에게 유의미한 오류를 안정적으로 드러내야 한다.

## 2. 출처별 메모

### R01. QASPER

Dasigi et al., **A Dataset of Information-Seeking Questions and Answers Anchored in Research Papers**, NAACL 2021. [학회 원문](https://aclanthology.org/2021.naacl-main.365/).

제목·초록을 보고 질문을 작성하고 다른 실무자가 본문 근거와 답변을 주는 분리된 수집 방식이 중요하다. 단일 논문 내 복수 근거도 다룬다. LinkPaper의 기존 외부 벤치마크 어댑터를 활용할 수 있다. 질문과 정답 작성자를 분리하는 설계는 이 연구를 인용해야 한다.

### R02. SciFact

Wadden et al., **Fact or Fiction: Verifying Scientific Claims**, EMNLP 2020. [학회 원문](https://aclanthology.org/2020.emnlp-main.609/).

전문가 과학 주장에 대해 지지·반박 초록과 rationale을 연결한다. 과학 주장 검증 자체의 중요한 선행연구다. LINK-DELTA는 원문 조건의 호환성과 근거 환경 사이의 변화에 초점을 둬야 한다.

### R03. ALCE

Gao et al., **Enabling Large Language Models to Generate Text with Citations**, EMNLP 2023. [학회 원문](https://aclanthology.org/2023.emnlp-main.398/), [저자 코드](https://github.com/princeton-nlp/ALCE).

답변 correctness와 citation quality를 구분한 근거 생성 평가다. 주장별 인용의 지지·누락을 평가할 때 참고한다. 단순 “인용을 포함하는 답변”이나 그 평가를 새로운 과제로 주장하지 않는다.

### R04. OpenScholar / ScholarQABench

Asai et al., **Synthesizing scientific literature with retrieval-augmented language models**, Nature 2026. [출판본](https://www.nature.com/articles/s41586-025-10072-4), [2024 arXiv 초기본](https://arxiv.org/abs/2411.14199).

문헌 검색·종합 답변과 인용 평가의 직접 비교 대상이다. 초기 arXiv와 출판본의 데이터 규모가 다르므로 버전별 수치를 섞지 않는다. 우리 연구는 ScholarQABench를 한국어 또는 HF Papers 데이터로 바꾸는 수준에 머물면 안 된다. 이번 제안은 해당 benchmark 문항·정답을 가져와 신작 데이터로 쓰는 것이 아니다.

### R05. PaperQA2 / LitQA2

Skarlinski et al., **Language Agents Achieve Superhuman Synthesis of Scientific Knowledge**, 2024. [저자 공개 논문](https://storage.googleapis.com/fh-public/paperqa/Language_Agents_Science.pdf), [저자 설명](https://www.futurehouse.org/research/engineering-blog-journey-to-superhuman-performance-on-scientific-tasks).

검색→근거 수집→답변의 agentic baseline과 문헌 QA 평가를 참고한다. 논문 제목의 superhuman 표현을 우리 시스템의 가능 성능으로 옮기지 않는다. 원 연구의 인간 비교 조건과 과제 범위를 벗어나 일반화해서는 안 된다. 향후 비교는 공개 구현과 고정 코퍼스 어댑트 범위를 명시한다.

### R06. LitSearch

Ajith et al., **LitSearch: A Retrieval Benchmark for Scientific Literature Search**, EMNLP 2024. [학회 원문](https://aclanthology.org/2024.emnlp-main.840/).

실제 문헌 검색 질문과 expert 검수의 참고점이다. 인용 문단 기반 생성 질문과 저자 작성 질문을 함께 사용한다. 우리도 생성 방식에 따른 성능 차이를 분석해야 한다. 검색 정답과 근거가 결론을 정당화하는지는 구분한다.

### R07. STaRK

Wu et al., **STaRK: Benchmarking LLM Retrieval on Textual and Relational Knowledge Bases**, NeurIPS 2024 Datasets and Benchmarks. [공식 proceedings](https://papers.nips.cc/paper_files/paper/2024/hash/e607b1419e9ae7cd5cb5b5bb60c2ad5c-Abstract-Datasets_and_Benchmarks_Track.html), [저자 코드](https://github.com/snap-stanford/stark).

텍스트와 관계를 결합한 검색을 이미 학술 논문 검색에도 평가한다. 구조화 관계와 텍스트를 함께 준다는 이유만으로 신규성을 주장할 수 없다. 강한 비그래프 retriever와 human-written 질문을 두는 설계에 참고한다.

### R08. GraphRAG-Bench

Xiao et al., **GraphRAG-Bench: Challenging Domain-Specific Reasoning for Evaluating Graph Retrieval-Augmented Generation**, 2025 arXiv. [논문](https://arxiv.org/abs/2506.02404).

교과서 기반 여러 도메인·형식의 추론 과제와 그래프 구축–검색–생성 전 과정을 평가한다. 현재 레포에도 다운로드·변환 설정이 있다. 레포 registry는 연구용·재배포 금지로 표시하므로, 원본을 새 공개 데이터에 섞기 전에 실제 데이터 라이선스를 다시 확인해야 한다. 우리 기여는 이를 다른 도메인에 복제하는 데 있지 않다.

### R09. CG-RAG

Hu et al., **CG-RAG: Research Question Answering by Citation Graph Retrieval-Augmented LLMs**, 2025 arXiv. [논문](https://arxiv.org/abs/2501.15067).

인용 그래프에 sparse/dense 검색 신호를 결합하는 연구 QA 방법이다. 이 계열을 비교하지 않고 단순 벡터 대비 인용 그래프의 유용성을 새 기법처럼 제시하면 약하다. 방법 baseline 후보이며 정확한 공개 구현 여부는 후속 확인 대상이다.

### R10. SciRAG

Ding et al., **SciRAG: Adaptive, Citation-Aware, and Outline-Guided Retrieval and Synthesis for Scientific Literature**, EACL 2026. [학회 원문](https://aclanthology.org/2026.eacl-long.303/), [저자 코드](https://github.com/yale-nlp/SciRAG).

적응적 검색, 인용 기반 reasoning, outline 기반 합성을 다룬다. 레포의 `docs/demo.png`에도 이 논문이 보이지만, 화면은 시스템 성능의 증거가 아니다. baseline 후보로 검토하되 제공 코퍼스와 생성 예산에 맞춘 변경을 별도 기록한다.

### R11. AgentHop

Park et al., **AgentHop: A Diagnostic Benchmark for Agentic Multi-Hop Scientific Question Answering**, 2026-09 arXiv. [논문](https://arxiv.org/abs/2609.34428), [HTML 본문](https://arxiv.org/html/2609.34428v1), [저자 코드](https://github.com/JohnnyNLP/agenthop).

1,011개 MCQ와 도구 sandbox를 제공하고 검색·합성·도구 사용·자원 관리를 분해한다. 본문의 parametric floor, generator–evaluator overlap, observational 한계는 우리 설계에도 직접 중요하다. 멀티홉 경로, 동일 예산, 진단 축을 추가하는 것만으로는 차별화가 안 된다. 재현 실험 전 최신 데이터 카드와 실제 release 버전을 맞춰야 한다.

### R12. SciNet

Shao et al., **SciNet: Evaluating AI Agents in Relation-Aware Scientific Literature Retrieval**, v2 2026. 초기 제목은 SciNetBench였다. [논문](https://arxiv.org/abs/2601.03260).

ego-centric, pairwise, path-wise 관계 이해 과제를 다룬다. 연구 계보, 상충 연구, 관계-aware retrieval 자체를 새 과제로 내세울 수 없는 이유다. 이번에는 초록과 버전 정보 중심으로 확인했다. 실제 조건 필드·관계 라벨·평가 부록에 우리 과제와 같은 항목이 있는지 먼저 정밀 확인해야 한다.

### R13. ResearchQA

Imran and Solanky, **ResearchQA: Benchmarking Citation-Grounded Question-Answering on Scientific Papers**, 2026-07 arXiv. [논문](https://arxiv.org/abs/2607.11074).

단일 논문 494편에서 만든 6,211개 QA, 복수 유효 지지 passage, 근거 있는 거절을 소개한다. `gold_chunk_ids` 한 벌만 쓰는 기존 레포보다 풍부한 근거 평가가 이미 존재한다. 대안 근거를 지원하는 것 자체는 우리 독창성의 충분한 근거가 아니다. 현재 메모는 초록 기준이다.

### R14. RGB

Chen et al., **Benchmarking Large Language Models in Retrieval-Augmented Generation**, 2023 arXiv / AAAI 2024. [논문](https://arxiv.org/abs/2309.01431), [AAAI 원문](https://ojs.aaai.org/index.php/AAAI/article/download/29728/31250).

noise robustness, negative rejection, information integration, counterfactual robustness를 이미 구분한다. 우리 네 환경을 이 네 능력에 이름만 바꿔 대응시키면 약한 확장이다. 실제 과학 조건 주석과 충분 근거 검증이 추가하는 측정 가치를 별도로 보인다.

### R15. ClashEval

Wu et al., **ClashEval: Quantifying the tug-of-war between an LLM’s internal prior and external evidence**, NeurIPS 2024 Datasets and Benchmarks. [공식 proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/3aa291abc426d7a29fb08418c1244177-Abstract-Datasets_and_Benchmarks_Track.html).

외부 근거를 정밀하게 변형해 모델 사전 지식과 충돌시킨다. “근거가 달라지면 답이 달라져야 한다”라는 관점의 직접 선행연구다. 우리는 원문의 진위 수치를 조작하지 않고, 질문 조건에 맞는지 다른 실제 근거로 진단하려 한다. 이 차이만으로 충분한지는 파일럿과 문헌 비교로 판단한다.

### R16. 인용 correctness와 faithfulness

Wallat et al., **Correctness is not Faithfulness in RAG Attributions**, 2024 arXiv / ICTIR 2025. [arXiv](https://arxiv.org/abs/2412.18004), [저자 공개본](https://mariaheuss.com/assets/correctness.pdf).

지지하는 인용과 답변 생성에 실제 영향을 준 인용을 구별하고 post-rationalization을 진단한다. 이 개념 구분은 반드시 인정해야 한다. 우리 환경 변화 검사는 행동적 민감성을 보는 것이며, 모델 내부의 실제 추론 경로나 완전한 causal faithfulness를 인증하지 않는다.

### R17. RAGONITE / ConfQuestions

Saha Roy et al., **Evidence Contextualization and Counterfactual Attribution for Conversational QA over Heterogeneous Data with RAG Systems**, 2024 arXiv. [논문](https://arxiv.org/abs/2412.10571).

기업 wiki 문맥의 QA에서 근거 제거에 따른 답변 변화로 attribution을 계산한다. 근거 제거 아이디어의 직접 선행연구다. 이번에는 초록을 확인했으며, attribution과 benchmark 구성을 실제 코드·본문으로 더 비교해야 한다.

### R18. SURE-RAG

Qiu et al., **SURE-RAG: Sufficiency and Uncertainty-Aware Evidence Verification for Selective Retrieval-Augmented Generation**, v2 2026. [논문](https://arxiv.org/abs/2605.03534).

set-level 근거 충분성, 세 가지 판정, selective answering, shortcut와 counterfactual swap 대조를 다룬다. 제안 baseline이나 감사 설계에 참고할 수 있다. “충분한 근거 없이는 유보한다”를 새 알고리즘 기여로 삼지 않는다. 초록 확인 단계이며 논문의 일반화 한계도 원문 재검토가 필요하다.

### R19. CLAIM-BENCH

Javaji et al., **Can AI Validate Science? Benchmarking LLMs for Accurate Scientific Claim → Evidence Reasoning**, 2025 arXiv. [논문](https://arxiv.org/abs/2506.08235).

과학 논문에서 주장–근거 추출과 validation을 평가한다. 조건 주석을 실제 원문에서 확인할 때의 직접 비교군이다. 이번 비교는 초록에 기반한다. 결과 수치나 비교 우위는 우리 제안의 근거로 전용하지 않는다.

### R20. RAGChecker

Ru et al., **RAGChecker: A Fine-grained Framework for Diagnosing Retrieval-Augmented Generation**, 2024. [논문](https://arxiv.org/abs/2408.08067), [저자 코드](https://github.com/amazon-science/RAGChecker).

검색과 생성의 세부 오류를 분해하고 human judgments와의 관계를 검증한다. Ragas 점수에 새 이름을 붙이는 대신, 기존 세부 지표로도 새 벤치마크의 오류를 설명할 수 있는지 비교해야 한다. metric meta-evaluation의 참고점이다.

### R21. SciConBench

Jung et al., **Can AI Agents Synthesize Scientific Conclusions?**, 2026-06 arXiv. [논문](https://arxiv.org/abs/2606.11337).

체계적 문헌고찰에 기반한 대규모 결론 합성과 clean-room 평가를 제안한다. 시간·원문 접근·정답 노출을 통제해야 한다는 동기가 겹친다. 과학 결론 합성이나 오염 통제 자체를 새로운 기여라고 쓰지 않는다. 현재는 초록·저자 소개 중심으로 확인했다.

### R22. PreScience

Ajith et al., **PreScience: A Dataset and Benchmark for Scientific Forecasting**, v2 2026. [논문](https://arxiv.org/abs/2602.20459).

시간 cutoff를 존중한 과학 문헌·저자·인용 스냅샷과 미래 연구 관련 과제를 제공한다. 이번 제안의 시간 확장은 미래 예측보다 접근 가능한 근거의 시점별 결론에 해당한다. 시간 데이터셋이라는 이유만으로 독창성을 확보할 수는 없다.

### R23. Axioms for RAG

Merker et al., **Axioms for Retrieval-Augmented Generation**, ICTIR 2025. [저자 공개 논문](https://downloads.webis.de/publications/papers/merker_2025b.pdf), [저자 코드](https://github.com/webis-de/ir_axioms).

좋은 RAG 출력의 성질을 제약으로 정하고 평가에 사용하는 접근이다. PLACEBO에서 결론을 보존해야 한다는 성질도 일반적인 평가 원칙의 연장선에 있다. 새 이름의 consistency 지표가 아니라 그 성질을 과학 문헌의 유효한 사례에서 검증하는 일이 필요하다.

### R24. DISCERN

Huang et al., **DISCERN: Can AI Agents Work Like Scientists and Guide Discovery?**, 2026-09 arXiv. [논문](https://arxiv.org/abs/2609.33357).

데이터 무결성·분석 검증·가설 생성/수정에 대한 과학 agent 평가다. “증거에 따라 과학적 결론을 수정한다”는 넓은 동기가 겹친다. 본 제안은 실험 수행 전체가 아닌 고정 문헌 근거와 조건에 제한한다. 현재는 초록 확인 단계다.

## 3. 독창성을 확인하는 다음 작업

1. **AgentHop, SciNet, ResearchQA, SciConBench의 본문·부록·release schema를 정밀 비교**한다. 실제 조건 필드, 근거 변형, 대안 근거, 유보, paired 지표의 존재를 행 단위로 기록한다.
2. RAGONITE·faithfulness 연구·SURE-RAG에서 제거/교체가 무엇을 식별하는지 비교한다. 일반적인 evidence intervention을 발명했다고 쓰지 않는다.
3. “논문 간 조건 적격성 + 대체 근거 검증 + 같은 질문의 변화/불변 대조” 중 선행연구에 없는 측정 요소와 이로 인해 발견되는 오류를 각각 제시한다.
4. 최근 논문을 매달 같은 검색식으로 확인하되, 논문에 쓰는 결론은 원문과 저자 자료로 검증한다. 검색 범위·날짜·제외 사유를 남긴다.
5. 같은 구성을 이미 충분히 제공하는 공개 benchmark가 발견되면, 단순 확장을 원천적 신규성으로 포장하지 않는다. 재현·평가 편향 감사 또는 과학 조건의 더 좁고 명확한 문제로 바꾼다.

재검색할 질의 예: `scientific literature evidence sufficiency benchmark`, `condition-aware scientific claim verification`, `cross-paper experimental comparability benchmark`, `counterfactual attribution evidence removal`, `scientific conclusion revision benchmark`.

**표절 방지와 연구 신규성은 별도 문제다.** 이 문서는 내용을 자체 서술하고 출처를 연결했지만, 문헌 조사가 끝났거나 아이디어의 절대적 비중복이 보장됐다는 증거는 아니다. 새 기여를 결정하기 전에 가장 가까운 연구의 실제 데이터와 실험을 대조해야 한다.
