# 구현·실행 안내

## 구현 범위

**핵심 과제 v2:** 필요한 논문 수를 주지 않는 단일/다중 논문 근거 연결 QA다. `Case.task_type` 여섯 private 유형, `Gold.answer_type`의 decision/short/numeric/explanation을 지원한다. 일반 QA에 verdict·결과 그룹을 강요하지 않으며, 판정·reference·계보 진단은 적용되는 문항에서만 집계한다. 숫자/단답 reference 일치와 구조 점수는 의미 정확도가 아니다. [전체 과제](TASK_SUITE_KO.md)를 따른다.

`condition_recall`은 private canonical key·표기 진단이다. 의미 점수는 이 정확한 필드명을 강요하지 않고, 검증된 trace·열람/인용·알려진 충분근거와 응답 hash 기반 의미 review를 결합한다. 실패는 자동 0, 유효한 미검수 응답은 대기(null)이며 하나라도 대기하면 전체 과학 점수도 null이다. 실제 검수 수와 자동 0점을 구분한다.

`evaluation/src/linkpaper_eval/agent_bench/`는 public task에 모든 근거를 미리 넣지 않는 CPU 도구 agent harness다. search/open/citations allowlist, 호출/관측 예산, opaque ID, episode별 상태, 근거 텍스트 hash·출처·버전·원문 locator, 모든 visible 문헌/알려진 result unit의 split 격리, 읽은 근거 인용 검증, 오류 포함 채점, 응답 hash 의미 검수를 제공한다. Python policy는 신뢰하는 실험 코드이며 OS 보안 sandbox가 아니다.

`available_evidence_ids` private mask는 실제 획득한 범위를 제한한다. 빈 목록도 허용하며 원래 gold와 예정 문항을 유지한다. 검수된 대안 충분집합의 paper/record 수를 private로 보고하지만 전역 최소 필요 수를 증명하지 않는다.

`paper_acquisition.py`는 arXiv API·PDF 획득·페이지 청크·cache·freeze를 제공한다. `live_paper_bench.py`에서는 같은 policy가 **episode 안에서** `search_papers/fetch_paper/search_local/open`을 교차 호출하고 답한다. 별도 strict replay는 저장 관측·근거 활성화 시점·인용을 네트워크/파서 없이 검사한다. 실제 외부 연결과 scripted loop를 확인했으며 실제 LLM 추론 실험과 구분한다. [획득 모드와 실행 명령](ACQUISITION_TRACKS_KO.md)을 따른다.

`evaluation/src/linkpaper_eval/lineage_metric.py`는 별도 GLRS 후보 지표와 matched triplet validator다. `evaluation/src/linkpaper_eval/agent_lineage.py`가 private triplet registry와 실제 core tool trace를 연결해 GLRS 입력을 만든다. 읽었다는 자기주장을 믿지 않고 frozen tool replay를 대조한다. 원문 record와 parent paper 수·unit 제약을 검사하며, B/R/N의 record별 원천 언어 구성과 paper별 언어 profile 구성도 맞춘다. standalone metric만 호출하면 paper/언어 metadata까지 자동 검증되는 것은 아니다. output에는 private gold가 있으므로 agent 입력으로 쓰지 않는다. 실제 자료의 eligible witness와 계보는 별도 사람 검수가 필요하다.

이 bridge는 결과 원천 하위 유형에만 사용하며 일반 QA를 GLRS로 채점하지 않는다. 외부 획득 registry는 draft이므로 live 구조 점수를 frozen reviewed-gold 점수로 바꾸지 않는다.

`Evidence.source_language`는 원천 record의 본문 언어이고 `Case.question_language`는 질문 언어다. 영어 논문에 한국어 질문을 붙일 수 있다. 본 데이터는 영어 논문이 다수인 영어·한국어 집합을 목표로 하며, 작은 합성 fixture의 언어 비율은 수집 목표를 실현했다는 증거가 아니다. [실제 수집 예시](../../../collection_examples/20261102/README_KO.md)는 원천과 검수 전 후보를 보여 주며 아직 publication gold가 아니다.

선택적으로 `hf_agent_policy.py`와 별도 Python worker가 실제 text LLM의 JSON 결정을 연결한다. 공개 task/history만 전달하며 모델은 상주하고 대화는 매 요청 새로 구성한다. [실제 smoke](REAL_LLM_SMOKE_KO.md)는 GPU3에서 가상3과제의 생성/실패 경로를 확인했다. 임의 모델의 prompt를 자동으로 최적화하거나 형식 오류를 복구하지 않는다.

프로덕션 LinkPaper의 indexing/Neo4j/Qdrant corpus를 이 archive schema로 내보내는 운영 adapter, arXiv 외 발행처 provider, 사람 gold와 추가 모델별 실험은 후속 작업이다. 새 benchmark live loop와 기존 서비스의 501 API scaffold를 구분한다. CSV 주석·빈 양식과 교육용 모범답은 제공하지만 독립 사람 검수를 대신하지 않는다.

## CPU 설치와 도구 fixture 실행

저장소 루트에서 Python3.11+를 사용한다. 이 작업의 격리 검증 환경은 Python3.12다.

```bash
uv sync --project evaluation --extra dev --python 3.12
uv run --project evaluation --frozen python -m linkpaper_eval.agent_bench validate
uv run --project evaluation --frozen python -m linkpaper_eval.agent_bench run-demo --agent lexical --out evaluation/runs/agent-lexical
uv run --project evaluation --frozen python -m linkpaper_eval.agent_bench run-demo --agent blind --out evaluation/runs/agent-blind
uv run --project evaluation --frozen python -m linkpaper_eval.agent_bench run-demo --agent oracle --out evaluation/runs/agent-oracle
```

