# 실제 실행한 검증

2026-11-02, Python3.12 격리 환경에서 단위·계약 검사를 CPU로 실행했다. 공개 GPU 설정을 일반화하고 HF 정책을 추가한 최종 검증은 아래 271개 통과다. 별도로 사용자 허가에 따라 단일 모델 가중치를 내려받아 물리 GPU3에서 3개 합성 episode의 실제 생성 경로를 확인했다. 유료 모델 API는 호출하지 않았다. 단위 검사와 실제 모델 smoke의 목적·결과를 구분한다.

```bash
CUDA_VISIBLE_DEVICES='' LINKPAPER_TEST_DOCKER_NEO4J=0 uv run --project evaluation --frozen --extra dev --extra stores python -m pytest -q evaluation/tests
# 271 passed, 4 skipped
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

모든 fixture의 scientific_semantic_accuracy는 null이다. 이 숫자들은 실제 모델·한국어 학술 능력·새 지표의 인간 타당성·main 학회 기여를 검증한 성능이 아니다. 역할/가용 정보가 다른 oracle과 일반 agent를 하나의 우승 순위로 합치지 않는다.

## 확인한 중요한 반례

- 충분한 대안 witness 하나만 정확히 찾은 경우를 불필요하게 감점하지 않음.
- 같은 unit을 여러 그룹으로 나누기/다른 unit 합치기, 가짜 cluster로 unit 수 맞추기, 기존 unit 재취득을 새 unit처럼 계산하기.
- 열지 않은 문헌 인용, 거짓 opened ID·tool observation, 누락/timeout/오류의 분모 보존.
- 모든 visible paper/version/result unit과 질문 언어 쌍의 split 누출.
- 작성자를 제외한 독립 reviewer metadata, fixture/draft/oracle의 publication/semantic-score gate.
- 같은 논문의 서로 다른 atomic record/locator와 matched record 수·source-paper 수의 구분.

추가로 새 소스의 Python3.11 문법 호환, bash 문법, git diff whitespace, 새 문서의 상대 링크를 검사했다. [validation_summary.json](validation_summary.json)에 source SHA와 합성 CLI 집계가 있다. raw fixture run은 로컬 evaluation/runs/korean-agent-validation-20261102에 있고 runs는 Git ignore 대상이다. CI의 korean-agent-smoke가 같은 스크립트를 CPU에서 재실행하고 artifact로 보관한다.

## 아직 필요한 연구 검증

실제 한국어 원천 자료·수작업 gold/초기 IAA·대체 근거·권리·source-family split, 실제 model snapshot 고정과 공정한 budget 실험, 전문가 metric meta-eval은 수행 전이다. [팀 작업표](TEAM_AND_DATA_KO.md), [실험표](AGENTS_AND_EXPERIMENTS_KO.md), [새 지표의 한계](METRICS_KO.md)를 따른다. 완전한 GPU/모델 runtime 검증이나 full production LinkPaper online API 검증을 완료했다고 쓰지 않는다.

## 추가 실제 LLM 생성 smoke

[REAL_LLM_SMOKE_KO.md](REAL_LLM_SMOKE_KO.md)에 Qwen3-0.6B 고정 revision 한 개, 실제 GPU3 배치·가중치 hash·원 응답·토큰·종료 확인을 기록했다. 3개 가상 한국어 episode에서 3번 생성했고 모두 claims 필드가 누락되어 스키마 실패로 집계됐다. 실제 tool 호출은0회였으며, 이 실행으로 실제 LLM의 tool traversal 성공을 입증한 것은 아니다. 실패3개를 남긴 GLRS는0이며 과학적 성능/한국어 연구 능력 점수로 해석하지 않는다. worker는 종료됐고 GPU3의 기존 다른 프로세스 점유량은 보존됐다.
