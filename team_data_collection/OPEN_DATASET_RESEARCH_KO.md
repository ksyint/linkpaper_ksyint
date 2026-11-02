# 기존 공개 논문 데이터셋 조사와 재사용 계획

조사일: 2026-11-02. 이 문서는 [팀 데이터 수집·라벨링 안내](DATA_COLLECTION_KO.md)의 보조 자료다. 질문은 **이미 쓸 만한 자료가 있는가**다. 답은 **있다**. 특히 영어 논문에는 단일 논문 근거 QA와 여러 논문 합성 QA가 모두 공개되어 있다. 한국어 논문 자료도 존재하지만, 확인한 KISTI 자료는 활용 신청과 재배포 제한이 있어 공개 벤치마크에 그대로 묶을 수 없다. 이 조사는 각 제공자의 공식 자료를 읽은 결과이며, 데이터 파일 전체를 다운로드하거나 개별 문항을 재검수한 결과는 아니다.

여기서 `공개`는 웹에서 찾을 수 있다는 뜻이고, `재사용 가능`은 각 데이터 **자체**의 이용 조건을 확인했다는 뜻이다. 코드 저장소의 MIT/Apache 라이선스가 논문 PDF나 QA 데이터에 자동으로 적용되지는 않는다. 공개 데이터의 질문을 그대로 옮겨 새 test라고 부르지 않는다.

## 1. 바로 비교하거나 개발에 쓸 후보

