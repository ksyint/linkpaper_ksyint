# LinkPaper 원본·포크 전체 브랜치 및 파일 감사

기준: 2026-11-02. 원본 `linkmind-ai/linkpaper`와 포크 `ksyint/linkpaper_ksyint`의 원격 heads를 모두 fetch한 스냅샷이다. 새 작업 브랜치를 만들기 전의 상태이며 원격 저장소는 변경하지 않았다.

## 조사 범위와 증거

- 원본 10개 브랜치, 포크 2개 브랜치: 총 12개.
- 브랜치별 tracked 파일 항목 2,362개. 같은 내용의 파일은 blob SHA로 중복 제거하면 381개, 2,890,924바이트다.
- 226개 서로 다른 Python blob을 전부 AST 파싱했다. 나머지 텍스트 151개는 UTF-8 디코딩·구조 목록화하고 JSON/JSONL은 문법 확인했다. 파싱 오류는 없었다.
- 바이너리 4개는 PNG 3개(크기·형식)와 DOCX 1개(문단 추출)다. lock·SVG 등 생성 산출물도 파일 목록에는 포함했다.
- 전 파일의 존재·크기·내용 식별 및 자동 구조 검사를 빠짐없이 수행했다. 기능 해석은 실제 실행 경계, 평가·구축 코드와 브랜치 변경분을 중심으로 직접 검토했다. AST 통과가 런타임·서비스 통합·과학적 정확성을 입증하지는 않는다. 이미지 전체에 대한 수동 판독이나 유료 모델 실험은 이 감사에서 수행하지 않았다.
- 두 저장소 모든 브랜치에 `AGENTS.md`는 없었다.

첨부 산출물:

| 파일 | 내용 |
|---|---|
| `branches.json` | 저장소·브랜치별 commit/tree SHA, 파일 수·크기, main 대비 ahead/behind |
| `branch_files.csv` | 모든 브랜치의 모든 tracked 경로·blob SHA·mode·type·size |
| `blob_analysis.json` | blob별 출현 브랜치·경로, Python 함수/클래스·import·stub, 문서 제목, JSON 행 수, 이미지 메타데이터·DOCX 문단 |
| `inventory_summary.json` | 전체 범위·시각·파싱 결과 |
| `generate_inventory.py` | 같은 감사 복제본에서 목록을 재생성하는 스크립트 |

## 브랜치별 상태

| 저장소 | 브랜치 | commit | 파일 수 | 해석 |
|---|---|---|---:|---|
| upstream | main | `beec4d7c6887f072d1f40b62c32e0db16895fe0d` | 228 | 현재 기준 트리 |
| upstream | 1019 | `8d745e06de3f55cc4e908d21e9011351129d17f6` | 228 | main과 파일 트리 동일. main merge commit과 이력만 다름 |
| upstream | 1016 | `1800d443299de876bfb20328be50b472bac2f3ff` | 224 | 평가 지표·회귀 게이트 보강 작업. main 대비 main-only2/branch-only1이므로 단순 최신 브랜치로 간주하면 안 됨 |
| upstream | benchmark | `1666aa05178f7f3affce6cb148ad14b7361f877a` | 191 | 초기 외부 벤치마크 registry/converter 기반, 이후 main에 통합된 오래된 상태 |
| upstream | data-pipeline | `3bb34aec928c0f352d96ea27d4d9c7080634e009` | 219 | HF Daily Papers·PDF 전처리·일별 수집. main의 선조 |
| upstream | evaluation | `74e0bea731e24d041e0355bfad9c2187d5ade8da` | 90 | 초기 평가 패키지. main의 선조 |
| upstream | feat/pipline | `de2a3a3ca2c5cba3a85e955fc86f0a5efe6a19b8` | 231 | main에 없는 2개 commit. 온라인 단일 논문 RAG와 OpenAI SSE를 구현한 별도 경로 |
| upstream | frontend | `dba8acd0e6b50c3ac428caa6a7e3daaa24377fd9` | 138 | React 목업 UI. main의 선조 |
| upstream | graph_vector_builder | `8b49540030446fd89434e23336b115f247a74d3a` | 217 | 오프라인 Neo4j/Qdrant 구축·온라인 읽기. main의 선조 |
| upstream | neo4j-schema-dev | `083b0d05f7fba3c8aa7d1ecb4ca132737aeb44d2` | 115 | 그래프 스키마·벡터 구조 문서의 초기 상태. main의 선조 |
| fork | main | `beec4d7c6887f072d1f40b62c32e0db16895fe0d` | 228 | upstream main과 commit·tree 동일 |
| fork | research/neurips-2027-benchmark-proposal | `bd1c07675cdc170fd9dd8192105031f81e29a54d` | 253 | main 이후 2개 commit, 30개 파일 변경·4,118줄 추가. 기존 LINK-DELTA 제안 및 텍스트 LLM 평가 구현 |

