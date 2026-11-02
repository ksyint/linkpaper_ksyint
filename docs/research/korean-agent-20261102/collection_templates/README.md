# 수집·검수 시작 양식

원문/정답을 수집했다고 표시하지 않는 **빈 header 양식**이다. assignments.csv만 사용자 확인 5인과 40개 pilot 목표를 담는다. TEAM_AND_DATA_KO.md의 회전 검수와 실제 가용 시간 확인을 따른다.

질문·triplet·review의 private 양식은 실제 gold가 채워지면 공개 agent 입력과 다른 저장소/권한에 둔다. 이 공개 디렉터리에는 실데이터 gold를 채워 넣지 않는다. 쉼표/JSON 배열 등의 세부 직렬화는 codebook freeze와 함께 결정한다. core JSONL에 옮길 때 형식 검사와 사람의 결과 unit/조건 판정을 각각 수행한다.

원문 PDF/본문·원문 checksum과 근거 record 텍스트 checksum을 구분한다. source_locator에는 page/section/table/row/span 위치를 남긴다. result unit은 통계적 독립성을 뜻하지 않는다. 시간/탈락 사유도 기록하여 목표 개수를 맞추려고 기준을 낮추지 않는다.

원문 언어와 질문 언어는 별개다. 원문은 **영어 다수·한국어 포함**이며 주제는 AI에 한정하지 않는다. AI/컴퓨터·자연과학·공학·환경·비임상 생명/농업 등의 후보를 판정 역량에 맞춰 찾는다. 원문 영어 약80%/한국어 약20%는 pilot 임시 제안이며, 사용자가 확정한 비율이 아니다. 분모는 중복 버전을 통합한 source-paper/version family이고 혼합 언어 family는 별도 집계한다. case/record/episode 수와 혼동하지 않는다.

`candidate_sources`/`source_registry`에는 venue·연도·분야·출판 상태·실제 본문 언어 판정 근거 위치를 남긴다. 저자 국적이나 초록 언어로 본문 언어를 추정하지 않는다. 주요 venue 발견은 truth/독립성/권리 gold가 아니다. 단순히 English-only/Korean-only/mixed source bundle별 성능 차이를 구한 결과는 분야·내용·시기 등이 다른 관측 분석이며, 같은 원문에서 KO/EN 질문만 바꾸는 paired 대조와 구별한다.

`questions_private`의 `source_language_profile`은 bundle의 원문 구성 요약이고, `record_source_language_counts`는 `en`/`ko`/`mixed` record 빈도다. `source_paper_language_profile_counts`는 paper_id별 visible record 언어의 정렬된 집합(profile) 빈도다. 예를 들어 한 paper의 기록이 en과ko이면 profile은 `en+ko`이며 선언값 `mixed`는 별도 값이다. `triplets_private`에는 B/R/N의 record 수·parent paper 수 외 두 원문 언어 빈도도 각각 일치하는지 남긴다. core bridge가 자동 대조한 결과와 사람이 언어 metadata·내용 대응을 확인한 note를 함께 보관한다. standalone GLRS의 `language`는 질문 언어로 source-language control을 자동 검증하지 않는다.

소량 실제 원문 수집 예시는 [collection_examples](../../../../collection_examples/20261102/README_KO.md)를 참고한다. 그 폴더의 후보·미검수 주석을 이 빈 private gold 양식에 검수 완료로 옮기지 않는다. 이전 합성 fixture나 실제 smoke의 언어 통계는 각 당시 hash 기준의 기록이며 실제 corpus 수집 목표를 달성했다는 증거가 아니다.
## 사람 입력용 CSV

[논문별 모범 예시와 빈 CSV](../../../../collection_examples/20261102/csv_labeling/README_KO.md)를 검수자별로 복사해 사용한다. 근거·관계·정답의 빈 CSV와 조정용 CSV, 논문별 3문항씩 총 9개의 작성 예시를 제공한다. 실제 순서는 [수작업 안내](../MANUAL_LABELING_KO.md)에 있다. 사람 검수 완료 표시나 실제 검수자 이름을 대신 채우지 않았다. 이 디렉터리의 기존 CSV는 운영·변환용 상세 양식으로 유지한다.
