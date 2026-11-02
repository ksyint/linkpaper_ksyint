# 실제 논문 수집 예시: 영어 6편 + 한국어 1편

2026-11-02 공식 출판사·학회 사이트에서 **PDF 7편, 총 12,847,303 bytes(약 12.25 MiB)**를 실제로 내려받았다. `raw/`에 원본 PDF, `local_text/`에 로컬 추출문과 검토용 페이지 렌더링을 두었다. 두 디렉터리는 Git에서 제외한다. GitHub에는 직접 작성한 수집 설명·질문 초안·메타데이터·재현 스크립트만 올린다.

이는 수집 절차를 설명하는 **관계 탐색용 seed 예시**다. 영어 6편/한국어 1편은 이 작은 예시의 구성일 뿐 최종 언어 할당량이 아니다. AI 논문 외에 해양환경·생물다양성 논문도 포함했으며, AI 여부는 포함 조건이 아니다. 유명한 고전 논문을 썼으므로 모델의 사전 지식 노출 가능성이 높다. 이 묶음으로 숨겨진 최종 시험 성능·최신성·분야 대표성을 주장하지 않는다.

**완료한 gold case 0개, 완성한 B/R/N triplet 0개다.** 본문 언어·서지 정보·파일 해시·근거 후보 위치를 확인한 수집 초안이며, 사람 2인의 독립 검수나 결과 계보 adjudication은 아직 수행하지 않았다. `benchmark_eligible=false`, `annotation_status=review_pending`을 모든 원천·후보·질문에 기록했다. DOI, 논문 수, 다른 저자, 인용 관계만으로 독립 결과 수를 정하지 않는다.

사람이 실제로 작성하는 방법은 [CSV 모범 예시](csv_labeling/README_KO.md)에 추가했다. 공유 예시 3편에 대해 **논문마다 3문항씩 총 9개**의 근거 연결 QA를 작성했다. 숫자·단답·설명·판정 답을 포함하며, 필요한 논문 수는 공개 질문에 알리지 않는다. 이번 실제 예시는 한 논문 안의 설정·방법·표·본문을 연결하는 연습이고 결과 원천은 하위 task 중 하나다. 교차 논문 task 실데이터가 확보되었다고 주장하지 않으며, 빈 CSV와 교사용 모범답안·근거 연결 단계를 별도로 제공한다. 교육용 작성 예시이며 검수 완료 gold가 아니다.

## 무엇을 모았고 어떻게 사용할 수 있는가

아래 쪽수는 다운로드한 **PDF의 1부터 시작하는 페이지 번호**다. 인쇄·서지 쪽수와 혼동하지 않는다. 표·그림 후보는 로컬 PDF를 렌더링해 확인했다. 질문은 여기서 새로 작성한 작업 초안이며 기존 벤치마크 문항을 가져오거나 번역하지 않았다. 수치·과학적 결론의 최종 판정은 별도 검수 대상이다.

