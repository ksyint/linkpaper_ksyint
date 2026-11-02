# LinkPaper 한국어 연구 에이전트 벤치마크 연구 패키지

기준일: 2026-11-02. 가제 **LinkPaper-KoEvidence**. 현재 상태는 **새 에이전트 평가 프로토타입 + 검증할 연구 설계**다. **핵심 과제 v2는 필요한 논문 수를 알려주지 않은 상태에서, 하나 또는 여러 논문의 근거를 스스로 찾아 연결해 정답을 구하는 것**이다. 결과 원천·재보고 판별은 여섯 하위 유형 중 하나다. 원천은 **영어 논문 비중이 높은 영어·한국어 논문 집합**이며 질문은 한국어 중심으로 자체 작성하고 같은 원천의 영어 질문 쌍으로 대조한다. **AI에 한정하지 않으며** 자연과학·공학·환경·생명과학 등의 논문도 포함한다. 실제 문헌의 전문가 gold와 본 논문 모델 결과는 아직 없다. 합성 fixture 점수는 소프트웨어 검증용이다.

저자 계획: **김수용 1저자**. 정상헌·남두현·오창원·이상민은 공저자 후보이며 순서는 정하지 않았다. 기존 서비스의 직무표를 이번 연구 분담의 근거로 사용하지 않는다.

| 읽을 문서 | 용도 |
|---|---|
| [RESEARCH_PROPOSAL_KO.md](RESEARCH_PROPOSAL_KO.md) | 주력 RQ, 선행연구와 경계, 과제·방법·논문 기여 후보 |
| [TASK_SUITE_KO.md](TASK_SUITE_KO.md) | 필요한 문헌 수 비공개, 여섯 과제 유형, 답변·근거·전체/하위 평가 계약 |
| [ACQUISITION_TRACKS_KO.md](ACQUISITION_TRACKS_KO.md) | 저장 archive·episode 내 외부 논문 검색/수집·고정 replay와 실행 명령 |
| [MAIN_TRACK_EVIDENCE_KO.md](MAIN_TRACK_EVIDENCE_KO.md) | 메인 논문의 주장–증거·필수 실험·독립 작성과 중복 감사 |
| [AGENTS_AND_EXPERIMENTS_KO.md](AGENTS_AND_EXPERIMENTS_KO.md) | 평가할 agent와 구성요소, 통제 실험·ablation·통계·실행 |
| [METRICS_KO.md](METRICS_KO.md) | 결과 원천 하위 track의 GLRS 후보 지표·반례·사람 기반 검증 |
| [TEAM_AND_DATA_KO.md](TEAM_AND_DATA_KO.md) | 5인 수집·수작업 gold·독립 검토·주별 배분·시간 산식 |
| [MANUAL_LABELING_KO.md](MANUAL_LABELING_KO.md) | PDF에서 무엇을 읽고 CSV에 무엇을 적는지, 논문별 3개씩 모범 문항과 수작업 안내 |
| [RELATED_WORK_KO.md](RELATED_WORK_KO.md) | 1차 출처 중심 충돌표와 대조 실험 근거 |
| [NOVELTY_COMPARISON_KO.md](NOVELTY_COMPARISON_KO.md) | K-BrowseComp·KoTAU 대비 차별성, 더 가까운 선행연구와 신규성 입증 조건 |
| [ORIGINALITY_KO.md](ORIGINALITY_KO.md) | 독립 작성·출처·코드/데이터 이용 조건·중복 감사 |
| [PAPER_OUTLINE_KO.md](PAPER_OUTLINE_KO.md) | 논문 구성과 검증 전 주장의 작성 원칙 |
| [REPOSITORY_COVERAGE_KO.md](REPOSITORY_COVERAGE_KO.md) | 모든 조사 대상 branch/file의 범위와 전수 inventory |
| [IMPLEMENTATION_KO.md](IMPLEMENTATION_KO.md) | 구현한 기능, 실행 명령, 실제 실행 검증과 남은 일 |
| [collection_templates/](collection_templates/README.md) | 5인 배분표와 빈 수집·라벨·실험 CSV |
| [실제 수집 예시](../../../collection_examples/20261102/README_KO.md) | 영어·한국어 실제 PDF의 로컬 수집, 출처·권리·근거 위치와 검수 전 질문 예시 |
| [KAKAO_DATA_STRATEGY_KO.md](KAKAO_DATA_STRATEGY_KO.md) | 단톡방에 보낼 수집 전략 두 문단 초안 |
| [VALIDATION_KO.md](VALIDATION_KO.md) | 실제 CPU 테스트·통합 재현 결과와 한계 |
| [GPU_EXECUTION_KO.md](GPU_EXECUTION_KO.md) | 한 장 선택·여러 worker·큰 모델 TP와 공정한 자원 기록 |
| [REAL_LLM_SMOKE_KO.md](REAL_LLM_SMOKE_KO.md) | 실제 단일 모델·GPU3 생성과 스키마 실패의 정직한 기록 |
| [sources.json](sources.json) | 논문·저자 저장소·공식 데이터 자료의 URL과 확인 범위 |

## 시작 순서

1. [과제 계약](TASK_SUITE_KO.md)과 관련 연구를 읽고, 여러 유형을 포함하는 **40개 기본 과제 파일럿**을 이용 조건이 확인된 원천에서 구축한다. 필요한 문헌 수·task 태그·충분근거집합은 private로 둔다.
2. 5인 순환표에 따라 작성자와 독립인 두 검수자가 정답·조건·원문 span·연결 단계·대안 근거를 검수한다. 결과 계보는 해당 하위 과제에서 검수한다.
3. 일반 QA와 계보 하위 track의 CPU fixture를 각각 확인한다. 이 fixture를 실제 benchmark 데이터로 발표하지 않는다.
4. 파일럿 신뢰도·단가·평가 타당성과 단순 baseline 대비 차이를 확인한 뒤 본 데이터 규모와 모델 실험을 확정한다. GLRS를 전체 suite의 유일 주 지표로 쓰지 않는다.

GPU 번호는 저장소에 고정하지 않는다. [단일·다중 GPU 매뉴얼](GPU_EXECUTION_KO.md)에 따라 할당받은 장치를 명시한다. 이번 작업의 단위·fixture 검증은 CPU이며, 필요성이 확인된 실제 LLM 연결 smoke는 사용자 지시대로 이 호스트의 물리 GPU3에서만 별도로 검증한다. smoke 결과도 실제 benchmark 본 실험과 구분한다. 실제 연구 성능은 본 데이터와 버전 고정 후 측정한다.

이전 [LINK-DELTA](../neurips-2027/README.md) 코드는 유지하되, 전체 근거를 처음부터 제공하는 packet 실험과 이번 순차 도구 agent 실험을 서로 다른 설정으로 보고한다.