원본 main tree SHA는 `e5a41bbb260667a45cf82149275a61a35461035f`다. 원본 1019 및 포크 main도 동일하다. 가장 큰 숫자의 브랜치나 가장 최근의 이름을 무조건 병합하지 말고 목적별 변경을 선택해야 한다.

## main의 실제 구현 상태

### 백엔드: 서비스 골격과 실제 조회 계층이 혼재

근거: `backend/README.md`, `backend/src/linkpaper/api/routes/{papers,conversations}.py`, `pipelines/{paper_analysis,question_answering}.py`, `modules/{generation,retrieval}/service.py`.

- health를 제외한 main의 사용자 라우트는 HTTP501이다. 질문응답·논문 분석 pipeline에는 의존성 연결만 있고 실행 메서드가 없다.
- GenerationService, RetrievalService, OpenAIClient, PaperService, 대화 저장 등은 stub이다. 현재 main을 완성된 논문 agent 서비스로 소개하면 부정확하다.
- 반면 `modules/vector_read/`의 Qdrant 필터·임베딩 설정 검증, `modules/knowledge_graph/`의 Paper/Author/Chunk/CITES 조회와 스키마 검증은 구현되어 있다.
- main의 online layer는 인덱스 read를 의도하고, PDF 처리·임베딩·DB write는 indexing에 분리했다. 벤치마크 생성 시 online service와 offline corpus build의 책임을 유지하는 편이 낫다.

### indexing: 재사용 가치가 높은 실제 자산

근거: `indexing/data_pipeline/{hf_client,preprocessor,chunker,metadata_curator,models,pipeline}.py`, `graph_builder/builder.py`, `vector_builder/{builder,embedding}.py`, `indexing_job/`.

- HF Papers 날짜별 메타데이터 수집·재시도·중복 제거, arXiv PDF 확보/Markdown 변환, 섹션·문자 길이 기반 청킹과 content hash가 있다.
- 문서 계층은 Paper·Author·Chunk, HAS_CHUNK·NEXT_CHUNK·AUTHORED_BY·CITES다. Entity constraint가 존재해도 의미 Entity/Triple 추출이 완성됐다는 뜻은 아니다. builder docstring이 후속 extractor 연결을 명시한다.
- 저자 이름 정규화와 논문·순서를 포함한 provisional ID는 동명이인 무조건 병합을 피한다.
- Qdrant point ID는 chunk ID에서 결정적으로 생성하고 payload에 embedding provider/model/dimension/version을 남긴다.
- `source_version`은 `hf-markdown`/`pdf-pymupdf4llm`인 **파싱 경로**다. arXiv v1/v2 같은 논문 버전과 혼동하면 시간·버전 벤치마크가 잘못된다.
- `CITES`는 서지 연결이며 지지·반박·재현성 또는 독립 실험의 GT가 아니다. 새 agent 과제의 과학 관계는 별도 수작업 검수와 span 위치가 필요하다.

### evaluation: 새 연구 구현의 권장 진입점

근거: `evaluation/src/linkpaper_eval/{schemas,runner,config,gates,report}.py`, `targets/`, `testgen/`, `benchmark/`, `.github/workflows/evaluation.yml`.