| ID / 분야 / 본문 언어 | 실제 자료와 근거 후보 | 새로 작성한 질문 초안에서 확인할 것 |
|---|---|---|
| `ioffe15` / 머신러닝 / 영어 | Ioffe·Szegedy, ICML 2015. PDF p.7, §4.2.2와 **Figure 3의 표 형태 결과**. [공식 논문](https://proceedings.mlr.press/v37/ioffe15.html) | BN만 추가한 비교군과 학습률·정규화 등을 함께 변경한 비교군을 구분하고, 훈련 단계 수와 최대 정확도의 조건을 함께 기록한다. Figure 3을 임의로 Table 3이라고 부르지 않는다. |
| `finn17a` / 메타러닝 / 영어 | Finn·Abbeel·Levine, ICML 2017. PDF p.7, Table 1 및 caption; 설정은 p.6 §5.2. [공식 논문](https://proceedings.mlr.press/v70/finn17a.html) | Omniglot과 MiniImagenet, way/shot, 정확도와 구간을 분리한다. Caption의 과거 비교군 출처와 split 비교 제한도 추적한다. 이전 논문에서 가져온 baseline 행을 이번 논문의 새 실험으로 자동 계산하지 않는다. |
| `chen20j` / 표현학습 / 영어 | Chen 등, ICML 2020(SimCLR). PDF p.7, Table 6·7 및 §6. [공식 논문](https://proceedings.mlr.press/v119/chen20j.html) | 선형 평가와 소량 라벨 fine-tuning, top-1/top-5, ResNet 폭을 구분한다. 같은 ImageNet 이름만 보고 다른 프로토콜의 숫자를 직접 비교하지 않는다. |
| `wang20k` / 표현학습 / 영어 | Wang·Isola, ICML 2020. PDF p.8 Table 1; p.9 Table 2; p.10 References의 Chen 등 항목. [공식 논문](https://proceedings.mlr.press/v119/wang20k.html) | STL-10/NYU-Depth-v2 등의 평가 조건과 선택 규칙을 추적한다. SimCLR의 논문을 인용하지만 그 사실만으로 실험 결과의 원천이 같다고 판정하지 않는다. |
| `min2024` / 한국어 자연어처리 / **한국어** | 민수영·고영중, 「트랜스포머 인코더를 활용한 음절 단위 경량화 형태소 분석기」, 정보처리학회 논문지 13(10), 2024. PDF p.4 Table 2, p.5 Table 3·4, §4.3–4.5. [공식 논문](https://tkips.kips.or.kr/digital-library/101425), [DOI](https://doi.org/10.3745/TKIPS.2024.13.10.553) | 계층 수·임베딩 차원을 조건으로 음절 정확도와 어절 정확도를 나누고, KorBERT 대비 파라미터 비율을 다른 지표로 기록한다. p.1 영어 초록이 있어도 본문 언어는 한국어다. |
| `eriksen2014` / **해양환경** / 영어 | Eriksen 등, PLOS ONE 2014. PDF p.8 Table 1; 조사·모델 방법 및 단위 설명을 함께 확인한다. [공식 논문](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0111913) | 관측 표본과 해양 전체의 모델 추정을 구분하고 count/weight 열의 배율·단위를 함께 기록한다. 초록과 표의 반복 보고를 새 관측 결과 두 개로 세지 않는다. 이는 검수할 후보 관계다. |
| `mora2011` / **생물다양성** / 영어 | Mora 등, PLOS Biology 2011. PDF p.5 Table 2; p.3 Table 1은 기존 추정법의 검토표다. [공식 논문](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1001127) | 등재된 종 수와 예측 종 수, 지구 전체와 바다, 표준오차와 신뢰구간을 구별한다. 기존 추정법 요약표를 저자의 새 종 수 실측 자료로 오인하지 않는지를 점검한다. |

## 실제 관계 후보와 아직 모으지 않은 것

`relationship_candidates.jsonl`에 실제 본문의 위치와 조사할 관계를 기록했다. Wang·Isola PDF p.10의 References에는 Chen 등 논문의 **arXiv:2002.05709**가 있다. 현재 수집한 SimCLR 파일은 ICML 출판 PDF다. 따라서 “같은 연구의 어떤 버전인가”부터 확인해야 하며, 해당 인용을 현재 PDF 바이트에 대한 참조라고 바꾸어 쓰지 않는다. `observed_relation=cites_work`, `target_version_resolution=review_pending`으로 남겼다.

그 외 같은 논문의 초록·본문·표가 같은 결과를 설명하는지, 과거 baseline의 수치가 재인용인지 새 재실험인지는 **검토 후보**다. 아직 미수집된 원 논문·부록·코드·실험 기록을 추가로 확보해야 한다. 이 7편만으로 관련 문헌 family가 완성되거나 reported result unit의 distinctness가 확인된 것은 아니다. 연구 질문에 맞는 원천을 더 모은 뒤 동일 출처 반복 R, 실제 새 결과 N, 기본 B를 문서 수·언어 구성·예산·질문·조건이 맞게 구성한다.

## 수작업으로 해야 하는 일

1. 수집자가 원본과 해시를 고정하고, 표의 정확한 행·열·평가 split·지표·단위·실험 조건을 `evidence_candidates.jsonl`에서 실제 atomic evidence 레코드로 다듬는다. 자동 PDF 추출이 성공해도 표 구조와 수치의 정답을 보장하지 않는다.
2. 작성자와 겹치지 않는 두 검수자가 원문을 각각 보고 결과 원천, 반복 보고, 새 실행, 조건 불일치, 확인 불가를 독립 라벨링한다. 이전 라벨을 서로 보지 않는다. 인용 여부와 same-result 여부는 별도 필드다.
3. 충돌을 adjudication하고, 근거·미해결 사항·부정 사례를 남긴다. 확인할 수 없는 원천은 `unknown`으로 유지한다. 과학적·통계적 독립성이라는 넓은 의미와 여기서 정의할 **보고된 결과 단위의 구별**을 혼동하지 않는다.
4. 권리 범위를 검수하고 질문을 수정한 뒤에만 정식 벤치마크 편입 여부를 결정한다. 공개한 이 예시 질문은 숨겨진 test 문항으로 재사용하지 않는다. 사람 이름으로 검수 완료 서명을 대신 쓰지 않았다.

## 파일과 재현

- `sources.json` / `sources.csv`: 출처·저자·분야·언어·버전·바이트 수·SHA256·개별 이용 조건과 근거 URL.
- `evidence_candidates.jsonl`: 원문 위치와 원자적 결과 후보. `study_unit_id=null`이며 gold가 아니다.
- `question_drafts.jsonl`: 직접 작성한 한국어 질문 8개. 정답·정확도·GLRS 점수 없음.
- `relationship_candidates.jsonl`: 관측한 인용과 아직 판정하지 않은 반복/원천 관계 후보.
- `RIGHTS_KO.md`: 원천별 권리 증거와 미확인 범위.
- `collection_summary.json`: 실제 파일 수·용량, 아직 0개인 gold/triplet 상태.

```bash
cd collection_examples/20261102
python download_examples.py --verify-only
# 다른 환경에서 동일 파일을 다시 수집할 때:
python download_examples.py
# 일부만 선택:
python download_examples.py --ids eriksen2014 mora2011
```

기존 파일이 있으면 네트워크 호출 없이 해시를 검증한다. 출판사가 PDF를 바꾸면 실패하며, 수정된 버전의 해시를 임의로 덮어쓰지 않는다. 원문 파일이나 추출 텍스트를 Git에 강제로 추가하지 않는다. 데이터 수집과 검증에는 CPU만 사용했으며 GPU·LLM·이전 OCR 서버를 호출하지 않았다.