| 후보·공식 자료 | 들어 있는 것과 우리 과제의 접점 | 확인된 이용 조건·경계 | 권장 용도 |
|---|---|---|---|
| [ScholarQABench](https://github.com/AkariAsai/ScholarQABench), [OpenScholar 논문](https://www.nature.com/articles/s41586-025-10072-4) | 여러 논문을 찾아 과학 문헌을 합성하는 질문·전문가 답·평가 rubric. CS 외 물리·생의학·신경과학도 포함. **우리의 가장 직접적인 선행 벤치마크**다. | 저장소는 `data/`의 집합 테스트 사례 등에 **ODC-BY**를 명시하며 구성 데이터별 이용 조건도 별도 확인하라고 한다. 저장소 코드의 MIT와 구분한다. | 동일 데이터에서 비교 baseline·rubric/인용 평가 재현. 신규 test는 독립 질문·독립 근거로 만든다. |
| [LitTraceQA](https://huggingface.co/datasets/LitTraceQA/LitTraceQA), [논문](https://arxiv.org/abs/2608.07370) | 숨겨진 원천을 찾는 단일/다중 논문 질문, `paper_id`·근거 위치·답을 함께 제출. 공개 validation 55개에는 단일 26개·다중 29개가 있다. 표·그림·본문·수식도 다룬다. **가장 가까운 retrieval+grounding 비교 대상**이다. | 주석·벤치마크 파일 **CC BY-NC 4.0**. 제공자는 PDF를 재배포하지 않고, test gold는 숨긴다. 큰 `test_extra`는 사람 검증이 안 된 진단용이라고 명시한다. | 공식 validation/평가 프로토콜과 비교; 우리 신규성 주장에는 반드시 이 연구와의 차이를 실제 실험으로 제시. 비상업 조건 준수. |
| [PaperScope](https://huggingface.co/datasets/Youxll/PaperScope), [논문](https://arxiv.org/abs/2604.11307) | AI 논문 2천여 편의 지식 그래프에서 만든 다중 논문 검색·추론·요약·문제 해결 과제. 공개 개발 corpus와 비공개 test를 구분한다. 에이전트 평가라는 점까지 겹친다. | 카드 상단은 `apache-2.0`으로 표시하지만 **카드 본문의 데이터 라이선스는 CC BY-NC 4.0**이라고 적혀 있어 표시가 충돌한다. 공개본은 주로 논문 ID이고 PDF는 포함하지 않는다. | 직접 비교할 선행연구로 검토. 데이터 이용은 더 제한적인 본문 조건을 기준으로 보고, 재배포 전 제공자에게 확인한다. AI·시각 자료 중심이라는 범위 차이를 기록. |
| [MDAQA](https://huggingface.co/datasets/YeloDriver/MDAQA), [구축 코드](https://github.com/YeloDriver/MDAQA), [논문](https://aclanthology.org/2025.findings-emnlp.576/) | 6,804개 영어 다중 논문 QA. 데이터 행에 `question`, `answer`, 2~4개의 논문 ID가 든 `support`가 있다. 인용 네트워크와 LLM으로 질문을 만들고 자동 필터링했다. | 데이터 카드 **CC BY 4.0**, 코드 저장소 **Apache 2.0**. 원 논문 본문 권리는 별개. `support` 논문 ID만으로 정확한 근거 span·조건·대안 충분근거 집합이 검증된 것은 아니다. | 다중 논문 검색·답 생성의 공개 비교, 문제 유형 분석, 사람 검수 대상 후보. 자동 생성 답을 우리 gold로 승격하지 않는다. |
| [QASPER](https://huggingface.co/datasets/allenai/qasper) | 1,585개 NLP 논문에서 5,049개 질문. 논문 본문 구조와 답의 근거 표시가 있다. **한 논문 안의 떨어진 근거 찾기**에 유용하다. | 데이터 카드 **CC BY 4.0**. 원 논문 PDF의 별도 권리 확인 필요. NLP·단일 논문에 치우치고 모든 문항이 공개되어 있다. | 단일 논문 개발/진단, 증거 찾기 baseline. 우리 숨겨진 다중 논문 test와 섞지 않는다. |
| [PeerQA](https://huggingface.co/datasets/UKPLab/PeerQA), [제공자 코드·설명](https://github.com/ukplab/peerqa) | 208개 논문, 579개 QA. 동료심사 질문과 논문 저자 답, 증거 문장·답 불가 라벨. ML/NLP 외 지구과학·공중보건 일부. | 데이터 카드 **CC BY-NC-SA 4.0**. 제공자는 논문별 권리 때문에 PDF를 묶어 배포하지 않는다고 설명한다. | 현실적인 질문·근거·정보 부족 판정의 진단/비상업 비교. 논문 간 합성 gold로 간주하지 않는다. |
| [SciFact](https://huggingface.co/datasets/allenai/scifact), [원 제공자](https://github.com/allenai/scifact) | 과학 주장에 대한 지지/반박과 **초록의** 근거 문장. 주장 판정·근거 검색의 작은 비교군. | 데이터 카드 **CC BY-NC 2.0**. 대체로 생의학 초록이며 방법·조건·표가 있는 논문 전문 과제와 다르다. | 주장 인증/반박 진단. 전문 기반의 복합 질문 gold로 확대 해석하지 않는다. |
| [SciFact-Open](https://github.com/dwadden/scifact-open), [필드 명세](https://github.com/dwadden/scifact-open/blob/main/doc/data.md) | 약 50만 개 과학 초록에서 열린 검색을 하는 주장 검증. 어려운 후보 검색·negative 분석에 유용하다. | 이 조사에서는 데이터 자체의 재배포 허락을 확인하지 못했다. `provenance=pooling`의 highlighted sentences는 **모델 예측**이고, `citation` 쪽만 사람 표시라는 제공자 설명이 있다. | 권리 확인 후 내부 retrieval 진단. `pooling` 표시를 사람 gold 근거로 쓰지 않는다. |

ScholarQABench·LitTraceQA·PaperScope·MDAQA가 이미 **여러 논문에서 답을 찾는 문제**를 다룬다. 따라서 `multi-paper QA 최초`, `paper retrieval 최초`, `근거 위치 평가 최초`, `논문 에이전트 평가 최초` 같은 주장은 성립하지 않는다. 우리 논문에서 시험할 차이는 **필요한 논문 수를 미리 주지 않는 단일/다중 혼합**, **논문 내·논문 간 방법/조건/수치/결과의 충분근거 연결**, **검색→확보→열람→답/종료의 단계별 실패**, **동일 문항의 오프라인·live·replay 비교**, **한국어 질문과 영어 우세·한국어 원문 포함**, **재보고/새 결과 구별 하위 과제**의 결합이다. 이것도 새롭다는 결론이 아니라 **실험으로 입증할 가설**이며, 공개 선행 benchmark와 겹치는 문항·문헌 family를 감사해야 한다.

## 2. 논문 발견·본문 후보와 평가 프레임워크

| 자료 | 확인한 범위 | 권장 판단 |
|---|---|---|
| [OpenAlex](https://help.openalex.org/data/how-its-built/) | 논문 ID·DOI·인용 관계·공개 접근 링크를 찾는 서지 데이터. 제공자는 OpenAlex **데이터 자체를 CC0**라고 명시한다. 이는 링크된 출판사 PDF의 권리까지 CC0라는 뜻이 아니다. | 영어·한국어 source 후보와 citation family·중복 확인에 우선 사용. PDF마다 별도 권리·버전 기록. |
| [peS2o](https://huggingface.co/datasets/allenai/peS2o) | Ai2의 대규모 공개 접근 논문 텍스트 corpus; 카드 라이선스 **ODC-BY**. S2ORC 기반, 영어와 다양한 학문 분야가 중심이다. | 대규모 오프라인 검색 corpus 후보. 전체 복제보다 필요한 문헌 subset만 권리와 버전을 확인. 이 corpus에는 우리 QA gold가 없다. |
| [AstaBench](https://github.com/allenai/asta-bench), [공식 소개](https://allenai.org/asta/bench) | PaperFindingBench, ScholarQABench2, LitQA2 전체 텍스트 검색 등 에이전트 문헌 탐색 평가를 제공한다. | **비교 실행 프레임워크**로 검토. 저장소는 별도 HF 데이터셋의 gated license 수락을 요구하므로 코드 Apache 2.0만 보고 데이터 접근·재배포를 가정하지 않는다. |
| [SPIQA](https://huggingface.co/datasets/google/spiqa), [제공자 코드](https://github.com/google/spiqa) | 논문 그림·표 QA와 추출 본문. 데이터 카드 **CC BY 4.0**, 평가 코드의 Apache 2.0은 별도 표기다. | 현재 본 track은 텍스트·사람이 확인한 표 셀을 평가하므로 직접 편입하지 않는다. 향후 시각 자료 track을 열면 비교군. |
| [M3SciQA](https://huggingface.co/datasets/yale-nlp/M3SciQA), [논문](https://arxiv.org/abs/2411.04075) | NLP 논문 군집 70개에서 약 1.45천 개의 사람 주석 질문. 기준 논문의 그림/표를 읽고 인용 논문을 찾는 **다중 문서·멀티모달** 과제. 데이터 카드 **CC BY 4.0**. | 본 track의 텍스트·표 셀 목표와 다르지만 강한 인접 비교군. 시각 확장 시 재평가하고 원 논문·그림 권리를 별도 점검. |

## 3. 한국어 논문: 유용하지만 공개 재배포에 제한이 있는 자료

| 공식 자료 | 내용 | 이용·품질 상태 | 우리 팀의 처리 |
|---|---|---|---|
| [KISTI 국내 논문 QA v2.0](https://aida.kisti.re.kr/data/aab572f0-c5b7-48f6-b775-516af0f77d0f/) | 한국어 논문 `doc_id`, 본문 `context`, 질문·추출형 답 `qas`, 난이도 등. | **활용신청**, 비영리 이용·출처 표기·**재배포 금지**. 논문 원문 저작권은 학술지/학회에 있다고 명시한다. 단일 논문 추출형 QA라서 우리 다중 근거 질문과 다르다. | 신청 승인을 받으면 접근 조건 범위에서 **내부** 한국어 검색·질문 유형 진단. 원문·기존 QA·파생물을 공개 Git/배포물에 넣기 전 별도 허락 확인. |
| [KISTI 국내 논문 전문 텍스트](https://aida.kisti.re.kr/data/b22c73ed-fa19-47b0-87b3-a509df8380e5) | 국내 논문 PDF에서 추출한 문단·문장 JSON. 표/그림/알고리즘 **실제 개체는 빠지고 캡션만** 편집했다는 제공자 설명이 있다. | **활용신청**, 비영리·출처 표기·**재배포 금지**, 원문 저작권 별도. | 승인 시 내부 corpus 후보. 본문 표 셀과 시각 근거 gold는 원 PDF에서 다시 확인. 공개본에 전문 복사 금지. |
| [KISTI 과학기술 논문 RAG](https://aida.kisti.re.kr/data/fc4da4bd-61b1-43ae-b394-4d52dff96c1a) | 한국어 질문·답·key sentences/phrases·`gold_passage_id`를 제공하는 논문 RAG 자료. 원천은 KISTI/ETRI 자료로 표기된다. | **활용신청**, 비영리·출처 표기·**재배포 금지**. 설명에는 LLM을 활용한 답 생성과 검증 과정이 있어 답 전부를 독립 전문가 gold로 볼 수 없다. | 승인 후 내부 retrieval 개발 후보. 위 QA/전문과 원고·질문 중복 가능성을 먼저 점검하고 split 누출 방지. |
| [HF `amphora/korean_science_papers`](https://huggingface.co/datasets/amphora/korean_science_papers) | 한국어 과학 논문 전문으로 보이는 공개 업로드. | 조사 당시 카드에 원문 권리·명확한 데이터 라이선스를 확인하지 못했다. HF 공개 업로드 자체가 재배포 허락은 아니다. | **사용 보류**. 원 출판사·수집 경로·이용 허락이 확인되기 전 복제/색인/공개 예시에 포함하지 않는다. |

KISTI 자료는 **“오픈소스 데이터셋”으로 분류하지 않는다.** 연구에 유용한 접근 제한 후보로 따로 기록한다. 한국어 원문을 포함하는 공개 평가셋은 이 자료의 질문을 옮기는 방식보다, **논문별 권리를 확인한 원문**에서 팀이 독립적으로 질문·근거·정답을 쓰고 두 사람이 검수하는 경로를 우선한다. 접근 허가가 생기더라도 허가 범위 밖의 공개 배포가 가능한지는 별도로 확인한다.

## 4. 수집·라벨링에 반영할 순서

1. **공개 baseline부터 재현:** ScholarQABench·LitTraceQA처럼 공식 평가 절차가 제공되는 자료는 해당 split·scorer를 사용한다. MDAQA·PaperScope는 공개 개발 문항과 평가 접근권을 먼저 확인하고, 동일 입력·동일 scorer로 비교할 수 있는 범위만 보고한다. 데이터셋/버전/라이선스/실행 모드/사용 corpus를 명시하며 서로 다른 벤치마크 점수를 같은 척도로 합치지 않는다. `LitTraceQA test_extra`의 미검수 문항은 주 결과에서 분리한다.
2. **개발용 증거 찾기:** QASPER의 본문+근거, PeerQA의 답 불가, SciFact의 지지/반박을 **auxiliary/dev**로 활용한다. 비상업·동일조건·출처 표시 요구가 붙은 자료는 해당 조건에 맞는 실험에서만 사용한다. 공개 기존 QA를 신규 hidden test에 넣지 않는다.
3. **새 평가 문항:** OpenAlex/arXiv/발행처에서 원천 후보를 찾고, DOI·arXiv ID·출판 버전·PDF hash·원문 권리를 기록한다. 영어 논문을 다수로 하고 한국어도 포함하며 AI 외 분야를 담는다. 질문·답·근거 연결 단계·조건·대안 충분근거 집합은 팀이 원문을 보고 새로 작성하고 R1/R2 독립 검수한다. [CSV 양식](templates/)과 [기존 작성 절차](DATA_COLLECTION_KO.md)를 따른다.
4. **중복·오염 감사:** 새 문항과 기존 benchmark의 질문 문구뿐 아니라 DOI, arXiv family, 같은 결과를 재보고한 논문, 번역 질문, 원고 버전, 개발에 사용한 공개 예시를 대조한다. 겹침은 `source_family`와 사용 목적에 기록하고 같은 family가 train/dev/test를 가로지르지 않게 한다. 공개 선행 QA를 보고 만든 문항은 “독립 hidden”으로 주장하지 않는다.
5. **오프라인/live의 같은 문제 비교:** 권리가 확인된 원천만 오프라인 archive에 넣고, live는 실제 검색·PDF 확보 경로와 실패를 기록한다. 외부 데이터셋에 이미 주어진 gold 논문 ID를 live 에이전트의 입력으로 주지 않는다. 현재 자동 live provider는 arXiv이므로 한국어 발행처 문항은 지원 여부를 분리 보고한다.

**현재 결론:** 기존 자료만으로 영어 단일·다중 논문 QA의 baseline과 개발 실험은 시작할 수 있다. 반면 우리 질문의 **대안 충분근거 집합·과학적 조건의 정확성·탐색 과정·멈추는 시점·한국어 원천**을 평가하려면 원문 확인과 신규 수작업 라벨이 여전히 필요하다. 이 문서는 후보와 이용 조건의 조사 기록이다. 실제 데이터 접근 허가, 파일 검수, 모델 성능, 신규성 증명은 완료 상태가 아니다.