- 설정·데이터 SHA, git SHA, case별 근거·응답, 오류와 지표 저장, 회귀 게이트, 오프라인 CI가 있다.
- 현재 sample JSONL은 retrieval12, generation8, extraction8, mock corpus16행이다. 실데이터 성능 결과가 아니다.
- `LexicalBaselineTarget`는 BM25와 상위 첫 문장 추출이다. `GraphRagHybridTarget`는 Qdrant 검색·인용 확장 뒤 역시 추출식 답변이다. `VectorRagTarget`만 별도 답변 모델을 호출한다. 생성기가 다른 타깃의 생성 점수를 그대로 비교해 GraphRAG 우월성으로 해석하면 안 된다.
- `EvalCase`에 gold_answer/gold_chunk_ids 등이 있고 SUT의 `run(case)`가 이 객체 전체를 받는다. 기존 타깃의 현재 구현이 gold를 사용하지 않더라도 자유 agent에 그대로 넘기면 gold 격리 계약이 아니다. 새 agent API는 public task DTO를 따로 둬야 한다.
- Ragas testgen·frozen snapshot 재생성과 실제 알고리즘 contract tests가 있다. offline template generator는 자체적으로 어휘 편향·배관 테스트 전용임을 명시한다. template fixture 성능을 논문 결과로 포장하면 안 된다.
- 외부 registry에 QASPER·MultiHop-RAG·GraphRAG-Bench가 포함된다. registry의 라이선스 문자열은 코드에 작성된 설명이며 원천 데이터의 현재 권리 조건 검증을 대체하지 않는다.
- CI는 evaluation 경로만 trigger하는 설계다. backend·indexing 변경에 대한 전체 제품 통합 보장은 별도 필요하다.

### frontend: 목업과 계약 불일치

근거: `frontend/src/api/{index,client,mockClient}.js`, `frontend/src/store/useChatStore.js`, `frontend/package.json`, `docs/frontend_fuction_list.{md,docx}`.

- 기본은 `VITE_USE_MOCK !== 'false'`이므로 목업이다.
- 실제 client가 요청하는 `/api/papers/search`, `/api/chat/stream`와 main backend의 `/api/v1/...`가 맞지 않는다.
- React18/Vite5인 package.json과 README의 React19.2/Vite8.1 배지가 일치하지 않는다. 발표 문서의 스택은 실제 lock/config로 확인해야 한다.
- 새 agent benchmark는 현재 프런트엔드에 의존하지 않는 평가 CLI로 먼저 완결하는 편이 빠르고 재현 가능하다. 추후 사람 주석·trajectory audit UI로 확장할 수 있다.

## feat/pipline의 별도 가치와 제한

근거: `docs/pipeline-development.md`, `backend/src/linkpaper/modules/online_retrieval/`, `adapters/papers/huggingface_markdown.py`, `api/routes/chat.py` (해당 branch SHA).

- HF 논문 Markdown을 받고 메모리 청크·OpenAI embedding으로 검색한 뒤 Responses API SSE를 내보내는 실제 구현이다.
- 단일 논문 인덱스를 공유하고 다른 논문 요청 때 교체한다. 다중 사용자·worker 캐시 격리, PDF fallback, citation 이벤트, 실제 GraphRAG는 아직 미구현이라고 문서가 명시한다.
- 이 브랜치를 최신 main에 통째로 덮어쓰면 이후 indexing/evaluation 작업을 잃는다. 필요한 인터페이스·테스트를 선택적으로 재사용할 수는 있으나 새 benchmark의 핵심은 고정 세계와 공정한 agent 도구 환경이다.

## 기존 포크 연구 브랜치의 안전한 재사용 범위

근거 commit: `bd1c07675cdc170fd9dd8192105031f81e29a54d`, 경로 `evaluation/src/linkpaper_eval/research_bench/` 및 `docs/research/neurips-2027/`.

- LINK-DELTA는 **영문 ML 논문 근거의 조건 보존과 근거 변경 반응**을 제안한다. 주 구현은 모든 contexts를 바로 제공하는 텍스트 LLM 근거 패킷 평가이며 agent 도구 환경은 아니다.
- 현재 2개 가상 질문×4세계=8개의 fixture다. real-science annotation, Korean benchmark, 논문용 실험 결과는 아직 없다.
- strict 입력/gold DTO 분리, evidence hash, 버전·라이선스 필드, 대안 충분근거 집합, 결정적 논문/계보 분할 검사, opaque task별 citation ID, 독립 호출, 실패 포함 분모, response-hash semantic review, 계보 bootstrap은 유용하다.
- GPT Responses/Claude Messages/Gemini generateContent/OpenAI-compatible/local CausalLM adapter와 재개 manifest가 있다. 새 benchmark용의 모델 능력 결과로 볼 수는 없다.

### 새 연구로 전환할 때 보완할 점

