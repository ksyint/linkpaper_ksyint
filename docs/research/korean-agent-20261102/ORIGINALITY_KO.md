# 독립 작성·출처·중복 감사

## 1. 이번 branch에서 한 일

기존 LinkPaper 및 fork의 MIT 고지를 유지하고, 기존 연구 branch를 기반으로 새 agent 환경과 지표 후보를 별도 모듈로 작성한다. 타 benchmark의 문제·답·template·prompt·source 데이터·코드를 새 fixture로 옮기지 않는다. fixture는 구현 계약을 확인하도록 자체 작성한 가상 자료이며 논문용 gold가 아니다.

공개 문서에는 선행연구가 이미 한 일, 이번 구현이 한 일, 아직 수집/실험할 일을 구분한다. 출처를 붙였다는 사실과 새로운 연구 기여라는 사실은 같지 않다. 요소를 새 이름으로 묶은 것만으로 최초라고 하지 않는다.

## 2. 기여·재사용 장부

| 항목 | 출처/상태 | 주장 가능한 범위 |
|---|---|---|
| LinkPaper indexing, ID, 평가 기반 | 원 저장소 MIT + 기존 contributor 고지 | 기존 자산 재사용 |
| LINK-DELTA packet 연구 코드 | fork의 기존 research branch | 이전 구현으로 명시 |
| agent_bench 도구·격리·trace | 이번 branch 자체 작성 | 실행 가능한 새 프로젝트 코드; 도구 agent 방식 발명 주장은 아님 |
| 6종 학술 근거 연결 과제·source 수 비공개 | 확장된 프로젝트 설계; 학술 QA·멀티홉은 선행연구에 존재 | 실제 새 자료·대안 충분근거·조건/종료 분석의 추가 발견을 검증. 설정 자체의 최초 주장 금지 |
| offline / live interleaved / frozen replay; staged 획득 대조 | 같은 Policy.step의 발견·fetch·검색·읽기 교차와 hash-bound 관측 재현 | arXiv 기본 provider 범위. 전체 웹·GUI·한국 발행처·production Neo4j/Qdrant API 완성이나 실제 LLM 성능으로 확대하지 않음 |
| lineage_metric GLRS | 결과 원천 하위 track 후보; B-cubed·근거 개입은 선행 방법 | 전체 benchmark primary가 아닌 subset의 구체적 운영화/타당성을 검증 |
| 영어 다수·한국어 포함 실제 답·근거 연결·대안·조건 gold 및 원천 subset | 본 corpus 구축·독립 검수 전 | 소량 수집 예시나 합성 fixture를 실제 benchmark gold/성능 결과로 발표하지 않음 |
| KoTAU | 비교 조사. 전 branch에서 license 파일을 확인하지 못함 | 구현·task를 복사하지 않음 |
| K-BrowseComp 및 학술 benchmark | 관련 연구 인용·공개 schema 비교 | 원 문제를 번역/부분 변형해 새 문항으로 발표하지 않음 |

[관련 연구 충돌표](RELATED_WORK_KO.md)와 [1차 출처 ledger](sources.json)에 가까운 연구와 확인 범위를 남긴다. 본문 문장을 가져오지 않고 자체 요약한다. 표·그림을 재사용하면 별도 출처·조건을 기록한다.

## 3. 데이터 제작 전 중복 검사

1. 기존 benchmark의 문항을 보지 않은 작성 단계에서 자체 원천 pool과 실제 연구자의 정보 요구를 기록한다. 별도 비교 담당자가 이후 overlap을 조사한다.
2. 원천 URL/DOI/version/hash, 질문 작성자·시각, 모델 초안 여부, 수정 이력을 보존한다.
3. 정확 문자열 hash, 한국어 정규화 n-gram/MinHash, 의미 유사도 후보 검색으로 외부 공개 문항 및 내부 split의 근접 사례를 찾는다. 유사도는 자동 표절 판정이 아니라 사람 검토 후보 생성이다.
4. 비슷한 사례는 질문의 제약 구조·핵심 답·선택 근거까지 대조하고 duplicate/adaptation/independently-authored-with-overlap/exclude 사유를 기록한다. 허용된 재사용이면 새 데이터와 별도 집계하고 원 benchmark를 인용한다.
5. 표·숫자·고유 사례를 그대로 가져와 이름만 바꾸지 않는다. 출처 본문의 사실을 묻는 새 과제와 기존 benchmark 문제의 재작성은 구분한다.

