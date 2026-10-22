# 저장소 검토: 무엇을 재사용하고 무엇을 새로 만들어야 하는가

기준: `ksyint/linkpaper_ksyint`의 `main`, **`beec4d7c6887f072d1f40b62c32e0db16895fe0d`**, 검토일 2026-10-22. 원격 `main`을 별도 clone한 뒤 연구 브랜치를 만들었다. 기존 로컬 `linkpaper/`는 upstream 저장소여서 작업 대상으로 바꾸지 않았다.

## 1. 검토 범위와 결론

**현재 레포의 가장 직접적인 연구 자산은 인덱싱과 평가 하네스다. 완성된 온라인 GraphRAG QA 서비스나 검증된 논문용 데이터셋이 있는 상태는 아니다.**

전체 추적 파일 목록 228개를 확인하고 파일별 크기·행 수·SHA-256을 [inventory](repository_inventory.tsv)에 기록했다. UTF-8 텍스트 225개, 바이너리 3개이며 Python 파일 134개는 AST 파싱과 구조 검사를 했다. 핵심 경로는 구현·설정·테스트를 연결해 상세 확인했고, 프런트엔드의 데이터 흐름, 문서·워크플로·배포 설정도 검토했다. 이미지 두 개는 시각적으로, DOCX는 내부 텍스트를 추출해 확인했다. lockfile은 의존성·빌드 재현 자료로 검토했다.

이것은 모든 기능의 실제 운영 검증이나 모든 코드 행의 형식 검증을 뜻하지 않는다. 운영 DB·실제 수집 코퍼스·외부 LLM 품질 평가에 대한 실행은 별도로 구분한다.

| 영역 | 추적 파일 수 | 확인한 역할 |
|---|---:|---|
| root | 5 | README, MIT LICENSE, env 예시, gitignore, compose |
| `.github/` | 1 | 평가 unit·smoke·Ragas·ontology workflow |
| `backend/` | 47 | FastAPI 경계, Neo4j/Qdrant 조회, 서비스·파이프라인 뼈대 |
| `docs/` | 11 | 요구사항·그래프·검색·평가·합성 benchmark·프런트엔드 설계 |
| `evaluation/` | 70 | 샘플·외부 benchmark·testgen·타깃·지표·리포트·테스트 |
| `frontend/` | 46 | React/Vite UI, 목업, SSE client, 상태 관리·스타일·lockfile |
| `indexing/` | 46 | 수집·PDF 변환·청킹·정규화·그래프·벡터 적재·테스트 |
| `scripts/` | 2 | 일일 인덱싱 wrapper와 설명 |

실제 원본 데이터 규모로 확인한 것은 **fixture 16개 청크 / 논문 ID 5개**, retrieval 샘플 12개, generation 8개, extraction 8개다. 이 샘플들로 대규모 시스템 품질을 주장할 수 없다. 문서에 등장하는 월별 배치 계획과 실제 배포 코퍼스 규모를 혼동하지 않는다.

## 2. 이미 구현된 가치 있는 부분

### 2.1 오프라인 인덱싱

- [`hf_client.py`](../../../indexing/data_pipeline/hf_client.py): 일일 논문·기간 수집, 중복 제거, 페이지 처리, 재시도.
- [`preprocessor.py`](../../../indexing/data_pipeline/preprocessor.py): arXiv PDF 다운로드와 PyMuPDF4LLM 변환. 다운로드 오류·지연을 다룬다.
- [`chunker.py`](../../../indexing/data_pipeline/chunker.py): 섹션 경계, 제목 노이즈 정리, references 구별, 해시 기반 chunk ID.
- [`metadata_curator.py`](../../../indexing/data_pipeline/metadata_curator.py): 참고문헌의 명시적 arXiv ID 추출.
- [`ids.py`](../../../indexing/indexing_common/ids.py): Paper/Chunk 공통 ID 정규화.
- [`graph_builder/builder.py`](../../../indexing/graph_builder/builder.py): 논문 단위 Neo4j transaction과 Paper·Chunk·Author·CITES 적재.
- [`vector_builder/builder.py`](../../../indexing/vector_builder/builder.py): 공통 ID 기반 Qdrant point, reference 청크 제외, 임베딩 출처.
- [`job.py`](../../../indexing/indexing_job/job.py): graph 적재 후 vector 적재, 논문 단위 실패 기록.

연구 재사용 가치는 문헌을 모으고 검색 단위로 연결하는 배관에 있다. 현재 구조 그래프가 과학적 지지·반박 관계를 제공한다고 해석해서는 안 된다.

