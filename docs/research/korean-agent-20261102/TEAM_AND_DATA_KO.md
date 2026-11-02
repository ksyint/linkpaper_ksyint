# 공저자별 데이터 수집·주석·검증 계획

기준일: 2026-11-02. **김수용이 제1저자이며, 정상헌·남두현·오창원·이상민의 저자 순서는 정하지 않는다.** 아래 표의 순서는 운영용 순환 배치다. 김대건·홍예린은 이 계획의 구성원이 아니다. 역할은 연구에 필요한 산출물에서 새로 배분했으며, 이름으로 개인의 전문성이나 기존 직무를 추정하지 않았다. 실제 가용 시간과 분야 이해도를 첫 회의에서 확인한다.

이 문서는 아직 수집하지 않은 실제 데이터나 실행하지 않은 평가 결과를 만들었다고 주장하지 않는다. 40개 pilot와 240/300개 확장 규모는 아래 조건을 확인하기 위한 계획이다. 문헌 조사만으로 main conference 채택이나 선행연구 부재를 보증하지 않는다.

## 1. 무엇을 새로 수집하고 라벨링하는가

후보 연구 질문은 **한국어를 주된 언어로 쓴 기술 논문·연구보고서에서, 여러 문헌이 언급하는 실험 결과가 같은 원래 결과의 재서술인지, 문헌상 새로 보고된 실험 단위인지 에이전트가 근거와 조건을 추적할 수 있는가**이다. 최종 기여의 범위와 선행연구 대비는 별도 연구 설계/문헌 문서에서 검증한다. 일반적인 문서 유효성 판정, counterfactual·중복 교란, citation checking 자체를 새 능력으로 소개하지 않는다.

여기서 **결과 계보(result provenance lineage)**와 **통계적 독립성(statistical independence)**은 다르다.

- 서로 다른 논문·저자·DOI라는 이유로 독립 실험이라고 라벨링하지 않는다. 동일 저자의 후속 논문도 새 실험을 보고할 수 있고, 다른 저자의 논문도 같은 표나 원래 결과를 다시 인용할 수 있다.
- 수치가 같다는 사실만으로 같은 실험이라고 하지 않는다. 우연히 같은 수치가 나온 경우, 반올림, 공통 baseline 표가 있을 수 있다.
- 다른 실험 조건의 새 결과 보고라고 해도 학습/평가 데이터·측정 장비·참여 집단·시드·시료를 공유할 수 있다. **새 reported unit 라벨은 통계적 독립성의 증거가 아니다.**
- 새 실험 수행이나 원래 결과의 재사용 여부를 원문에서 확인할 수 없으면 `unresolved`로 남긴다. 독립성은 확인할 자료가 없으면 `not_assessed` 또는 `unknown`이다. `new_reported_unit`을 `independent_study`로 자동 변환하는 필드는 만들지 않는다.

### 1.1 주석 단위

| 단위 | 필수 내용 | 추정으로 채우지 않는 것 |
|---|---|---|
| source document | 원본 URL/DOI 또는 발행기관 문서 ID, 버전, 본문 언어, 문서 hash, 이용 조건 | DOI가 없는데 DOI를 만들어 넣지 않음 |
| reported result unit | 원문상 실험/측정/분석 식별자, 결과 위치, 조건, 결과값/범위, 해당 단위를 보고했다고 판단한 근거 | 독자 재현 실험을 했다는 추정 |
| claim mention | 사람이 짧게 재서술한 주장, 그 주장이 등장한 문서와 문단/표 위치 | 문서 전체가 주장을 지지한다는 포괄 판정 |
| lineage edge | 두 mention/unit 사이의 관계, 출처를 잇는 실제 근거, 판정 가능성 | 인용 링크가 있다는 이유만으로 결과 재사용 확정 |
| base case | 한 개의 독립적으로 작성한 한국어 연구 질문과 필요한 source bundle, gold 판정 대상 | 기존 benchmark 질문 번역·어휘 교체 |
| language variant/run | 같은 base case의 영어 질문, 표기 변형, 반복 실행 | 새로운 독립 표본 수로 계산 |

문서의 결과 단위는 원문이 식별 가능한 수준까지만 자른다. 예를 들어 한 논문의 동일 실험군을 여러 표/문단에서 보고한 경우 한 계보의 여러 mention이 될 수 있다. 같은 데이터셋에서 새 방법이나 조건의 실험값을 별도로 보고했다면 새 reported unit일 수 있지만, 같은 study/evaluation family에 묶일 수 있다. 어떤 경우든 실험 단위의 세분화 규칙을 codebook과 주석 근거에 남긴다.

### 1.2 edge 판정 초안과 유보 조건

아래 이름은 pilot에서 검증할 운영용 제안이다. 구현 schema와 최종 codebook의 용어를 일치시킨 뒤 동결한다.

| 관계 | 채택에 필요한 원문 근거 | 반례/유보 |
|---|---|---|
| `same_result_restatement` | 원래 표/결과/실험을 특정해 재인용·재서술한다는 내용과 조건/값의 대응 | 숫자만 같음, 제목/저자만 비슷함 → 확정 불가 |
| `new_reported_unit` | 새 실험/분석/측정 수행 또는 새 조건별 결과 보고를 원문에서 식별 가능 | 논문이 다르다는 사실만 있음 → `unresolved` |
| `partial_reuse_or_extension` | 기존 결과의 일부 재사용과 추가 실험/조건의 범위를 각각 식별 가능 | 기존/추가 부분 경계가 불명확하면 유보 |
| `unresolved` | 공개 자료로 관계를 확정할 수 없음, 원문이 필요한 식별 정보를 주지 않음 | 검증 실패를 임의의 새 단위로 처리하지 않음 |

