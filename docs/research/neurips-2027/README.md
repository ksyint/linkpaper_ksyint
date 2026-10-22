# LinkPaper → NeurIPS 2027 연구 구상

작성 기준: **2026-10-22**, 원본 검토 커밋 [`beec4d7`](https://github.com/ksyint/linkpaper_ksyint/tree/beec4d7c6887f072d1f40b62c32e0db16895fe0d).

추천은 **LINK-DELTA: Benchmarking Condition-Aware Evidence Revision in Scientific Literature QA**라는 가제의 벤치마크다. 논문 여러 편을 찾는 능력에서 한 걸음 더 나아가, **주장이 성립하는 실험 조건과 필요한 근거를 구별하고, 근거가 바뀌면 결론을 적절히 수정하는 능력**을 측정한다.

현재 단계는 연구 제안이다. 실제 벤치마크 데이터, 전문가 라벨, 모델 성능 결과는 아직 없다. 아래 규모·예산·성공 기준은 실행을 위한 제안값이며, 독창성 및 채택 가능성이 검증됐다는 뜻이 아니다.

후속 구현으로 **텍스트 전용 LLM 실험 코드**를 추가했다. GPT·Claude·Gemini API, 로컬 CausalLM 자동 로드, GPU 6 제한, 네 환경 생성·격리 실행·재개·묶음 진단·의미 검수 재채점을 지원한다. 실행 방법과 현재 구현 범위는 [evaluation/RESEARCH.md](../../../evaluation/RESEARCH.md)를 참조한다. 포함된 8개 가상 사례는 배관 검증용이며 과학적 성능 결과가 아니다.

| 문서 | 내용 |
|---|---|
| [PROPOSAL_KO.md](PROPOSAL_KO.md) | 추천 아이디어, 대안 비교, 과제 정의, 데이터·지표·실험·논문 구성 |
| [RELATED_WORK.md](RELATED_WORK.md) | 직접 확인한 1차 출처, 가까운 선행연구와 중복 위험, 추가 검증 사항 |
| [REPOSITORY_AUDIT.md](REPOSITORY_AUDIT.md) | 구현과 설계의 구분, 코드 근거, 재사용 가능 자산, 실행 점검 결과 |
| [ROADMAP.md](ROADMAP.md) | 2주 파일럿, 2027년 준비 일정, 인력·비용 산식, 진행/전환 기준 |
| [repository_inventory.tsv](repository_inventory.tsv) | 검토 시점의 전체 추적 파일 228개에 대한 크기·행 수·해시 목록 |

2026년 공식 트랙 명칭은 기존 Datasets & Benchmarks에서 **Evaluations & Datasets**로 바뀌었다. 같은 NeurIPS proceedings에 수록되고 main track과 함께 발표하지만, 기관별 실적 분류까지 자동으로 같다는 의미는 아니다. 2027년 공식 CFP와 마감일은 이번 조사에서 확인하지 못했다. 연구 일정은 내부 목표이며 2027년 공고에 맞춰 갱신해야 한다. [2026 CFP](https://neurips.cc/Conferences/2026/CallForEvaluationsDatasets), [공식 FAQ](https://neurips.cc/Conferences/2026/EvaluationsDatasetsFAQ).

가장 먼저 할 일은 모델 개발보다 **실제 논문에서 조건 차이와 필수 근거를 명확하게 판정할 수 있는 질문 30개를 손으로 만드는 것**이다. 그 라벨이 재현되지 않으면 데이터 규모를 늘려도 좋은 벤치마크가 되기 어렵다.