### 2.2 평가 및 합성 데이터 배관

- [`schemas.py`](../../../evaluation/src/linkpaper_eval/schemas.py): 검색·생성·추출의 공통 계약.
- [`runner.py`](../../../evaluation/src/linkpaper_eval/runner.py): 시스템 실행, 지표, 사례별 결과·근거 저장.
- [`benchmark/`](../../../evaluation/src/linkpaper_eval/benchmark): QASPER, MultiHop-RAG, GraphRAG-Bench, local 변환과 준비.
- [`testgen/pipeline.py`](../../../evaluation/src/linkpaper_eval/testgen/pipeline.py): 코퍼스·그래프·설정·해시·버전을 묶은 생성 산출물과 snapshot 재사용.
- [`testgen/export.py`](../../../evaluation/src/linkpaper_eval/testgen/export.py): Ragas 근거의 ID/텍스트 일치 검사와 불완전 사례 제외.
- [`testgen/ragas_engine.py`](../../../evaluation/src/linkpaper_eval/testgen/ragas_engine.py): 실제 Ragas 알고리즘을 사용하는 single/multi-hop 생성 경로.
- [`targets/vector_rag.py`](../../../evaluation/src/linkpaper_eval/targets/vector_rag.py): Qdrant 검색 후 독립 답변 모델 사용, 미검색 인용 거부, 임베딩 서명 검사.
- [`gates.py`](../../../evaluation/src/linkpaper_eval/gates.py), [`report.py`](../../../evaluation/src/linkpaper_eval/report.py): 회귀 gate, 태그·실패·사례 리포트.

특히 snapshot 재생성, 해시 불일치 검출, 원래 입력 보존, 근거 매핑 실패를 테스트하는 부분은 연구 재현성의 좋은 출발점이다. 다만 저장소 snapshot은 논문이 역사적 특정 시점에 공개한 원문 버전의 archive와는 다르다.

## 3. 논문 준비를 막는 실제 간극