별도 필드 `statistical_independence_status`는 기본 `not_assessed`다. 원문이 데이터/표본 공유를 명시하면 `shared_components_reported`와 그 근거를 기록할 수 있다. 이 라벨도 통계적 독립성을 완전히 판정했다는 뜻은 아니다. 명시적인 분석 없이 `independent`를 출력하게 하는 task는 pilot 범위에서 제외한다.

확정 계보를 묻는 track과 공개 정보 부족을 인지해야 하는 track을 분리한다. `unresolved` 사례의 gold는 근거 있는 유보다. 미확인 unit을 0 또는 1로 강제해 단일 정답 개수를 만들지 않는다. 가능한 상·하한이 실제로 검증된 경우에만 범위 정답을 만들고 그 증명 근거를 남긴다.

## 2. 후보 수집은 gold 작성과 분리한다

상태 전이는 `candidate → rights_reviewed → source_verified → drafted → independently_annotated → adjudicated → frozen`이다. 각 단계의 보류/탈락 이유도 남긴다. 자동 검색이나 파서 산출물은 `candidate`일 뿐이다. LLM이나 citation graph가 제안한 unit/edge는 사람이 원문으로 확인하기 전 gold로 사용할 수 없다.

### 2.1 확인한 공식 탐색 경로

| 경로 | 사용할 범위 | 확인한 공식 근거/주의 |
|---|---|---|
| [KCI KOAJ 학술지·논문 안내](https://www.kci.go.kr/kciportal/landing/about.kci?landingSearchBean.aboutDiv=3) | 한국어 기술 논문 후보, 발행기관·DOI·원문 제공처 확인 | KOAJ는 KCI 등록 학술지/논문 탐색 서비스다. `Full Text` 표시를 재배포 허가로 해석하지 않음 |
| [KJCI 저작권 정책 안내](https://copyright.oak.go.kr/faq.do) | 학술지별 저작권·CC·셀프아카이빙·원문 접근 조건의 출발점 | 최종 선택 문서의 publisher/버전별 조건과 함께 확인. 열람 가능과 재사용 허가는 구분 |
| [NKIS 연구보고서 탐색 도움말](https://www.nkis.re.kr/onlineHelper.do) | 발행기관·주제·시기별 연구보고서 후보와 원래 발행기관 페이지 추적 | 보고서별 이용 조건을 확인. 정책 제언만 있고 원래 실험/측정 결과가 없는 문서는 main 대상 아님 |
| 각 선택 문서의 발행기관/학회 공식 원문 페이지 | 최종 원문·수정본·erratum·부록과 라이선스 증거 확보 | 이 문서가 일괄 crawling 허가나 특정 API endpoint의 동작을 보증하지 않음 |

ScienceON/기관 리포지터리 등 추가 탐색처는 후보로 확장할 수 있지만, 검증하지 않은 API·무제한 수집 권한·일괄 라이선스를 문서에 만들지 않는다. 이번 조사에서 일부 포털 첫 화면의 fetch가 실패했으므로 자동 수집 가능성을 실증했다고 쓰지 않는다. 검색 결과에서 발견한 미러보다 원래 발행기관과 문서 버전을 우선 확인한다.

모든 사람은 새로운 검색어와 source pool에서 출발한다. K-BrowseComp/KoTAU의 문제·정답·gold chain·seed 목록·생성 프롬프트를 수집 시드로 사용하지 않는다. 다른 benchmark를 비교 실험에 쓰는 경우도 원래 split과 인용을 유지한 별도 external evaluation으로 둔다.

### 2.2 pilot 모집단과 포함 조건

40개 base case를 목표로 하되, 처음에는 1인 32개씩 총 **160개 candidate record**를 수집한다. 25%가 통과한다는 것은 인력 산정을 위한 가정이며 채택률을 맞추려고 기준을 낮추지 않는다.

포함 조건은 다음과 같다.

1. 주요 방법/결과/해석이 한국어 본문으로 작성되어 있다. 한국인 저자나 한국 기관이라는 사실만으로 Korean-primary라 하지 않는다. 영어 초록만 있는 한국어 본문은 가능하며 언어 판정 근거 위치를 기록한다.
2. 한국어로 처음 작성한 질문이 특정 실험 조건과 결과의 출처를 확인하도록 요구한다. 영어 문제 번역본을 원본 한국어 문제로 제시하지 않는다.
3. 원래 결과와 후속 재서술/확장/검토를 연결하거나, 새 reported unit 여부를 확인할 수 있는 공개 자료가 있다. 기본 source bundle은 2~5개 문서, 핵심 mention 4~12개를 작업량 가정으로 한다.
4. text-first prototype에서 문단/표의 텍스트와 원문 locator를 사람이 대조할 수 있다. PDF 표가 필요하면 원본 page/table/row/column locator를 남기되 OCR 추출물만 gold로 삼지 않는다.
5. 해당 버전의 다운로드·내부 처리·주석 작성·재배포 범위를 각각 검토했다. 공개 test에 넣을 문서는 frozen corpus 또는 합법적인 재현 방법을 제공할 수 있어야 한다.
6. 두 명의 독립 reviewer와 제3자의 조정으로 판정 가능성을 검증할 수 있다. 분야 전문 판단이 팀 역량을 넘으면 외부 검토 또는 보류가 필요하다.

제외 또는 보류 대상은 로그인/유료벽 우회가 필요한 원문, 이용 조건이 불명확한 재배포 원문, 내부/민감 개인정보, 환자/개인 사례 식별 자료, 보도자료만으로 실험 수행을 추정하는 사례, 초록만으로 원래 결과가 확인되지 않는 사례, 근거 위치를 찾을 수 없는 자동 추출 문서, 다른 benchmark 문항의 번역/변형이다. survey 자체는 원래 결과의 재서술 여부를 검증할 연결 문서로 쓸 수 있지만 survey의 인용 수를 새 실험 수로 세지 않는다.

### 2.3 quota와 선정 편향 기록

pilot은 아래 다섯 탐색 영역에서 각 8개 base case를 목표로 한다. 각 사람의 영역은 후보 수집 담당일 뿐 독립 reviewer의 판정 권한을 제한하지 않는다.

- 정보통신·컴퓨터 성능 실험 8개
- 에너지·전기 성능/효율 실험 8개
- 기계·재료 성능/물성 실험 8개
- 환경·토목 측정/실험 8개
- 비임상 농업·생명공학 실험 8개

분야별 8개는 정밀한 분야 순위 추정용 표본이 아니다. 확보 가능성이 낮으면 분야를 임의로 바꾸기 전에 수정 사유와 날짜를 protocol log에 쓴다. pilot에서 한 발행처가 대부분을 차지하지 않도록 같은 학술지/기관에 최대 8개 base case, 같은 연구과제·실험 family에 원칙적으로 1개 base case를 목표로 한다. 연결 문서의 저자가 같은 것은 허용하고 그 때문에 자동 탈락시키지 않는다.

결과 관계의 목표 구성은 재서술 중심 12, 새 보고 단위 중심 12, 부분 재사용/확장 중심 8, 공개 정보 부족 중심 8개다. 이 비율은 **stress-test 층화 설계**이며 한국어 연구 문헌 전체의 발생률을 추정하는 표본이 아니다. 다중 관계가 있는 case는 주된 판정 대상으로 하나의 strata를 정하고 전체 edge 분포도 별도로 공개한다. 목표 quota가 불가능하면 사례를 만들어 채우지 말고 실제 가능 수와 탈락 원인을 보고한다.

후보 제외 전후의 분모, 검색어·날짜·포털·발행연도·기관·OA 조건, 누락 원인을 보존한다. agent 실패 여부로만 main test 문항을 선택하지 않는다. 개발용 adversarial stress set은 모집단 성능 추정과 분리해 표시한다.

## 3. 다섯 명의 정확한 산출물

모든 구성원은 자기 8개를 출제하고, 타인 16개를 독립 검토하며, 자신이 출제/검토하지 않은 묶음의 불일치를 조정한다. 아래 역할 산출물은 그 공통 데이터 업무에 더하는 책임이다. 각 역할은 특정 개인의 기존 역량을 가정한 평가가 아니다.

| 담당 | 후보 수집과 8개 base case | 추가 소유 산출물 | 직접 수작업/검증 |
|---|---|---|---|
| **김수용 — 제1저자** | KOAJ/발행기관의 한국어 정보통신·컴퓨터 논문: 평가 데이터/조건/metric이 명시된 결과와 후속 인용 문헌 | 연구 질문, unit/lineage codebook v1, episode·gold 경계, main protocol, 논문 주장–근거 장부 | 원래 reported unit 정의, 조건별 구분, 자기 8개와 타인 review, 조정 결과 검토. 자기 문항의 분쟁을 단독 확정하지 않음 |
| **정상헌 — 순위 미정** | 한국어 에너지·전기 기술 논문/공식 연구보고서: 효율/출력/측정 조건과 재서술 문헌 | `source_registry`·`rights_registry`, 버전/정정본 체크, 원문 hash·수집 로그 표준 | 문서별 실제 이용 조건/본문 언어/출처 확인, 같은 결과 인용 관계의 근거 위치, 자체 8개와 순환 review |
| **남두현 — 순위 미정** | 한국어 기계·재료 논문: 시료/장비/평가 protocol/조건이 식별되는 실험과 후속 보고 | 조건 표준화 사전, reported-unit/mention/edge annotation 지침, ambiguity register | 단위·조건·metric의 대응과 부분 재사용 경계, `unknown` 처리, 자기 8개와 순환 review |
| **오창원 — 순위 미정** | 한국어 환경·토목 측정/실험 논문: 측정 위치/기간/조건과 후속 보고 | 한국어 원문 질문–영어 질문 대응표, bilingual review rubric, valid-alternative-evidence 목록 | KO/EN의 지시 대상·범위·부정·시점·허용 유보가 같은지 검토. 자기 번역을 유일한 최종 검수자로 확정하지 않음 |
| **이상민 — 순위 미정** | 한국어 비임상 농업·생명공학 논문: 품종/처리/측정 조건과 결과 재인용·확장 보고 | split/family 중복 감사, pilot 통계·IAA 보고서, baseline budget/log 재현표 | source/version/연구과제/family 연결, 문항·언어 variant 누출 확인, 자기 8개와 순환 review |

전문 용어 이해가 부족한 reviewer는 그 사실을 기록하고 `domain_review_needed`로 넘긴다. 자신 있게 추측한 라벨로 disagreement를 없애지 않는다. 외부 분야 검토를 받으면 참여자·검토 범위·동의를 별도 기록하고 공저자 여부는 기여에 따라 팀이 판단한다.

### 3.1 출제자와 분리한 순환 review/조정 표

| 출제·source packet 담당 (각 8개) | 독립 reviewer R1 | 독립 reviewer R2 | 불일치 조정자 |
|---|---|---|---|
| 김수용 | 정상헌 | 남두현 | 오창원 |
| 정상헌 | 남두현 | 오창원 | 이상민 |
| 남두현 | 오창원 | 이상민 | 김수용 |
| 오창원 | 이상민 | 김수용 | 정상헌 |
| 이상민 | 김수용 | 정상헌 | 남두현 |

R1/R2는 출제자의 잠정 gold와 서로의 라벨을 보지 않고 같은 원문 packet과 같은 codebook으로 작성한다. source 발굴/질문 작성자의 gold 제안은 별도 잠금 열에 둔다. 조정자는 원래 두 reviewer도 출제자도 아니다. 사실을 추가 확인해야 하면 출제자에게 재수집을 요청할 수 있지만, 최초 라벨·수정 사유·추가 근거를 보존한다. 자기 문항이 다른 task family와 연결되어 누출 우려가 있으면 review 배치를 재지정하고 로그를 남긴다.

영어 질문은 출제자가 초안을 만들고 R1이 의미 대응을, R2가 영어만 먼저 읽은 뒤 요구 조건을 역정리하여 한국어 질문과 비교한다. 분야 용어는 source에서 확인한다. 영어 문장을 보기 좋게 바꾸면서 조건·유보 범위를 줄이지 않는다. 자동 번역/LLM 초안 사용 여부와 사람이 수정한 기록을 남긴다.

### 3.2 각 사람이 오늘 바로 시작할 업무

| 사람 | 오늘/첫 작업일 완료 기준 | 첫 주 말 검토 가능한 파일 |
|---|---|---|
| 김수용 | unit 대조 예시를 실제 권리 검토 완료 원문 2쌍으로 설명하고, 8개 질문 ID의 작성 양식 확정 | codebook 초안, 자기 후보 32행, 권리 통과 packet 4개, 범위/중단 기준 |
| 정상헌 | 모든 사람의 source sheet 필수 열과 rights 판정 기준 배포, 자기 후보 32행 | source/rights registry v1, publisher 정책 URL·확인일, 보류 사유 목록 |
| 남두현 | domain 공통 조건 표와 `unresolved`의 실제 판정 절차 작성, 자기 후보 32행 | unit/edge 주석 양식, 조건 사전 v1, 불명확 사례 기록 |
| 오창원 | 한국어/영어 질문에서 유지할 조건 체크리스트 작성, 자기 후보 32행 | bilingual 양식, 지시 대상/시점/조건/유보 검사표 |
| 이상민 | candidate/source/version/family ID 연결 규칙과 중복 검사 절차 작성, 자기 후보 32행 | split registry skeleton, candidate 중복 보고서, 시간 기록·IAA 양식 |

아직 원문 packet이 없으면 예시를 실제 데이터라고 작성하지 않는다. 빈 양식과 검토할 후보 URL만 제출한다. `8개 완성`은 자동 생성 행 8개가 아니라 rights·source·독립 review gate를 통과한 base case 8개다.

## 4. 표계산/JSONL에 남길 필드

전체 원문과 잠정/최종 gold는 공개 Git 작업 트리 밖의 접근 제한 저장소에 두고, 공개 가능한 schema·빈 양식·검증 코드만 Git에 둔다. credentials·개인 연락처·미공개 test 정답은 포함하지 않는다.

### 4.1 Source / rights 등록표

| 필드 | 형식/의미 |
|---|---|
| `source_id`, `candidate_id`, `collector` | 영속 ID와 담당자. URL이 바뀌어도 ID를 바꾸지 않음 |
| `discovery_url`, `canonical_url`, `doi_or_report_id` | 탐색 경로와 원래 발행처 식별자. 값이 없으면 null |
| `title`, `publisher`, `publication_date`, `version_id`, `supersedes_source_id` | 제목/발행자/날짜/버전·정정 관계 |
| `primary_language`, `language_evidence_locator` | 주요 본문의 언어와 확인 위치 |
| `fetched_at_utc`, `last_checked_at_utc`, `http_status` | ISO-8601 UTC 시각과 실제 접근 결과 |
| `raw_sha256`, `canonical_text_sha256`, `parser_name_version`, `parser_config_hash` | 원본/추출물 구분 및 변환 재현성 |
| `media_type`, `page_count`, `text_locator_scheme` | PDF/HTML 구분, 원본 위치 체계 |
| `rights_status`, `rights_evidence_url`, `rights_evidence_checked_at`, `rights_reviewer` | 허용/보류/불가의 근거와 독립 확인자 |
| `license_exact_text_or_identifier`, `permitted_version`, `access_allowed`, `internal_processing_allowed`, `redistribution_allowed` | 항목별 실제 확인값. 불명확하면 unknown |
| `privacy_screen_status`, `privacy_screen_reviewer`, `exclusion_reason` | 식별 가능한 개인정보/민감 내용 검토 |
| `storage_uri_private`, `release_artifact_policy` | 비공개 원문 경로와 URL-only/metadata-only/원문 포함 등 실제 허용 범위 |

권리 증거 자체의 원문/화면을 저장하는 경우도 허용 범위를 확인한다. 수집 가능한 라이선스라고 해서 모든 2차 표/그림의 권리가 같은 것은 아니다. 포털 검색 결과를 source 원문의 이용허락으로 대체하지 않는다.

### 4.2 Unit / mention / lineage 표

| 필드 | 의미 |
|---|---|
| `reported_unit_id`, `source_id`, `study_family_id`, `result_family_id` | 보고 단위와 source/연구 family 연결 |
| `original_unit_locator`, `reported_performed_locator` | 원래 결과·새 실험 수행/보고 판단 근거 위치 |
| `dataset_or_sample`, `dataset_version`, `population_or_material`, `sample_size_reported` | 원문상 식별 가능한 데이터/표본 조건. 미보고는 `not_reported` |
| `method_or_treatment`, `comparator`, `metric`, `unit`, `measurement_protocol`, `condition_values`, `time_window` | 결과를 구별하는 조건. 다른 물리량/metric을 같은 값으로 합치지 않음 |
| `reported_value_raw`, `reported_value_normalized`, `normalization_rule` | 원문 표기와 허용된 단위 변환 구분 |
| `mention_id`, `mention_source_id`, `claim_paraphrase_ko`, `page_section_table_cell` | 짧은 자체 재서술과 원문 locator |
| `exact_text_span_private`, `text_offset`, `span_hash` | 내부 확인용 span과 추출물 offset. 공개 인용량은 권리 검토에 따름 |
| `from_id`, `to_id`, `lineage_label`, `supporting_locators`, `link_evidence_type` | 결과 계보와 그 직접 근거 |
| `statistical_independence_status`, `shared_components_reported`, `independence_evidence_locator` | 기본 미평가. 자료 없는 독립성 추정 금지 |
| `uncertainty_reason`, `alternative_explanations`, `domain_review_needed` | 유보 이유와 가능한 대안 |

원본 page 번호와 PDF viewer page index가 다르면 둘 다 남긴다. 표 row/column, 각주, 단위 및 조건 문단을 함께 연결한다. OCR/파서 offset이 바뀌면 원본 hash·locator에 대응하는 수정 기록을 남긴다.

### 4.3 Question / annotation / adjudication / split 표

- Question: `base_case_id`, `author`, `candidate_ids`, `source_bundle_ids`, `task_family_id`, `question_ko`, `question_en`, `required_conditions`, `permitted_abstention`, `label_track`, `expected_answer_type`, `tool_budget`, `variant_id`, `language_reviewers`, `created_at_utc`, `revision`.
- Independent annotation: `base_case_id`, `reviewer_id`, `review_round`, `codebook_version`, `source_hashes`, `unit_ids`, `edge_labels`, `supporting_locators`, `accepted_alternative_evidence`, `possible_alternative_answer`, `uncertainty_reason`, `annotation_started_at`, `annotation_finished_at`. 출제자 gold를 보지 않았다는 기록을 포함한다.
- Adjudication: 원래 R1/R2 값, 불일치 종류, 추가 원문 확인, 조정자, 최종 라벨/유보, 변경 이유, 반영 codebook version, 처리 시각. disagreement 원본을 덮어쓰지 않는다.
- Split: `base_case_id`, `source_version_family`, `study_family_id`, `result_family_id`, `task_family_id`, `connected_component_id`, `split`, `freeze_at_utc`, `gold_visibility`, `release_status`. family 판단 근거와 unresolved 연결도 남긴다.
- Episode: model ID/version, endpoint 종류, 실제 입력 언어, prompt/tool/schema hash, corpus/snapshot hash, seed/repeat ID, 검색/읽기/token/시간 budget와 실제 사용량, tool trace, 오류·재시도, 최종 예측 및 채점기 버전. API/compute 비용은 원문/정답 파일과 분리된 실행 장부에 기록한다.

같은 source/result/study family의 버전·정정본·한국어/영어 질문·가벼운 paraphrase·반복 실행은 모두 같은 split connected component에 둔다. 확실치 않은 연결은 우선 보수적으로 같은 component에 묶고 확장이 너무 커지면 별도 split 정책을 문서화한다. 이 규칙은 문헌 계보를 이용한 누출 방지용 grouping이지 통계적 독립성 증명이 아니다.

## 5. 수작업 라벨과 IAA

자동화 가능한 것은 metadata 후보 수집, URL/버전/hash 기록, 허용된 원문 파싱, 표 위치 후보 탐색, near-duplicate 후보 탐색, 빈 양식 검증이다. 사람이 해야 하는 것은 결과 보고 단위의 경계, 원래 결과 재서술/새 보고/부분 재사용 여부, 조건·표·각주의 연결, 원문상 부족 정보, 대안 근거/답, 한국어 맥락과 KO/EN 의미 동일성이다. LLM은 후보를 제안할 수 있으나 최종 gold와 독립 human review를 대체하지 않는다.

**조정 전 IAA를 먼저 계산한다.** 두 reviewer가 합의한 뒤 같은 답을 다시 기입한 수치로 IAA를 만들지 않는다.

| 항목 | 조정 전 기록/통계 |
|---|---|
| lineage category | raw agreement, label별 confusion, Krippendorff α 등 불완전 reviewer 배치를 처리하는 nominal agreement, eligible pair 분모 |
| unit/mention 식별 | 정렬 규칙을 동결한 뒤 unit/edge set agreement 및 disagreement 수. 임의로 node ID만 달라진 경우와 의미 차이를 구분 |
| 조건 값/결과값 | exact normalized agreement와 불일치 원문 표기, 단위 변환 오류율 |
| 근거 locator | 동일 표/문단 및 허용 대안 evidence의 합의율. 완전히 같은 text offset만 유일 정답으로 강제하지 않음 |
| KO/EN 동등성 | 조건 누락, 부정/시점/지시 대상/유보 변경 각각의 reviewer 판정과 수정 전후 로그 |
| 원문 정보 부족 | `unresolved` 이유별 분포, reviewer 간 불일치, 확정 판정으로 바뀐 경우 추가 근거 |

`unresolved`는 명시적 라벨이고 미작성/null과 다르다. α만 높고 한 라벨로 쏠린 경우를 놓치지 않도록 class 분포와 raw agreement를 함께 보고한다. CI/모델 비교의 resampling 단위는 base/source family cluster로 하고 같은 문항의 언어 변형/반복을 표본 수에 더하지 않는다.

pilot 운영 gate 초안은 핵심 edge raw agreement 85% 이상, nominal agreement 약 0.8을 목표로 하되 숫자 하나로 gold의 진실성을 인증하지 않는다. 기준은 pilot 결과를 본 뒤 유리하게 바꾸지 않고 사전 protocol에 기록한다. 불일치가 많으면 codebook/원문 packet을 수정하고 새 blinded round를 진행한다. 특히 unresolved 비율이나 분야 간 disagreement가 높으면 더 많은 자동 생성으로 메우지 않고 범위를 좁히거나 연구 질문을 수정한다.

## 6. 5주 pilot의 주별 gate

| 주 | 공통 작업 | 사람별/팀 완료 산출물 | 다음 단계 조건 |
|---|---|---|---|
| 1주 | 160 candidate screening, 권리/언어/버전 확인, 2쌍 공동 calibration 후 codebook 초안 | 1인 후보 32행, 권리 통과 우선 packet 4개; 김수용 codebook, 정상헌 rights표, 남두현 조건표, 오창원 bilingual표, 이상민 split표 | 공동 calibration 자료는 IAA/test에서 제외. source/rights 필수 열이 채워지고 unverified 데이터가 gold에 없음 |
| 2주 | 1인 4개씩 20개 base case 초안, independent review 시작 | 잠정 gold는 출제자만 접근; R1/R2는 원문 packet으로 독립 주석 | alternate answer와 unknown을 기록. 원문 locator/hash 및 KO 원문 질문 존재 |
| 3주 | 1인 나머지 4개씩 총 40개 초안, KO/EN 의미 검토, 누출 family 연결 | 전 사례 source/unit/mention/edge/question 표, 최소 20개에 blinded double review | 자기 문항 self-review 없음. 해시/버전 일치와 연결 component 검사 통과 |
| 4주 | double review 완료, 조정 전 IAA, adjudication, codebook 변경 기록 | 40개 전부 2인 독립 review; 불일치 조정표·대안 근거·수작업 시간 보고 | unresolved를 임의 확정하지 않음. 권리/개인정보 및 gold 분리 gate 100% 확인 |
| 5주 | CPU 검증과 작은 agent preflight, protocol 동결, scale/no-go 결정 | completeness/누출 감사, pilot IAA와 비용/시간, baseline trace, 논문 주장–증거 목록 | 실제 반복 비용·최소효과·성능 분포로 확장 가능성을 판단. 허위 성능표/미실행 항목 없음 |

데이터가 없거나 이용 조건을 통과하지 못하면 주차를 넘겼다는 이유로 `frozen`으로 바꾸지 않는다. 종료일을 밀거나 범위를 줄이고 그 사실을 기록한다. pilot 40개는 개발·가설 수정용이다. 이 사례로 프롬프트·채점기·규칙을 조정한 뒤 같은 자료의 수치를 최종 held-out 성능이라고 보고하지 않는다.

## 7. 인력·예산 가정과 확장 중단 기준

각 사람의 공통 업무 가정은 다음과 같다. **실측이 아니며,** 문서 2~5개/mention 4~12개 정도의 text-first case와 분야 이해가 있는 검토자를 전제로 한다.

| 업무 | 1인 분량 | 단위 시간 가정 | 1인 시간 |
|---|---:|---:|---:|
| 후보 확인/권리·언어 screening | 32개 | 0.15~0.30h | 4.8~9.6h |
| source packet·질문·잠정 주석 | 8개 | 2~3h | 16~24h |
| 타인 blinded review | 16개 | 0.75~1.25h | 12~20h |
| 제3자 adjudication, 전 건 분쟁 가정 상한 | 최대 8개 | 0.5~0.75h | 4~6h |
| 역할 소유 양식/검증·회의 | 1세트 | 10~14h | 10~14h |
| 합계 |  |  | **46.8~73.6h/인** |

팀 공통 데이터 작업은 약 234~368h이고, 김수용의 통합 연구 설계/논문 초안 등은 별도 10~20h를 잡는다. 5주간 주당 약 10~15h/인 수준의 참여를 계획한다. 복잡한 표·부록·미확인 권리 때문에 시간이 늘면 실측 p50/p90을 대입해 일정을 다시 계산한다. 후보 탈락률·재작업 시간도 포함한다. 저자 순위를 작업 시간만으로 자동 결정하지 않는다.

실행 비용은 `base_groups × languages × repeats × models × configurations`로 episode 수를 계산한다. 예를 들어 pilot 전체 40×2언어×3반복×4모델×2설정이면 **1,920 episodes**다. 이것을 1,920개의 독립 문제라고 부르면 안 된다. 첫 API/모델 preflight는 8개 case×2언어×1회×2모델×2설정=64 episodes 같은 작은 범위로 시작하고, 실제 지연·token·비용을 기록한 뒤 확대한다. 이 문서는 해당 외부 API 실험을 실행했다는 뜻이 아니다.

현재 수집/형식 검사/단위 검증은 CPU 우선으로 한다. 저장소는 특정 GPU 번호를 고정하지 않고 [단일·다중 GPU 매뉴얼](GPU_EXECUTION_KO.md)에 따라 운영자가 할당한 장치의 UUID를 명시한다. 단일 worker의 logical cuda:0과 실제 물리 장치 번호를 구분하고, 여러 worker 또는 큰 모델의 tensor parallel 사용 시 총 자원·비용을 함께 기록한다. 이 세션에서 필요한 실제 모델 smoke에 한해 사용자가 물리 GPU3만 허용했으며 다른 GPU를 실행하지 않는다. 외부 API 비교는 실제 실행 여부·예산·endpoint를 기록한다. 실제 모델 smoke와 CPU 계약 검증을 연구 본 실험 결과로 포장하지 않는다.

### 7.1 조건부 확장

pilot 이후 다음 조건을 확인해야 확장한다: 원문/출판 이용 조건, 수작업 시간의 감당 가능성, 충분한 valid source family, double-review 안정성, agent 오류의 해석 가능성, 누출 차단, main 통계 분석의 최소효과/검정력. 원하는 점수 차이가 나올 때까지 test를 고르는 방식은 쓰지 않는다.

- 예시 A: 전체 240 base groups = 개발 pilot 40 + 공개 calibration 40 + 잠금 main test 160.
- 예시 B: 전체 300 base groups = 개발 pilot 40 + 공개 calibration 60 + 잠금 main test 200.
- 두 숫자는 선택지다. pilot과 source-family clustering으로 유효 표본 수를 계산하고, 비교할 모델 차이에 대한 paired 분석/검정력을 시뮬레이션해 하나를 정한다. 확보되지 않은 사례를 이미 확보했다고 적지 않는다.
- 각 그룹의 KO/EN 질문·반복 실행·버전·관련 unit을 모두 같은 split에 둔다. 240 base groups의 두 언어 질문 480행이 통계적 N=480이라는 뜻은 아니다.
- pilot에서 파생된 source/연구 family가 main test에 닿으면 그 connected component 전체를 dev로 이동하거나 test에서 제외한다. 제목/DOI exact 중복 제거만으로 누출 검증을 끝내지 않는다.
- 5개 분야에서 각각 충분한 원문/권리를 확보하지 못하면 domains를 줄이는 수정 protocol을 먼저 동결한다. 명목상 1인 48/60개 할당을 채우는 것보다 판단 가능한 실제 사례의 품질을 우선한다.

## 8. 공개/잠금 자료와 개인정보·권리 경계

| 자료 | 개발 중 위치/접근 | 공개 시 판단 |
|---|---|---|
| schema, 자체 codebook, 빈 양식, 검증 코드 | Git | 자체 작성분과 인용/라이선스 고지 확인 후 공개 |
| candidate URL/서지정보/수집 로그 | 내부 registry | 원문/개인정보 포함 여부와 이용 조건 확인 후 필요한 metadata만 |
| raw full text/PDF/표 이미지 | 접근 제한 source store | 각 문서·버전·제3자 요소의 실제 재배포 범위가 허용할 때만 frozen corpus에 포함 |
| 자체 질문·evidence locators·자체 주석 | 내부 annotation store | 자체 창작/기여 동의와 source 권리 검토 후 release 범위 확정 |
| held-out 질문/정답/연결 graph | evaluator 전용 | 평가 기간에는 agent process·retrieval index·로그 UI·공개 Git에 노출하지 않음 |
| 토큰/API key·개인 연락처 | 별도 secret 관리 | 공개하지 않음 |

무료로 열린 문서는 모두 원문 재배포가 가능한 문서라는 뜻이 아니다. 원문을 공개할 권리가 불명확하면 main frozen-corpus 공개 후보에서 보류하고, URL-only 연구용 기록과 재현성 한계를 별도로 남긴다. 라이선스를 임의로 CC-BY/MIT로 채우지 않는다. 개인정보가 보이면 gold에서 가릴 수 있다는 이유로 원문을 먼저 대량 공개하지 않는다. 임상/민감 사례는 이번 pilot의 포함 범위에서 제외한다.

공개 질문·gold를 낼 때는 작성자 기여 동의, 인용, 원문 범위, 스냅샷/파서 버전, source hash, 조정 전 불일치 통계와 누락 한계를 함께 기록한다. 불완전한 provenance를 확신하는 모델을 평가하기 위해 연구팀이 불완전한 provenance를 사실처럼 확정해서는 안 된다.

## 9. 빈 양식을 바로 만드는 CPU 명령

아래 명령은 모델 호출 없이 사용자 홈의 별도 private 작업 폴더에 **header만 있는 CSV**를 만든다. 실제 원문·질문·정답·허위 예시는 생성하지 않는다. 기존 CSV는 덮어쓰지 않는다. 팀 공유가 필요하면 접근 제어가 있는 내부 경로로 `root`만 바꾼다.

```bash
python3 - <<'PY'
from pathlib import Path
import csv
root = Path.home() / 'linkpaper-annotation-private' / 'pilot-20261102'
people = {'KSY':'김수용', 'JSH':'정상헌', 'NDH':'남두현', 'OCW':'오창원', 'LSM':'이상민'}
sheets = {
    'sources': ['candidate_id','source_id','collector','discovery_url','canonical_url','doi_or_report_id','title','publisher','publication_date','version_id','primary_language','language_evidence_locator','fetched_at_utc','raw_sha256','parser_name_version','rights_status','rights_evidence_url','rights_reviewer','redistribution_allowed','privacy_screen_status','exclusion_reason'],
    'units': ['reported_unit_id','source_id','study_family_id','result_family_id','original_unit_locator','dataset_or_sample','method_or_treatment','comparator','metric','unit','condition_values','reported_value_raw','statistical_independence_status','uncertainty_reason'],
    'edges': ['base_case_id','from_id','to_id','lineage_label','supporting_locators','alternative_explanations','annotator','codebook_version'],
    'questions': ['base_case_id','author','source_bundle_ids','task_family_id','question_ko','question_en','required_conditions','permitted_abstention','label_track','revision'],
    'reviews': ['base_case_id','reviewer_id','review_round','codebook_version','source_hashes','unit_ids','edge_labels','supporting_locators','accepted_alternative_evidence','possible_alternative_answer','uncertainty_reason','annotation_started_at','annotation_finished_at'],
    'adjudications': ['base_case_id','r1_original','r2_original','disagreement_type','extra_evidence','adjudicator','final_label','reason','resolved_at_utc'],
    'splits': ['base_case_id','source_version_family','study_family_id','result_family_id','task_family_id','connected_component_id','split','freeze_at_utc','gold_visibility'],
    'time_log': ['person','candidate_or_case_id','activity','started_at_utc','finished_at_utc','minutes','rework_reason'],
}
for person_id in people:
    person_dir = root / person_id
    person_dir.mkdir(parents=True, exist_ok=True)
    for sheet, columns in sheets.items():
        target = person_dir / (sheet + '.csv')
        if not target.exists():
            with target.open('w', encoding='utf-8-sig', newline='') as stream:
                csv.writer(stream).writerow(columns)
print(root)
PY
```

각자 source 후보 32행을 먼저 채우고, source별 권리/언어/버전 검토를 통과한 packet부터 자신의 8개 base case를 작성한다. R1/R2에게는 원문 packet과 빈 review표만 전달한다. 자동 hash 계산과 형식 검사는 case가 실제로 채워진 뒤 수행하며, schema 통과를 과학적 정답의 증거로 보고하지 않는다.

## 10. 비교 자료에 대한 출처 기록

로컬 감사의 전수 inventory와 세부 근거는 [로컬 감사](audits/local/LOCAL_BENCHMARK_AUDIT_KO.md) 및 그 연결 inventory를 함께 검토한다. KoTAU의 private 개발 환경과 아직 확정되지 않은 grader proposal을 완성된 한국어 benchmark 평가로 소개하지 않는다. K-BrowseComp는 이미 한국어 multi-hop/parallel 문제와 expected chain/checklist를 다루므로 한국어 질문·근거 경로·진단 항목만으로 새로운 기여라고 주장하지 않는다. [K-BrowseComp 공식 dataset card](https://huggingface.co/datasets/prometheus-eval/k-browsecomp), [공식 논문](https://arxiv.org/abs/2606.02404), [KoTAU 저장소](https://github.com/HAE-RAE/KoTAU).

문헌/자료의 개념을 비교·인용하는 것과 문제·답·구현을 새 창작물처럼 복제하는 것을 구분한다. 표절/오염을 완전히 자동 판정하는 단일 점수는 없으므로 source lineage, 자체 작성 기록, near-duplicate 감사, 독립 검토, 적절한 인용, 공개 범위 검토를 함께 남긴다. 이 문서의 pilot 설계와 역할 분담은 제안이며 실제 수집 완료·IAA 수치·모델 성능을 대신하지 않는다.


## 구현 granularity 보충 (2026-11-02)

코드의 public document_id는 원문 locator가 있는 **근거 record**다. 질문 관련 result unit 하나당 record를 두며, 한 논문의 여러 결과는 동일 paper_id 아래 다른 record로 나타낸다. 실제 논문 수와 record 수를 모두 수집·통제한다. standalone GLRS는 record 수를 검사하고 agent-lineage bridge는 source paper 수까지 비교한다. 본문·표의 위치/조건을 사람이 확인해야 하며 record schema가 과학적 unit 경계를 자동 판정하지 않는다.

5개 탐색 영역은 후보 발굴 업무의 초기 배분이며 각 이름의 분야 전문성을 인정한 것이 아니다. 파일럿 판정 역량과 외부 검토 확보를 확인한 뒤 본 gold는 신뢰할 수 있는 1–2개 영역으로 좁힐 수 있다. 그 경우 모집단·분야 범위와 제외율을 다시 기록하고 5분야 일반화 주장을 하지 않는다.
