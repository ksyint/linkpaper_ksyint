# 한국어 연구 근거 탐색용 원본 가상 픽스처

일반 스키마에서 `Evidence`는 논문 전체가 아닌 원자적 결과 근거 기록입니다. 같은 논문의 서로 다른 실험·표 행은 같은 `paper_id`와 서로 다른 `source_locator`·`study_unit_id`를 가질 수 있습니다. 실제 reviewed 기록에는 검수 가능한 페이지·절·표·행·span locator가 필요하며 이 locator는 공개 도구 메타데이터에 포함됩니다.

여기에는 실제 논문·연구 결과가 없습니다. 이번 구현에서 독자 작성한 가상 문헌 32개와 질문 8개의 한영 쌍 16개입니다. 다른 벤치마크의 코드·문항·데이터를 복사하지 않았습니다. Codex 보조로 작성한 배관 점검용 자료이며 전문가 실데이터 주석으로 표현하면 안 됩니다.

각 과제의 관측 가능 문헌은 4개로 같습니다. 비공개 관리 태그 A와 B 각각에 supported/refuted/mixed/insufficient가 모두 들어 있어 태그에 정답을 고정하지 않습니다. 영어 원 실험 문헌, 한국어 재서술 문헌, 별도 실험 기록과 조건이 다른 문헌을 연결합니다. 단순히 다른 논문이라는 이유로 통계적 독립성을 부여하지 않습니다. 원 실험 계보를 알 수 없는 문헌의 `study_unit_id`는 null입니다.

`source_url`의 example.org는 실제 원천 논문 주소가 아닌 가상 자료 표시입니다. CC0 표시는 직접 작성한 가상 본문에만 적용하며 LinkPaper 프로그램·실제 논문·다른 벤치마크의 라이선스를 바꾸지 않습니다. `annotation_status=fixture`, `synthetic=true`로 표시하고 `--publication`에서 거부합니다. 이 기계적 검사는 실제 자료의 권리·전문가 판정의 진위를 인증하지 않습니다.

`Case`의 정답·계보·분할·관리 태그와 `Evidence.study_unit_id`는 평가자용입니다. 일반 policy는 PublicTask와 search/open/citations의 공개 반환값만 받습니다. 원 실험 그룹명은 에이전트가 임의의 이름으로 제시하며 평가는 이름 일치가 아닌 문헌 쌍의 동일/상이 계보 판단을 비교합니다. 알려진 계보 문헌을 읽거나 묶지 않으면 coverage가 낮아집니다.

```bash
# evaluation 디렉터리에서, 기존 격리 환경을 사용
.venv/bin/python -m linkpaper_eval.agent_bench validate
.venv/bin/python -m linkpaper_eval.agent_bench run-demo --agent lexical --out runs/agent-lexical-fixture
.venv/bin/python -m linkpaper_eval.agent_bench run-demo --agent blind --out runs/agent-blind-fixture
.venv/bin/python -m linkpaper_eval.agent_bench run-demo --agent oracle --out runs/agent-oracle-fixture
```

lexical은 이 가상 자료의 명시적 조건·결과·실험명 표현을 읽는 단순 휴리스틱입니다. blind는 근거를 열지 않는 음성 대조군이며 oracle은 정답에 특권적으로 접근하는 양성 대조군입니다. 어느 점수도 실제 모델의 과학 능력·한국어 연구 능력·새 방법의 성능을 입증하지 않습니다. 구조 점수와 별도로 응답 해시에 묶인 의미 검수가 필요하며, 가상 자료에서는 의미 검수를 붙여도 `scientific_semantic_accuracy`를 계산하지 않습니다.

외부 policy는 `step(PublicTask, list[ToolEvent]) -> Action | Answer`를 구현하고 `--policy module:factory`로 명시적으로 불러옵니다. 매 과제마다 새 policy를 생성합니다. 기본 코어는 CPU 전용이며 네트워크·모델 다운로드·GPU 호출을 하지 않습니다. 외부 policy의 모델·명령·버전·비용·GPU 제약은 해당 어댑터가 별도로 고정·보고해야 합니다.
