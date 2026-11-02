# 우리 파이프라인의 신규성 후보와 비교 기준

확인일: 2026-11-02. **현재는 신규성이 입증된 benchmark가 아니라 검증할 기여 후보**다. 가장 강한 주장은 '실제 논문 결과의 원천을 사람이 확인하고, agent가 같은 결과의 재보고와 새 결과 보고를 구별하는 능력을 통제된 탐색 환경에서 측정한다'는 것이다. 한국어·논문 QA·GraphRAG·수작업·CSV 자체를 신규성으로 삼지 않는다.

## K-BrowseComp·KoTAU와의 차이

| 축 | K-BrowseComp | KoTAU | LinkPaper-KoEvidence 후보 |
|---|---|---|---|
| 핵심 과제 | 한국 맥락 웹의 멀티홉·병렬 제약을 풀어 짧은 정답 검색 | 여행 조건을 충족하는 기차·숙소·지도 도구 사용과 예약 상태 변경 | 문헌의 결과·조건·원천을 찾아 재보고와 별도 reported-result unit을 구별 |
| 정답/주석 | 정답, expected chain, URL, 중간 값 checklist | task 입력과 disclosure; 별도 라벨 proposal의 최종 상태·reference calls 등 | 판정·조건·대안 근거와 atomic record별 결과 원천 그룹·unknown |
| 진단 | 정답·보정과 trajectory 실패 분석, adversarial synthetic | 관측 coverage·누락/오래된 정보 등 진단과 실행 상태 | 실제 읽고 인용한 근거의 그룹 정합성, 반복 보고 불변성·새 unit 반응 |
| 주 측정 단위 | 정보 요구를 해결하는 답과 근거 경로 | 사용자 요구를 실행하는 행동·상태 | 질문 관련 결과 보고 단위와 그 원천 관계 |

K-BrowseComp는 이미 300개 verified·100개 synthetic 문항과 경로·checklist를 제공한다. '최종 정답만 본다'거나 '우리만 중간 근거를 본다'는 비교는 틀리다. checklist는 대안 경로를 금지하는 강제 순서가 아니다. [공식 논문](https://arxiv.org/html/2606.02404v1), [공식 저장소](https://github.com/prometheus-eval/K-BrowseComp), [데이터 카드](https://huggingface.co/datasets/prometheus-eval/k-browsecomp/raw/main/README.md)

KoTAU는 로컬 main `f88a6a462cc27cec5d18c160ff932a8a145681e6`와 라벨 proposal `66556653d706d8187d157a2e96cdc206f4557d21` 기준이다. main의 공인 채점 미확정과 proposal의 평가 설계를 구분한다. main에 grader가 아직 없다는 사실은 우리 연구의 신규성이 아니다. snapshot·도구 allowlist·관측/private gold 분리도 이미 구현돼 있다. 공개 웹 접근 실패를 프로젝트 부재로 해석하지 않는다. [조사 범위·파일 근거](audits/local/LOCAL_BENCHMARK_AUDIT_KO.md)

## 추가로 측정하려는 것

가상의 예로 A가 실험 결과를 보고하고 B·C가 그 결과를 재인용했다면 문헌은 3개여도 원래 결과가 3개 생긴 것은 아니다. 반면 표현과 수치가 비슷해도 D가 새 실험·분석 결과를 보고했다면 별도 reported unit일 수 있다. 어느 쪽도 DOI·저자·문장 유사도만으로 확정하지 않는다. 새 reported unit은 통계적 독립성의 증명이 아니다.

핵심 데이터는 **표현이 다르지만 같은 원 결과**와 **표현이 유사하지만 별도 결과**를 모두 포함해야 한다. 같은 PDF의 표와 본문을 비교하는 것만으로는 이 차이를 충분히 보여 줄 수 없다.

| 세계 | 같은 수의 문헌을 주는 설명용 가상 구성 | 확인된 결과 unit 수 |
|---|---|---:|
| B | 원 결과 A + 원 결과 D + 배경 문헌 P | 2 |
| R | 원 결과 A + 원 결과 D + A의 재보고 B | 2 |
| N | 원 결과 A + 원 결과 D + 새 결과 E | 3 |

질문·조건·문헌/record 수·원천 언어 구성·예산을 맞추고, 길이·검색 순위·관련성 차이도 검사한다. R에서 문헌 수나 반복 표현에 끌려 결과 수를 부풀리는지, N에서 새 unit의 근거를 실제 취득·인용하는지 평가한다. N에서 최종 verdict가 반드시 뒤집혀야 하는 것은 아니다. 위 구성은 설명용이며 실제 완성된 자료가 아니다.

GLRS는 이 비교에서 **취득·인용한 근거의 계보 정합성, 반복 보고 불변성, 새 unit 반응**을 결합한 후보 지표다. 정답이나 개별 citation이 맞아도 원천을 중복 집계하는 실패를 추가로 식별하려 한다. 수학적 최초나 사람 타당성이 검증됐다는 주장은 하지 않는다. [지표 정의·한계](METRICS_KO.md)

## 더 가까운 선행연구도 넘어야 한다

- [CUE-R](https://arxiv.org/abs/2604.05467)는 REMOVE/REPLACE/DUPLICATE와 정답·grounding·confidence·trace 반응을 이미 다룬다. 중복 자료 개입 자체가 신규성은 아니다.
- [RARE](https://aclanthology.org/2026.acl-long.923/)는 atomic fact 중복 추적과 redundancy-aware retrieval 평가를 이미 다룬다. 같은 사실의 반복과 실제 실험/결과 원천의 재사용을 구별해야 한다.
- [SciNet](https://proceedings.mlr.press/v306/shao26h.html)은 논문 관계·학술 계보를 찾는 agent 과제를 이미 다룬다. 문헌 그래프를 탐색하는 것만으로는 새롭지 않다.

따라서 K-BrowseComp·KoTAU와 과제가 다르다는 사실은 **차별성**이고, 전 세계 연구 대비 **신규성의 증명**은 아니다. [전체 충돌표](RELATED_WORK_KO.md)와 함께 검토한다.

## 논문 기여로 주장하기 위한 실험

1. 실제 교차 논문 family에서 unit 경계·관계에 대한 조정 전 2인 일치도와 미확인 비율을 확인한다.
2. DOI 통합, text/embedding dedup, 일반 CITES GraphRAG, common-parent grouping으로 해결되는 정도와 추가로 구별되는 사례를 비교한다.
3. 최종 정답·citation 점수가 높은데 결과 원천을 오집계하는 실패가 여러 모델·새 source family에서 재현되는지 확인한다.
4. 표현 유사도×원천 동일성을 교차하고 문헌·길이·언어·검색 순위·budget 차이가 효과를 설명하는지 검사한다.
5. GLRS와 단순 정확도/F1/count 점수를 전문가의 블라인드 출력 평가와 비교한다. strict gate의 0점·동점률 및 대안 근거의 부당한 감점도 검사한다.

현재 구현한 harness·replay·그룹 검증은 평가를 수행할 기반이다. 실제 과학적 신규성은 아직 입증하지 않았다. CSV의 9개 모범 문항은 라벨링 연습용으로, 본 분석용 교차 논문 family나 B/R/N gold가 아니다. DOI/text dedup으로 대부분 해결되거나 지표가 사람 평가에 추가 설명력을 주지 못하면 새 능력·primary metric 주장을 낮추거나 연구 질문을 수정한다.