1. `search/open/citations` 같은 예산 제한 도구와 실제 action/observation trajectory가 필요하다. public task에 허용 문서 전체를 넣은 packet score와 tool-agent score를 분리한다.
2. 기본 FULL/CUT/PLACEBO/SCOPE builder는 CUT/SCOPE를 항상 insufficient로 고정한다. 세계 라벨을 숨겨도 문서 수·길이 차이와 판정 prior가 shortcut이 될 수 있다. 문서 수·길이·정답 분포의 counterbalance와 blind/prior-only 대조군을 설계해야 한다.
3. 현재 split 검사는 결정적 논문은 보호하지만 background/SCOPE 추가 논문의 모든 ID·버전까지 격리하지 않는다. 완전 독립 분할을 주장한다면 모든 관련 논문을 검사하고 예외 정책을 공개한다.
4. citation validity는 보이는 ID인지의 구조 검사다. 빈 claims에서 `all([])`은 참이고, sufficient set도 claim별 entailment를 보장하지 않는다. 기존 문서도 semantic review 전 diagnostic으로만 해석한다. 새로운 점수에서 이름만 바꿔 과학적 정답률로 쓰면 안 된다.
5. agent가 파일/웹 도구를 받는다면 gold와 public data를 같은 로컬 경로에 둔 것만으로 격리가 보장되지 않는다. 모델에 노출되는 도구 allowlist와 반환 스키마에서 evaluator-only 정보가 빠지는지 검증한다.
6. 한글 질문만 번역해 붙이면 언어 기여가 약하다. 한국어 실제 연구자 질의·용어 혼용·원문 검색·논문 버전/조건/계보 판정의 난점을 별도 라벨링하고 한영 paired 조건에서 비교해야 한다.

## 원전·라이선스·공저자 처리

- 원본 `LICENSE`는 MIT이고 copyright owner는 linkmind-ai다. 기존 license·저작권 표시를 유지한다.
- `docs/PROJECT_SPEC.md`는 AlphaXIV-Open을 base project로 명시하고 README도 참고 저장소를 링크한다. 새 구현·논문에서 그 출발점과 기존 GraphRAG/RAG 요소를 인정하고 새 기여와 분리한다.
- 오픈소스 MIT와 논문 PDF/벤치마크 데이터의 재배포 권한은 별개다. 논문별 source URL, 논문 버전, 본문 hash, 접근/라이선스 증거가 필요하다.
- README의 공개 팀 명단은 김수용·정상헌·김대건·남두현·오창원·홍예린이다. 이번 사용자 지정에 따라 김수용1저자와 나머지 공저자 무순위를 적용하되 기존 서비스 직무를 새 연구 작업 배분의 고정 조건으로 삼지 않는다.
- 이 감사는 코드 출처를 추적했지만 외부 전체 저장소와의 정량 코드 유사도 검사를 완료한 것이 아니다. 절대적 비표절을 증명했다는 표현은 사용할 수 없다. 각 아이디어·도구·데이터의 기존 출처를 기록하고 독자 작성·검증 이력을 남겨야 한다.

## 권장 구현 경계와 검증

`evaluation/src/linkpaper_eval/agent_bench/`를 별도 모듈로 둔다. 기존 product backend와 분리해, frozen corpus + public task + evaluator-only gold + tool trace + response-bound reviews를 명확히 한다. SUT는 public task와 허용 도구 반환값만 받는다. 검색/열기/인용 탐색마다 호출 수·관측 문자 예산을 집계하고 잘못된 action/미열람 citation/예산 초과/실행 오류도 분모에 남긴다.

필수 검증은 실제 코드 경계를 겨냥한다: gold 비노출, open하지 않은 인용 거부, 알 수 없는 도구·예산 초과 거부, seed/세계 격리 재현성, 모든 논문 버전의 split 충돌, 빠진 prediction·agent error의 실패 집계, fixture publication gate, 응답 hash와 semantic review 결합. 이들은 벤치마크 시스템 검증이며 새로운 실제 데이터·인간 상한·여러 LLM의 본 실험을 대체하지 않는다.

감사 결과 main과 포크의 기존 기반은 재사용 가치가 있다. 다만 현재 상태를 완성된 한국어 연구 agent benchmark나 1티어 채택이 입증된 연구로 소개할 근거는 없다. 차별적인 측정 문제, 독립 제작·검수한 실데이터, 공정한 agent 관측/예산, 인간 검수와 실패 분석을 실제 실험으로 뒷받침해야 한다.
