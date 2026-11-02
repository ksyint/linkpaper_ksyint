# 실제 도구 추론 기록 → GLRS 연결 점검용 가상 자료

코드의 `Evidence` 및 legacy 공개 키 `document_id`는 **과제와 관련된 원자적 결과 근거 기록**입니다. 논문 전체를 단일 결과 단위로 가정하지 않습니다. 한 `paper_id`에 서로 다른 locator·결과 단위의 여러 기록을 둘 수 있습니다. 실제 reviewed 기록은 페이지·절·표·행·span을 가리키는 `source_locator`가 필요합니다. 이 픽스처는 각 과제에 기록 4개·서로 다른 원천 문헌 4개를 맞췄으며 연결 모듈은 두 수를 각각 검사하고 private manifest의 `matched_counts`에 기록합니다.

이 자료는 이번 작업에서 독자 작성한 가상 문헌 6개, 한국어 과제 3개, 비공개 대조군 묶음 1개입니다. 실제 논문·전문가 GT·모델 성능 자료가 아니며 기존 `agent_bench`의 문헌 32개·한영 과제 16개를 변경하지 않습니다. 다른 벤치마크 문항·코드를 복사하지 않았고, 작성 시 Codex의 보조를 사용했습니다.

세 과제는 같은 질문·언어·데이터셋 조건을 쓰며 관측 문헌은 각각 4개입니다. B는 원 실험 RA·RB와 배경 문헌, R은 같은 원 실험 RA를 재서술한 문헌을 추가하고 배경 문헌을 교체한 상태, N은 새 실험 기록 RC를 추가하고 배경 문헌을 교체한 상태입니다. 적격 결과 단위 수는 2/2/3이지만 **세 과제의 verdict는 모두 supported**입니다. 결과 단위 수 변화와 판정 변경을 자동으로 동일시하지 않습니다. 다른 실험 기록이라는 이유로 통계적 독립성을 보증하지 않습니다.

`study_unit_id`, B/R/N 대응, 적격 증거 목록은 평가자 전용입니다. 에이전트는 같은 한국어 질문과 허용된 search/open/citations 반환값만 봅니다. 원문에는 RA·RB·RC를 설명하는 가상 문장이 있고, lexical 데모가 이를 읽어 임의의 그룹을 출력합니다. 숨긴 정답 unit ID를 정책에 주입하지 않습니다. 계보를 모르는 배경 문헌은 null로 남기며 적격 결과 근거에 포함하지 않습니다.

```bash
# evaluation 디렉터리에서, CPU·오프라인만 사용
.venv/bin/python -m linkpaper_eval.agent_bench run-demo \
  --corpus fixtures/agent_lineage/corpus.jsonl \
  --cases fixtures/agent_lineage/cases.jsonl \
  --agent lexical --out runs/lineage-tool-agent-fixture

.venv/bin/python -m linkpaper_eval.agent_lineage \
  --corpus fixtures/agent_lineage/corpus.jsonl \
  --cases fixtures/agent_lineage/cases.jsonl \
  --predictions runs/lineage-tool-agent-fixture/predictions.jsonl \
  --triplets fixtures/agent_lineage/triplets.jsonl \
  --out runs/lineage-evaluator-fixture
```

연결 모듈은 먼저 core 평가의 기록 무결성 검사를 수행하고 고정 도구를 재생해 실제로 open한 ID를 다시 구합니다. 제출된 `opened_ids`만 믿지 않습니다. N 응답 누락, agent error, 조작한 도구 관측값이나 open 목록은 대조군을 삭제하는 대신 해당 episode의 오류로 남아 GLRS 0을 받습니다. 서로 다른 case 3개, 같은 질문·언어·조건·분할·계보군, 같은 문헌 수를 요구합니다. 적격 witness ID는 실제 관측 가능한 근거여야 하고 R의 결과 단위 집합 보존 및 N의 기존 단위 보존·신규 단위 추가도 검사합니다.

`triplets.jsonl`은 `TripletSpec`으로 읽는 평가자용 매핑입니다. B/R/N은 각각 case ID이고 `eligible_evidence_ids`에는 각 과제의 원천 Evidence ID를 적습니다. 이 목록을 core의 충분 근거 집합 합집합과 강제로 동일시하지 않습니다. 같은 결과 단위의 다른 적격 원문 witness를 명시할 수 있지만 과학적 적격성은 사람이 별도로 검수해야 합니다.

출력 `triplets.private.json`, `manifest.private.json`, `core_diagnostics.json`, `glrs.json`에는 **비공개 정답이 들어갑니다. 에이전트 입력으로 사용하지 마세요.** 입력 파일·연결 모듈·지표 모듈 SHA도 저장합니다. 이 쉬운 fixture에서 GLRS 1이 나오는 것은 실제 search/open/citations → 출력 그룹 → 지표 연결의 점검 결과일 뿐이며, 새 지표의 과학적 타당성이나 실제 모델 성능을 입증하지 않습니다.
