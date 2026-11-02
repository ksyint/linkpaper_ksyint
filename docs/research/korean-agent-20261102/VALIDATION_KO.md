# 실제 실행한 검증

2026-11-02, Python3.12 격리 환경에서 단위·계약 검사를 CPU로 실행했다. 일반 학술 QA·획득 실패 mask·외부 논문 획득/live loop·replay와 의미 gate까지 추가한 최종 검증은 아래 **336개 통과**다. 새 코드의 실제 arXiv 검색·PDF 수집·열람 경로도 scripted policy로 확인했다. 이번 v2 검증에서 모델·GPU·유료 API는 실행하지 않았다. 별도의 과거 Qwen3-0.6B GPU3 실행은 당시 코드의 역사적 기록으로 구분한다.

```bash
CUDA_VISIBLE_DEVICES='' LINKPAPER_TEST_DOCKER_NEO4J=0 uv run --project evaluation --frozen --extra dev --extra stores --extra acquire python -m pytest -q evaluation/tests
# 336 passed, 4 skipped in 4.12s
bash scripts/run_korean_agent_demo.sh /path/to/new/output
# Integrated synthetic GLRS: lexical=1, blind=0 (not scientific performance).
```

4개 skip 항목은 설치하지 않은 Ragas의 module/contract 검사들과 opt-in Docker Neo4j 통합 검사다. Qdrant embedded/store 의존성은 설치하여 해당 CPU 검사를 실행했다. 새 agent/bridge/policy/metric 단위 검증은 skip되지 않았다. 사용자가 선택한 GPU index/UUID 격리·기존 할당 범위 검사는 mock NVIDIA/torch로 검증했다. 단위 검사에서는 실제 GPU를 할당하지 않았다. 별도 실제 GPU3 모델 smoke는 아래 기록을 따른다.

## fixture에서 관측한 값

| 가상 자료/정책 | 관측 | 해석 |
|---|---:|---|
| 기존 agent fixture lexical / oracle | structural_pass1.0 | 명시적 가상 표현을 읽는 heuristic/특권 양성 대조 |
| 기존 agent fixture blind | structural_pass0.0 | 읽지 않은 근거에 credit 없음 |
| metric 손계산 두 triplet | family macro0.5(1과0) | 누락 실패를 분모에 남긴 계산 예제 |
| 실제 도구 trace→GLRS lexical |1.0| 정확한 가상 result partition+획득+반응 경로 |
| 실제 도구 trace→GLRS blind |0.0| 미열람/무근거 주장이 점수로 바뀌지 않음 |
| 새 scholarly_qa 7문항 oracle / blind | structural_pass1.0 /0.0 | 6유형·단일/다중 근거·대안 충분집합의 합성 계약 검증 |

모든 fixture의 scientific_semantic_accuracy는 null이다. 이 숫자들은 실제 모델·한국어 학술 능력·새 지표의 인간 타당성·main 학회 기여를 검증한 성능이 아니다. 역할/가용 정보가 다른 oracle과 일반 agent를 하나의 우승 순위로 합치지 않는다.

## 확인한 중요한 반례

- 충분한 대안 witness 하나만 정확히 찾은 경우를 불필요하게 감점하지 않음.
- 같은 unit을 여러 그룹으로 나누기/다른 unit 합치기, 가짜 cluster로 unit 수 맞추기, 기존 unit 재취득을 새 unit처럼 계산하기.
- 열지 않은 문헌 인용, 거짓 opened ID·tool observation, 누락/timeout/오류의 분모 보존.
- 모든 visible paper/version/result unit과 질문 언어 쌍의 split 누출.
- 작성자를 제외한 독립 reviewer metadata, fixture/draft/oracle의 publication/semantic-score gate.
- 같은 논문의 서로 다른 atomic record/locator와 matched record 수·source-paper 수의 구분.
- 질문 언어가 같아도 B/R/N의 원천 record 언어 수가 다른 경우 거부. record 언어 수가 같더라도 parent paper별 visible-record 언어 profile 분포가 다른 경우 거부. 선언된 metadata의 검사이며 본문 언어 자동 판별·과학적 동등성 인증이 아님.
- 일반 QA에서 verdict·그룹 강제 없음, task별 N/A 분모, 단답/숫자 reference 진단과 실제 의미 점수 구분.
- 의미상 올바른 답의 조건 별칭·서술이 private 필드명과 다르더라도 응답 검수로 판단. strict 조건 형식과 의미 gate 분리. 실제 열람/충분근거가 없는 응답은 사람 pass 기록만으로 통과하지 않음. 실패 자동0과 유효 응답의 의미 검수 대기를 구분하고, 대기 중 subset 평균을 보고하지 않음.
- private task/count/gold 비노출, 한 paper 복수 근거, 한 편/두 편 대안 충분집합, 확보 실패 `[]`와 원래 gold·예정 분모 보존.
- 실제 PDF text 추출과 parser 실패, 검색 반복 응답 순서, provider별 cache·원문/metadata hash, 예산·redirect·권리 미검증 상태.
- live 초기 catalog·search/fetch/local search/open 교차, 동적 근거 활성화, 미등록/미열람 인용·그룹 거부, response 검수 hash, strict replay.

