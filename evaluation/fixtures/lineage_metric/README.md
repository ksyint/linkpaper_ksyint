# GLRS 전용 합성 계산 예제

모든 문서 ID·unit·질문·조건은 이 지표의 손계산 검증을 위해 새로 만든 가상 값이다. 실제 논문, 한국어 benchmark, 사람 주석 또는 모델 실행 결과가 아니다. 다른 benchmark 문항이나 프롬프트를 복제하지 않았다.

`synthetic_triplets.json`은 perfect 예제 1개와 repeat 세계의 agent 응답을 비운 missing 예제 1개다. 각 세계에는 atomic evidence record 4개가 있고 알려진 eligible unit 수는 B=2, R=2, N=3이다. R은 B의 unit을 유지하며 같은 unit의 재보고 비중을 바꾸고, N은 B의 unit을 유지한 채 새 unit을 포함한다. 두 예제는 합성 평가 family가 서로 다르다. 예상 GLRS는 1과 0, family macro는 0.5다. 이 수치는 과학적 유효성 검증이나 실험 성능이 아니다.

모듈 실행 방법과 수식·한계·사람 meta-eval 계획은 `docs/research/korean-agent-20261102/METRICS_KO.md`를 참조한다. gold mapping은 evaluator 전용이며 에이전트 입력으로 쓰면 안 된다.


## Record와 원문 논문의 구분

이 fixture의 `gold_units` key와 `study_groups` key는 질문 조건에 관련된 결과 unit을 최대 하나 담는 **atomic result/evidence record ID**다. 물리 논문 전체의 ID가 아니다. 실제 core에서는 각 record에 parent `paper_id`와 원문 page/table/span locator가 붙고, 한 논문의 여러 결과 unit은 별도 record로 나뉜다. 한 논문 ID에 서로 다른 gold unit을 동시에 배정하면 안 된다.

`len(gold_units)=4`는 RECORD 수 control이다. 이 standalone 합성 JSON에는 parent-paper mapping이 없으므로 물리 논문 수가 B/R/N에서 같다는 검증은 할 수 없다. core bridge는 unique parent-paper 수도 별도로 같게 검사하고 record 수와 source 논문 수를 함께 보고한다. 원문 논문 수·record 수·길이/정보량·검색 rank control은 서로 다른 감사 항목이다. 이 fixture는 실제 source 논문이나 실제 결과 라벨을 제공하지 않는다.