기존 output 디렉터리는 덮어쓰지 않는다. 다른 run 경로를 선택한다. fixture는 자체 작성한 가상 문헌32개, 기본 질문8개의 한영 쌍16개다. 각 case에서 visible 문헌4개이며 private control A/B 각 태그 안에 모든 verdict가 있다. lexical은 fixture의 명시적 표현을 읽는 heuristic이며 실제 LLM baseline이 아니다. oracle은 gold에 접근한 양성 대조다.

위 기본 fixture는 이전 결과 원천 track이다. 새 `evaluation/fixtures/scholarly_qa/`는 가상 근거16개·paper14개·문항7개로 여섯 유형, 한 논문 복수 근거, 한 편/두 편 대안 충분집합을 검증한다. `run_korean_agent_demo.sh`는 이 자료도 oracle/blind로 실행한다. 원천 유형을 제외한 문항의 계보 지표는 N/A이며 본 모델 성능이 아니다.

publication 검사는 fixture/draft를 거부한다. reviewer 이름·권리 metadata 형식 검사는 실제 사람의 판단/권한을 인증하지 않는다. 본 데이터의 독립 검수 ledger를 함께 검토해야 한다.

## 통합 CPU 재현

```bash
bash scripts/run_korean_agent_demo.sh /tmp/linkpaper-korean-agent-demo
```

도구 fixture의 lexical/blind/oracle, 손계산 GLRS fixture, **실제 tool trace→GLRS bridge**를 함께 실행한다. bridge 전용 자료는 별도로 직접 작성한 가상 record6개와 B/R/N 3개 episode다. visible record 수와 paper 수, 원천 언어 구성을 맞추고 known unit 수는2/2/3이며, 세 verdict는 모두 supported다. unit 추가가 항상 verdict flip이라는 shortcut을 만들지 않는 예시다. 이 자료도 실제 논문/모델 결과가 아니다. 언어 구성을 보강하기 전의 실제 HF smoke 기록은 당시 hash와 결과를 그대로 보존한다.

상위 CLI에서도 `linkpaper-eval agent ...`, `linkpaper-eval lineage-metric ...`, `linkpaper-eval agent-lineage ...`를 사용할 수 있다.

## 실제 정책 연결

`step(PublicTask, list[ToolEvent]) -> Action | Answer`를 구현하는 factory를 `--policy module:factory`로 지정한다. 질문·공개 도구 trace만 정책에 전달한다. 매 case 새 policy를 만든다.

```bash
uv run --project evaluation --frozen python -m linkpaper_eval.agent_bench run   --policy my_agent:factory --corpus /path/to/frozen/corpus.jsonl   --cases /path/to/private/cases.jsonl --out evaluation/runs/my-agent-v1
```

실제 agent process에는 private cases/gold 경로를 노출·mount하지 않는 별도 public-observation 경계를 사용한다. 위 Python plugin 예시는 신뢰하는 실험 코드용이다. import 가능한 임의 코드를 실행하면서 gold 파일 접근까지 차단하는 OS sandbox라고 표현하지 않는다. model ID·revision·비용·GPU UUID/배치 증거는 정책 adapter manifest에 별도로 고정한다.

### JSON 명령 정책 adapter

`linkpaper_eval.agent_bench_policy:factory`는 명시적인 `LINKPAPER_POLICY_COMMAND_JSON` argv 배열의 신뢰하는 외부 정책을 호출한다. stdin에는 `schema_version`, public `task`, 공개 `history`만 전송하고 stdout의 Action 또는 Answer JSON 하나를 엄격히 해석한다. timeout/실행 실패/잘못된 JSON은 평가 실패로 남긴다. 명령·stderr·환경변수의 비밀값은 error 보고에 넣지 않는다. 전체 public history를 재전송하므로 wrapper가 모델 token·비용을 별도 장부로 기록해야 한다.

기본 child는 CUDA_VISIBLE_DEVICES를 비워 CPU만 보게 한다. 명시적으로 LINKPAPER_POLICY_USES_GPU=1과 LINKPAPER_POLICY_GPU_INDEX를 설정했을 때만 선택한 물리 GPU UUID를 확인해 child를 격리한다. 단일·다중 GPU 사용법과 현재 backend 범위는 [GPU 매뉴얼](GPU_EXECUTION_KO.md)을 따른다. 이 adapter는 모델을 설치하거나 원격 서버의 GPU 배치를 인증하지 않는다. 실제 모델 ID/revision·wrapper source·usage ledger도 함께 고정해야 한다. 별도 private evaluator와의 OS 접근 격리는 운영 설정이다.

## 의미 평가와 본 실험

`score --predictions ... --reviews ...`는 최종 응답 hash와 연결된 **조정된 최종 의미 review**를 받는다. 검수자 두 명의 원래 기록은 별도 장부에 보존한다. fixture/draft 또는 oracle이 포함되면 scientific_semantic_accuracy는 null이다. 구조 점수1.0을 과학 정확도100%로 해석하지 않는다.

본 데이터는 권리/버전/검수 metadata를 채운 뒤 `--publication`으로 형식을 검증한다. 이는 과학적 타당성과 신규성의 자동 인증이 아니다. [실험 계획](AGENTS_AND_EXPERIMENTS_KO.md)과 [팀 작업표](TEAM_AND_DATA_KO.md)를 따른다.

## 검증 기록

실제 실행한 검사·fixture CLI·GLRS 반례 검증과 남은 제한은 이 디렉터리의 `VALIDATION_KO.md`에 최종 기록한다. 실행하지 않은 model/API/GPU 성능은 기록하지 않는다.
