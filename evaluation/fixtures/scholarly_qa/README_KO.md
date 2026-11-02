# 일반 학술 QA 계약용 합성 fixture

자체 작성한 가상 문헌14개·근거16개·한국어 질문7개다. 실제 논문이나 사람 검수된 gold가 아니다. 한 후보 archive를 공유하며 여섯 private task 유형, 한 논문의 여러 근거, 여러 논문의 bridge, 한 편/두 편 대안 충분집합, 조건 비교·수치·상충/부족·결과 원천을 검증한다.

모델은 공개 질문·언어·불투명 ID와 도구 관측만 받는다. `Case.task_type`, `Gold`, 필요한 문헌 수는 전달하지 않는다. 알려진 충분집합의 paper 수는 전역 최소 필요 수의 증명이 아니다. 일반 QA의 미적용 계보 지표는 N/A다.

`run_korean_agent_demo.sh`의 oracle은 private gold에 접근한 소프트웨어 양성 대조이고 blind는 무근거 음성 대조다. 둘의 구조 점수·reference 일치를 LLM 능력이나 논문 성능으로 발표하지 않는다. scientific_semantic_accuracy는 null이다. 같은 질문의 실제 영어 대조 질문이 이미 수집됐다는 뜻도 아니다.