| 우선순위 | 발견 | 코드 근거 | 연구에 미치는 영향·후속 조치 |
|---|---|---|---|
| P0 | 온라인 retrieval/generation은 `pass`, QA pipeline은 생성자 중심 | [retrieval service](../../../backend/src/linkpaper/modules/retrieval/service.py#L1), [generation service](../../../backend/src/linkpaper/modules/generation/service.py#L1), [QA pipeline](../../../backend/src/linkpaper/pipelines/question_answering.py) | 실행형 benchmark는 독립 evaluator로 먼저 구축. 제품 완성에 종속시키지 않음 |
| P0 | 논문 검색·분석·대화 route가 501 반환 | [papers routes](../../../backend/src/linkpaper/api/routes/papers.py#L20), [conversation route](../../../backend/src/linkpaper/api/routes/conversations.py#L30) | HTTP target이 완성된 QA를 평가하는 상태가 아님 |
| P0 | 프런트엔드 기본값은 mock | [API switch](../../../frontend/src/api/index.js#L7) | 데모·빌드 성공을 연구 답변 성능으로 사용하면 안 됨 |
| P0 | 평가 타깃이 gold를 담은 `EvalCase` 전체를 받음 | [target interface](../../../evaluation/src/linkpaper_eval/targets/base.py#L21), [EvalCase](../../../evaluation/src/linkpaper_eval/schemas.py#L49) | 기존 vector 타깃의 무참조 생성은 테스트되지만 계약상 누출 방지는 아님. 새 `TaskInput`/`GoldRecord` 분리 |
| P0 | 하나의 flat gold chunk 목록, paired 환경·조건·대안 근거·유보 verdict 없음 | [schemas](../../../evaluation/src/linkpaper_eval/schemas.py) | 버전 있는 연구 계약과 주장별 충분 근거 집합이 필요 |
| P0 | 현재 품질 집계는 실패 사례에 지표를 만들지 않음 | [runner](../../../evaluation/src/linkpaper_eval/runner.py#L113), [aggregate](../../../evaluation/src/linkpaper_eval/metrics/__init__.py#L33) | 오류율은 보고하지만 품질 평균은 성공 사례 중심이 될 수 있음. 논문 주 지표는 실패를 포함한 분모 사용 |
| P0 | `source_version`은 PDF/Markdown 확보 경로이고 arXiv 논문 버전이 아님 | [models](../../../indexing/data_pipeline/models.py#L56), [reference version stripping](../../../indexing/data_pipeline/metadata_curator.py#L90) | v1/v2·버전 공개 시각·원문 해시를 새로 보존. 단순 날짜 필터로 역사 평가 불가 |
| P0 | 재적재는 과거 청크·인용을 교체하고 PDF 중간 산출물은 삭제 | [stale chunk deletion](../../../indexing/graph_builder/builder.py#L73), [citation replacement](../../../indexing/graph_builder/builder.py#L128), [preprocessor](../../../indexing/data_pipeline/preprocessor.py) | 불변 source archive와 benchmark snapshot을 별도로 둬야 함 |
| P1 | CITES는 ID 관계이며 근거 속성이 없음. 의미 Entity/Triple 추출은 후속 계획 | [graph builder 설명](../../../indexing/graph_builder/builder.py#L3), [citation comment](../../../indexing/graph_builder/builder.py#L341) | CITES·유사도·공유 엔티티를 과학적 지지·한계 해결 정답으로 사용하지 않음 |
| P1 | 참고문헌에서 명시적 arXiv ID만 추출 | [curator](../../../indexing/data_pipeline/metadata_curator.py) | DOI·다른 출판 형태 누락. 실제 인용 그래프 coverage를 수동 감사 |
| P1 | 부록 기본 제외, 큰 섹션 청킹 | [config](../../../indexing/data_pipeline/config.py#L45), [appendix filter](../../../indexing/data_pipeline/chunker.py#L245) | 실험 조건·추가 결과가 빠질 수 있음. 근거 archive는 부록·표·캡션 보존 |
| P1 | hybrid는 추출식 답변, vector는 LLM 답변 | [hybrid target](../../../evaluation/src/linkpaper_eval/targets/graphrag_hybrid.py), [vector target](../../../evaluation/src/linkpaper_eval/targets/vector_rag.py) | 생성 성능 비교 시 동일 LLM과 프롬프트·토큰·근거 예산을 사용 |
| P1 | hash embedding이 여러 경로의 기본값 | [embedding config](../../../evaluation/src/linkpaper_eval/stores/config.py#L101), [hybrid config](../../../evaluation/configs/hybrid.yaml) | 배관 점검에 유용하나 learned retrieval 품질 결과와 구분 |
| P1 | 어휘 groundedness·인용 ID 존재는 과학적 지지 판정이 아님 | [generation metrics](../../../evaluation/src/linkpaper_eval/metrics/generation.py), [heuristic judge](../../../evaluation/src/linkpaper_eval/judges.py) | 조건·부정·수치·함의 평가 및 human/judge meta-evaluation 추가 |
| P1 | 생성 JSON의 추가 연구 필드가 조용히 버려질 수 있음 | [extra ignore](../../../evaluation/src/linkpaper_eval/schemas.py#L52) | strict 연구 스키마와 필수 필드 validation 사용 |
| P1 | `TargetResponse.usage`가 있어도 CaseResult에는 usage가 없음 | [response/result contracts](../../../evaluation/src/linkpaper_eval/schemas.py) | 재현 가능한 token·비용·도구 호출 accounting을 연구 결과에 추가 |
| P2 | UI API 경로와 backend route 계약이 일치하지 않음 | [frontend client](../../../frontend/src/api/client.js), [backend router](../../../backend/src/linkpaper/api/router.py) | 주석 도구로 바꾸기 전에 계약 통일. benchmark 핵심과는 별도 |
| P2 | README badges·이미지·설계와 구현의 시점 차이 | [frontend package](../../../frontend/package.json), [pipeline image](../../../docs/data-architecture/data_pipeline.png) | 실제 package는 React 18/Vite 5 계열. 이미지의 Markdown 우선 경로는 현 PDF 전용 구현과 다름 |

P0/P1은 이 연구를 시작하기 위한 우선순위다. 이번 문서 작업에서 위 문제를 수정한 것으로 주장하지 않는다. 기존 CI의 회귀 검사용 선택과, 논문용 측정 계약의 요구가 다른 부분도 있다.

## 4. 실행해 확인한 사항

검증은 원본 코드에 대해 별도 임시 Python 환경에서 수행했다. 주요 버전은 Python **3.12.4**, pytest **8.4.2**, Pydantic **2.14.1**, Qdrant client **1.19.1**, Neo4j driver **6.4.1**, Ragas **0.3.9**다. 프로젝트 CI의 Python 3.11과 동일 환경을 재현한 것은 아니다.

| 검증 | 결과 | 한계 |
|---|---|---|
| `backend`: `python -m pytest -q` | **9 passed** | 주로 health·조회 서비스의 fake driver 검증 |
| `indexing`: `python -m pytest -q -rs` | **86 passed, 1 skipped** | 실제 저장소 integration은 opt-in이라 미실행 |
| `evaluation`: Ragas 포함 `python -m pytest -q -rs` | **113 passed, 2 skipped** | 아래 skip 사유 참조 |
| local benchmark prepare/run | **성공** | fixture 16청크/5논문, retrieval 12사례의 배관 점검 |
| offline testgen 20개 생성→snapshot 재생성→`cmp` | **바이트 단위 일치** | 템플릿 생성. 과학 질문 품질 검증이 아님 |
| frontend frozen install + production build | **성공** | mock 기본값 UI 정적 빌드. backend 통합 검증 아님 |

Python 최종 합계는 **208 passed, 3 skipped**다. evaluation skip은 (1) Ragas 미설치 상황 전용 테스트가 실제 설치 환경이라 제외, (2) 실제 Docker Neo4j integration opt-in 미설정이다. indexing skip은 실제 Neo4j/Qdrant integration opt-in 미설정이다. Ragas의 LangChain wrapper 관련 deprecation warning 2개는 있었고 테스트 실패는 없었다.

처음에는 Ragas 없이 evaluation을 실행해 `103 passed, 4 skipped`를 확인했고, 이후 선택 의존성을 설치해 위 최종 결과를 얻었다. 두 실행의 테스트 수를 더하지 않는다. Ragas 테스트는 scripted provider를 사용하므로 유료 원격 모델의 생성 품질을 검증한 것이 아니다.

프런트엔드는 설치된 pnpm이 없어 `npx pnpm@9.15.9`를 사용했다. 일반 install은 `pnpm-workspace.yaml`의 packages 필드 부재로 실패했고, `--ignore-workspace`를 지정해 기존 lockfile을 바꾸지 않고 설치·빌드했다. 이 호환성 문제의 구현 수정은 이번 작업에 포함하지 않았다.

재실행 예시:

```bash
# 레포 root, 별도 가상환경 사용
uv venv /tmp/linkpaper-research-audit
uv pip install --python /tmp/linkpaper-research-audit/bin/python \
  -e 'evaluation[dev,stores,ragas]' -e 'backend[dev]' -e 'indexing[dev]'

# 각 package 디렉터리에서
/tmp/linkpaper-research-audit/bin/python -m pytest -q -rs

# frontend/에서
npx --yes pnpm@9.15.9 install --ignore-workspace --frozen-lockfile --ignore-scripts
npx --yes pnpm@9.15.9 --ignore-workspace run build
```

```bash
# evaluation/에서, PATH에 위 가상환경의 bin을 추가한 뒤
linkpaper-eval bench prepare --name linkpaper-local
linkpaper-eval bench run --name linkpaper-local --suite retrieval \
  --run-id research-audit --quiet
linkpaper-eval testgen --source jsonl --corpus fixtures/mock_corpus.jsonl \
  --engine offline --size 20 --out /tmp/linkpaper-research-audit/smoke.jsonl
linkpaper-eval testgen-regenerate \
  --manifest /tmp/linkpaper-research-audit/smoke.manifest.json \
  --out /tmp/linkpaper-research-audit/regenerated.jsonl
cmp /tmp/linkpaper-research-audit/smoke.jsonl \
  /tmp/linkpaper-research-audit/regenerated.jsonl
```

생성 경로가 이미 있으면 다른 출력명을 사용한다. 위 명령은 실제 논문 수집·유료 추론·운영 DB 적재를 수행하지 않는다. 설치 버전 범위가 넓어서 미래 재실행은 현재 환경과 달라질 수 있으며, 논문 실행 전에는 별도의 고정 환경을 배포해야 한다.

## 5. 문서와 코드로 아직 알 수 없는 것

- 실제 배포된 코퍼스의 논문 수·주제 분포·라이선스·버전·PDF 변환 오류율.
- 운영 Neo4j/Qdrant에 의도한 schema와 embedding signature가 일치하는지.
- 실제 사용자 질문 분포, 연구자가 중요한 오류라고 판단하는 기준.
- 전문가 주석 인력의 가용성과 필수·대체 근거 판정의 재현성.
- 모델별 성능·비용과 LINK-DELTA의 추가 진단 가치.

이 정보는 코드만 읽어 추정한 숫자로 채우지 않는다. 이번 커밋은 연구 문서·inventory·README 탐색 링크만 추가하며, 새로운 benchmark 구현이나 수집 결과가 있는 것처럼 표현하지 않는다.