## 4. 원문 이용 조건

검색 서비스의 metadata 제공과 본문 재배포 권한은 별도다. [KCI OpenAPI](https://www.kci.go.kr/kciportal/po/openapi/openApiConnSamp.kci)는 서지·검색 metadata 경로이고, 그것만으로 모든 PDF의 이용 조건을 확정하지 않는다. [국립중앙도서관 KJCI 안내](https://copyright.oak.go.kr/faq.do)와 발행기관/논문별 표시를 원천 장부에 남긴다.

권리 확인 전 PDF·제3자 원문을 새 공개 repo에 일괄 넣지 않는다. 재배포가 확인된 원문은 조건에 맞춰 보존하고, 나머지는 metadata/원문 링크/자체 주석을 분리한다. 변환물의 이용 조건도 원문과 함께 검토한다. 검수용 비공개 holdout은 public fixture와 다른 저장소·권한·hash로 관리한다.

## 5. 지표 독창성과 논문 검증

원문은 영어 논문이 다수이고 한국어 논문을 포함하므로, 한국어 원문을 새로 다룬다는 주장만으로 기존 영어 scholarly benchmark와 구분하지 않는다. 주제는 AI에 한정하지 않는다. 주 질문의 한국어와 source_language를 분리하고 한 논문/교차 논문 근거 연결·대안 충분성·조건·탐색 종료 분석의 추가 가치를 검증한다. 필요한 논문 수를 공개하지 않는 설정 자체를 최초라 부르지 않으며, 검수한 대안의 수를 전역 최소 source 수로 확정하지 않는다. 결과 원천은 여러 task 중 하나다. 여러 분야를 수집했다는 사실만으로 학문 전체를 검증했다고 하지 않는다.

offline archive, live interleaved, frozen replay를 구분하고 staged 획득 후 QA는 별도 대조로 둔다. live는 한 episode에서 같은 Policy.step이 search_papers/fetch_paper/search_local/open 후 Answer를 선택한다. replay는 hash-bound 원문/관측 artifact를 검증하며 네트워크나 parser를 다시 호출하지 않는다. live의 의미 정확도는 null이고 사람 응답 review는 별도 hash-bound 기록이다. source·정답·개별 버전 권리를 사람이 확인하기 전 정적 gold를 자동 이식하지 않는다. arXiv 기본 provider·plugin·가상 fixture·HTTP preflight의 구현 사실을 전체 웹/GUI·한국 발행처 coverage·production API·실제 LLM 성능으로 바꾸어 쓰지 않는다.

새 GLRS는 결과 원천 하위 track의 novelty **후보**다. 전체 benchmark의 primary 점수로 사용하지 않는다. CUE-R·RARE·CONFPROP·SciValidityBench 등의 지표가 이미 같은 판정을 제공하는지 식·입력·실패 사례를 대조한다. 동일한 측정을 재명명한 것으로 확인되면 원 지표를 인용하고 이 프로젝트의 새 지표라는 주장을 철회한다.

새 metric의 unit test 통과는 계산 구현의 증거다. 전문가 평가와의 일치·반례·단순 baseline 대비 추가 식별력이 확인되어야 논문 기여로 주장한다. 실제 모델 실험을 하지 않은 수치는 결과표에 넣지 않는다. 다른 논문의 실험 수치와 자체 측정치를 섞지 않는다.

## 6. 투고 전 점검 기록

출처 원문/부록/release schema 재검토, 새 논문 재검색, 서술/그림 유사도 검토, 데이터 권리/기여자 고지, 논문-코드-데이터 숫자 일치, reviewer 관점 novelty 반증 메모를 별도 commit으로 보존한다. AI 도구 사용 범위와 사람이 검증한 항목도 해당 학회의 공개 정책에 맞춰 기록한다.

“절대 표절이 아님”이나 전 세계의 선행연구 부재를 도구 실행으로 증명할 수는 없다. 이 branch는 독립 작성과 추적 가능한 출처, 비교·제외 절차를 구체화한다. 미해결 충돌을 숨기지 않고 주장 범위를 줄인다.