추가로 새 소스의 Python3.11 문법 호환, bash 문법, git diff whitespace, 새 문서의 상대 링크를 검사했다. [validation_summary.json](validation_summary.json)에 source SHA와 합성 CLI 집계가 있다. 원천 언어 구성 보강 뒤 새 CPU run은 로컬 `evaluation/runs/bilingual-source-validation-20261102`에 있다. 이전 `evaluation/runs/korean-agent-validation-20261102`와 실제 HF smoke는 덮어쓰지 않았다. runs는 Git ignore 대상이다. CI의 korean-agent-smoke가 같은 스크립트를 CPU에서 재실행하고 artifact로 보관한다.

현재 bridge fixture는 B/R/N 모두 영어2·한국어2 record 및 paper profile로 맞췄다. 원천6개 전체는 영어4·한국어2이지만, 어느 쪽도 본 데이터의 영어 다수 비중이나 분야 대표성 검증이 아니다. 실제 HF smoke는 보강 전 R의 언어 구성이 달랐으며, [당시 기록](REAL_LLM_SMOKE_KO.md)에 차이를 명시했다. 보강 뒤 모델을 다시 실행하지 않았다.

## 아직 필요한 연구 검증

영어가 다수인 영어·한국어 다분야 실제 원천의 수작업 gold/초기 IAA·대체 근거·권리·source-family split, 실제 model snapshot 고정과 공정한 budget 실험, 전문가 metric meta-eval은 수행 전이다. [실제 수집 예시](../../../collection_examples/20261102/README_KO.md)는 원문과 draft 후보를 준비한 것이며, 독립 검수된 benchmark gold가 아니다. [팀 작업표](TEAM_AND_DATA_KO.md), [실험표](AGENTS_AND_EXPERIMENTS_KO.md), [새 지표의 한계](METRICS_KO.md)를 따른다. 완전한 GPU/모델 runtime 검증이나 full production LinkPaper online API 검증을 완료했다고 쓰지 않는다.

## v2 실제 외부 논문 경로와 replay

최종 코드로 `evaluation/runs/live-paper-agent-final-20261102`를 실행했다. 최초 tool catalog 뒤 **search_papers 1회 → fetch_paper 1회 → search_local 1회 → open 2회 → scripted Answer**가 같은 episode에서 일어났다. arXiv 검색 결과는 **Understanding Batch Normalization, 1806.02375v4**였다. 원래 수집 예시의 Ioffe·Szegedy ICML 2015 파일과 혼동하지 않는다. 실제 PDF 3,479,757 bytes·24페이지를 가져와 page chunk62개를 만들고 2개를 열람했다. policy/tool 실패는0, 구조 진단은1.0, 과학적 의미 점수는null이다. 이 답은 연결 확인용이며 해당 연구 질문을 과학적으로 풀었다는 결과가 아니다.

같은 final run을 `live_paper_bench replay --run-dir ...`로 검증해 `replay_validated=true`, `network_calls_during_replay=0`을 확인했다. replay는 새 모델 평가가 아니라 기록된 도구·인용 재검증이다. provider·PDF·원문 청크·시도·실패·관측 timeline·응답/검수 hash·모듈 hash를 run에 보관했다. 앞선 `paper-acquisition-live-20261102`, `live-paper-agent-live-20261102` 기록은 보존했으며 최신 판정에는 final run을 쓴다.

가상 provider도 `evaluation/runs/live-paper-fixture-final-20261102`에서 도구 loop와 replay를 확인했다. 최종 의미 gate 수정 후 일반 QA·계보 demo는 `evaluation/runs/scholarly-qa-release-20261102`에 새로 보관했다. live provider의 현재 범위는 arXiv이며, 다른 한국어 발행처·전체 웹·GUI browser를 검증했다고 하지 않는다. [정확한 명령·범위](ACQUISITION_TRACKS_KO.md)를 따른다.

## 추가 실제 LLM 생성 smoke

[REAL_LLM_SMOKE_KO.md](REAL_LLM_SMOKE_KO.md)에 Qwen3-0.6B 고정 revision 한 개, 실제 GPU3 배치·가중치 hash·원 응답·토큰·종료 확인을 기록했다. 3개 가상 한국어 episode에서 3번 생성했고 모두 claims 필드가 누락되어 스키마 실패로 집계됐다. 실제 tool 호출은0회였으며, 이 실행으로 실제 LLM의 tool traversal 성공을 입증한 것은 아니다. 실패3개를 남긴 GLRS는0이며 과학적 성능/한국어 연구 능력 점수로 해석하지 않는다. worker는 종료됐고 GPU3의 기존 다른 프로세스 점유량은 보존됐다.
