# 로컬 비교 자료 감사: KoTAU와 K-BrowseComp

조사일: 2026-11-02. 이 보고서는 LinkPaper 새 벤치마크를 위한 비교 조사이며, 두 프로젝트의 코드·문제·프롬프트·데이터를 새 저장소에 복사하지 않았다.

## 조사 범위와 재현성

- `/mnt/AI_NAS/AI_MODEL/cole0707/libre4/hwp2pdf/linkpaperedit/KoTAU`: 현재 체크아웃 및 모든 local/origin branch ref. `git fetch origin --prune` 뒤 local 21개와 origin 21개가 같은 21개 head를 가리킴을 확인했다. HEAD 심볼릭 ref는 중복 제외했다.
- `K-BrowseComp-main.zip`: Git 이력이 없는 main 스냅샷이다. ZIP 엔트리 101개(파일 80개, 디렉터리 21개)를 전부 목록화하고 텍스트 파일을 읽었다. 이것으로 원격 저장소의 모든 과거 브랜치를 조사했다고 주장하지 않는다.
- 새 `linkpaper_ksyint` 체크아웃은 상위 에이전트의 별도 감사 범위다.
- KoTAU branch×file 전수 목록은 81,082행이며, 13,130개 서로 다른 blob을 내용 유형별로 조사했다. UTF-8 텍스트 blob 1,388개(총 1,159,525줄)를 프로그램으로 읽어 제목·심볼·해시를 추출했고 주요 설계/서비스/task/수집/eval 문서는 직접 검토했다. 11,741개 binary/compressed blob은 파일 종류·크기·해시 메타데이터를 조사했다. 원문 페이지·제3자 논문·각 raw record 전부를 사람이 의미적으로 읽었다는 뜻은 아니다.
- 민감할 수 있는 `keys_seen.json`은 파일 메타데이터만 기록하고 내용을 보고서에 쓰지 않았다.
- 현재 filesystem에는 `.git` 외 파일 673개, `.git` 메타데이터 파일 70개가 있고 untracked/ignored 추가 파일은 없었다. 기존 변경 `dataset/lodging/scripts/yanolja_followup.sh` 한 건을 그대로 보존했다. 소스/DB/작업 트리는 수정하지 않았다.

전수 목록은 이 디렉터리의 `kotau_branch_file_inventory.jsonl.gz`, `kotau_branches.json`, `kotau_unique_blob_analysis.json.gz`, `kotau_filesystem_inventory.json`, `kbrowsecomp_zip_inventory.json`에 있다. 전체 SHA와 파일 단위 byte 수를 포함하므로 요약 표와 대조할 수 있다. ZIP SHA-256은 `inventory_summary.json`에 있다.

## KoTAU: 실제 구현 상태

기준은 main `f88a6a462cc2`이며, 문서가 말하는 offline 한국 여행 agent 환경이다. train/lodging 예약 상태를 바꾸는 SQLite 서비스, 지도 조회와 이동 모형, 별도로 관리되는 personal context가 있다. main README는 rail 11개, lodging 8개, map 4개, personal 13개 MCP 노출을 표기한다. 이 숫자에는 personal의 inspector용 harness 편의 함수가 포함되어 있으므로 모두 순수 agent 업무 tool이라고 읽으면 안 된다.

- `src/kotau/tasks/env.py`: 원본 rail/lodging DB를 임시 디렉터리에 복사하고 초기 예약·시계를 넣는다. agent 호출은 tool allowlist를 거치며 reset/set_clock/load_bookings는 노출하지 않는다. 지도 DB는 read-only다. shared account는 결제수단 소유 확인용으로 personal profile을 읽는다.
- `src/kotau/tasks/model.py`, `dataset/tasks/README.md`: 환경 task 입력 12개(rail 7, lodging 4, map+rail 1)가 있고 specified/clarify/authorization/env_context 행동을 나눈다. 질문에 빠진 정보는 별도 disclosure로 기록한다. 입력 JSON 자체는 Git이 아니라 pinned HF snapshot에 있다.
- main에는 합의된 정답 라벨·agent 채점기가 없다. validation은 task 입력 형식과 환경 초기화 검증이지 benchmark 성능 평가가 아니다. `AGENTS.md`도 grader/GT/scoring은 draft proposal에서만 다루며 main에 합치지 말라고 명시한다.
- `proposal/task-labels` (`66556653d706`)는 별도 proposal이다. reference calls와 기대 최종 예약 상태, SQL/규칙 derivation, 일부 잘못된 경로를 제안한다. 이 branch를 main의 확정된 scoring protocol로 소개하면 안 된다. proposal 자체도 wrong_calls·응답 기대·무호출 경로·부수 상태 변화 전부를 검증하지 않았다고 한계를 적는다.
- `tools/personal/personal_context.py`는 observable source 검색과 evaluator canonical facts/required facts를 분리한다. retrieval_report는 어떤 정보가 전달되었는지의 coverage로, 이해·최종 성공을 증명하지 않는다.
- `tools/personal/personal_mcp.py:98,104`: inspector 편의를 위해 load_task/reset을 실제 `@mcp.tool()`로 노출한다. benchmark 실행에는 별도 allowlist 또는 서버 분리가 필요하다. LinkPaper가 이를 따라 만들 때 harness control을 agent의 schema에 넣지 않아야 한다.
- 개인 검색은 keyword substring 기반이고 고정 기본 인자가 있는 inspector wrapper도 있다. 이런 환경 가정을 정교한 한국어 semantic retrieval 성능으로 오해하면 안 된다.

데이터는 `HAERAE-HUB/KoTau-dev-data`의 비공개 개발 snapshot에 의존한다. main `data.lock.json`은 revision `9622f70f4a28c7507d6b03429b735d0d7b5384eb`와 manifest SHA-256을 고정한다. 이 감사에서는 private raw/DB를 새로 다운로드하거나 agent 성능 실험을 실행하지 않았다.

### 브랜치 전체 목록

각 origin ref도 아래 같은 SHA와 파일 수를 가진다. MiB가 아니라 십진 MB다. 오래된 데이터 브랜치와 현재 src 패키지 구조는 크게 달라 diff 파일 수가 기능 추가량을 직접 뜻하지 않는다.

| local branch | SHA 앞 12자 | tracked 파일 | MB | 마지막 commit 요지 |
|---|---|---:|---:|---|
| `booking-engine-snapshots-oct` | `997d27e95a14` | 12,706 | 644.70 | data: 예약 엔진 10-01~04 스냅샷과 온다 PMS 캡처, 야놀자 places3 표본 추가 |
| `booking-screen-tools` | `440ca4e420a0` | 3,939 | 351.76 | chore(tools): 코레일, 야놀자, 네이버 예약 화면 탐색용 puppeteer 스크립트 |
| `chore/tasks-hide-labels` | `eb7ba45b5b75` | 222 | 3.65 | chore(tasks): 정답 label을 main과 HF main에서 빼고 task 입력만 남김 |
| `docs/new-domain-guide` | `1d8229cd2db1` | 670 | 4.23 | docs: 새 domain과 tool 추가 가이드 |
| `docs/readme-agents` | `ff03dea4d6fa` | 669 | 4.22 | refactor(schemas): OpenAPI 3.1 로 바꿔 변환기를 없애고 OpenAI strict 출력 삭제 |
| `feat/bus-attraction-data` | `338367a89f6c` | 135 | 2.65 | feat(data): 서울 버스와 관광지 데이터 등록과 HF 6735322 고정 |
| `feat/bus-observation-query-api` | `44230556e8d7` | 724 | 4.41 | feat(bus): add read-only express and intercity observation APIs |
| `feat/data-window-sept-dec` | `b85dcf781f2f` | 673 | 4.32 | feat(data): 기차와 숙소 DB 기간을 2026-09-01 ~ 12-26으로 늘리고 HF PR #9 고정 |
| `feat/graphhopper-route-draft` | `a8080d456631` | 682 | 4.28 | feat(map): add GraphHopper setup and pin OSM data on Hugging Face |
| `feat/lodging-nights-until` | `2e1b201a3722` | 670 | 4.23 | feat(lodging): 요금 조회 끝 날짜를 KOTAU_NIGHTS_UNTIL로 지정하고 HF 9622f70 고정 |
| `feat/pce-collect-form` | `ed78d3f61567` | 672 | 4.32 | feat(personal): 페르소나와 부탁 수집 HTML 폼과 JSON 형식 문서 |
| `feat/platform-redesign` | `57a9e3ae8623` | 220 | 3.63 | chore(data): map component 등록과 HF 470759a 고정 |
| `feat/public-business-data` | `4e8ff3d35fdb` | 677 | 4.26 | fix(data): verify published business snapshots without mutation |
| `feat/rail-lodging-booking-env` | `a3c697f907e8` | 135 | 2.65 | docs: 9월 기준 기간과 synthetic_ 열 규칙 반영 |
| `feat/subway-data` | `9c10003c89e1` | 695 | 4.40 | refactor(subway): 공용 구조에 맞추고 중복 수집 파일 정리 |
| `fix/seeds-to-hf` | `24a8a45b0e92` | 216 | 3.60 | chore(data): seed 데이터를 HF로 옮기고 768c400 고정 |
| `lodging-collector-consolidation` | `efe9b0c40e0a` | 11,688 | 610.41 | feat: 전국 홈페이지 발굴 통합, lodging.db 슬림화, 야놀자 평점 반영 (C3/C8) |
| `main` | `f88a6a462cc2` | 673 | 4.30 | docs: README에 저장소 구조 그림 추가 (#28) |
| `proposal/task-labels` | `66556653d706` | 228 | 3.68 | proposal(tasks): oracle_calls를 reference_calls로 바꾸고 HF PR fc8d459 고정 (merge 금지) |
| `refactor/tasks-validation-only` | `6264ae6a2576` | 223 | 3.67 | refactor(tasks): 채점 코드를 빼고 task 문서 검증 도구로 축소 |
| `travel-benchmark-research` | `a8202ce381a3` | 4,024 | 401.98 | docs(research): 여행 benchmark query 조사 자료와 요약 PDF |

### 브랜치별 해석

- `booking-engine-snapshots-oct`, `booking-screen-tools`, `lodging-collector-consolidation`: 3,939~12,706개 파일, 351.76~644.70MB를 추적하는 과거 수집/스냅샷 계열이다. raw 웹/DB/화면 자료를 새 저장소로 옮길 이유가 없다. main 673파일/4.30MB 구조와 혼동하지 않는다.
- `travel-benchmark-research`: 여행 benchmark 논문·웹·기존 데이터 조사 자료가 많다. 제3자 자료를 그대로 재배포하는 방식을 LinkPaper에서 따르지 않는다. 참고 URL과 자체 요약·수집 허용 기록으로 바꾼다.
- `feat/rail-lodging-booking-env`, `feat/platform-redesign`, `chore/tasks-hide-labels`, `fix/seeds-to-hf`, `refactor/tasks-validation-only`: 환경 구현, 데이터 HF 이관, 라벨 제거, task 입력 검증 중심으로 이동한 개발 계보를 보여 준다.
- `docs/readme-agents`, `docs/new-domain-guide`: 구조/도메인 추가 지침과 schema 생성 절차를 정리했다.
- `feat/bus-attraction-data`, `feat/bus-observation-query-api`: bus/attraction 데이터와 express/intercity read-only 관측 query API다. 새 bus API는 부분 coverage이며 완전한 예약 환경이 아니다.
- `feat/subway-data`: 지하철 데이터/코드를 공용 구조에 맞춘 branch다. 코드 유무와 전체 여행 agent task의 검증 여부는 별개다.
- `feat/lodging-nights-until`, `feat/data-window-sept-dec`: 기간 확장과 snapshot pin 변경이다. 9월 legacy task와 10~12월 관측의 시점을 구분해야 한다.
- `feat/graphhopper-route-draft`: 별도 Java/로컬 OSM 엔진과 Python 도보 경로를 추가한 draft다. main의 기존 이동 모형과 같지 않다.
- `feat/public-business-data`: 공공 사업체 스냅샷의 비변경 검증 및 dataset component를 추가한다.
- `feat/pce-collect-form`: 페르소나/요청 수집용 HTML 형식 제안이다. 자동 생성 profile과 실제 참여자 정보를 구분해야 한다.
- `proposal/task-labels`: 확정 benchmark가 아닌 정답/평가 설계 제안이다.

### 출처와 라이선스

조사한 KoTAU 모든 branch path에서 LICENSE/LICENCE/COPYING/NOTICE 파일을 찾지 못했다. 저장소를 볼 수 있다는 사실만으로 코드·데이터 재사용 허용을 확정하지 않는다. `docs/huggingface-card.md`는 private development repository이고 출판 데이터는 별도 frozen release를 쓴다고 한다. third-party 자료는 원래 제공자의 조건을 따른다는 문구가 있다. OSM 유래 값에는 ODbL 표기가 있고, 여러 예약 사이트의 수집 허용·약관 검토 상태는 미정 또는 보류다. 새 benchmark에 이 raw 자료를 복사하면 계보·이용 조건·평가 누출을 함께 물려받는다.

## K-BrowseComp: 이미 존재하는 기여와 구현

로컬 ZIP README와 소스, [공식 논문](https://arxiv.org/abs/2606.02404), [공식 dataset card](https://huggingface.co/datasets/prometheus-eval/k-browsecomp)를 대조했다. 한국 웹 탐색 자체, multi-hop/parallel 조건 추적, evidence chain/checklist, 합성 adversarial 생성은 이미 이 프로젝트의 범위다. 이것들을 새 기여라고 주장하지 않아야 한다.

- 로컬 fallback `ko_browsecomp.jsonl` 300행과 `ko_browsecomp_synthetic.jsonl` 100행을 전수 파싱했다. 각각 `problem`, `answer`, `type`, `category` 네 필드만 있다. 문제·정답은 보고서나 새 저장소로 복사하지 않았다.
- 공식 HF는 verified 300개와 같은 문항의 verified_with_metadata 300행, synthetic 100행을 별도 config로 제공한다. 따라서 화면의 총 700행을 서로 다른 700문제로 세면 틀린다. 유일 문항은 400개다.
- verified_with_metadata의 expected_chain과 checklist는 출제자가 기대한 근거 경로와 중간 값이다. checklist는 대체 가능한 해결 경로를 금지하는 hard requirement가 아니다.
- `search_evals/suites/ko_browsecomp.py`: 기본 verified/test를 HF에서 읽고 dry_run은 첫 10개 live API 실행이다. closed offline smoke test가 아니다.
- `search_evals/agents/deep_research.py`: 기본 최대 10번 검색과 최대 step을 사용하는 agent다. task마다 search tool, final answer/설명/신뢰도 형식을 쓴다.
- `search_evals/suites/graders.py`: gold short answer와 agent 최종 응답을 LLM judge로 비교한다. alias/한자/로마자 등 표기 변형을 허용하고 서로 다른 후보를 나열하면 오답으로 본다. 코드상 metadata chain이 default 최종 점수의 필수 gate는 아니다.
- `automated_data_gen/`: 원본 seed 계보 보존, 후보 확장, 문제 생성 뒤 sanity/oracle/adversarial gate, 복수 target model 실패를 요구하는 diagnostic 생성이 이미 있다. 따라서 단순 'LLM으로 문제 만들고 다른 LLM으로 풀어 본다' 역시 차별화 주장이 될 수 없다.
- contamination filter는 검색 결과 title/doc/url regex 차단이다. 새 작업에서는 이 정도만으로 train contamination이나 item overlap이 해결됐다고 말하지 않는다.
- 코드 LICENSE는 MIT이며 Perplexity/search_evals에서 유래한 파일의 provenance comment가 있다. 공식 dataset도 MIT를 표기한다. 이는 링크된 제3자 웹 원문에 대한 권리를 새로 주지는 않는다. 비교 목적으로 논문·repo·dataset을 인용하고 새 implementation/task는 독립 작성한다.

논문은 공개 텍스트 웹 근거만 허용하고 PDF·표계산·이미지 등 다운로드/비텍스트 해석을 제외한다. 이 차이는 LinkPaper가 독립적으로 만든 scholarly artifact 연구 task를 설계할 때 비교 축이 될 수 있다. 다만 mixed-artifact 또는 citation evaluation 자체가 최초라는 뜻은 아니며, 더 넓은 문헌 검토가 필요하다.

## 새 연구에 적용할 수 있는 구체적 교훈

1. 한국어로 바꾸거나 더 많은 사이트를 추가하는 것만으로는 충분하지 않다. LinkPaper의 학술문서/인용/증거 구조를 이용해 무엇을 새로 측정하는지 하나의 반증 가능한 연구 질문으로 좁힌다.
2. 다른 벤치마크의 문항·gold·template·failure taxonomy를 번역/부분 교체해 새 데이터라고 부르지 않는다. 질문 작성 전 자체 source pool과 수집 기준을 정하고 task family와 출처 계보를 기록한다.
3. agent가 볼 수 있는 문서/tool과 evaluator-only gold/주석/개입조건을 물리적으로 분리한다. schema에 load_task/reset/reference_calls 등을 노출하지 않는다.
4. 원본 source snapshot, parser 산출물, 사람이 확인한 evidence span, 가설/합성 artifact를 구분한다. 각각 URL·수집시각·source license·문서 hash·변환 버전을 남긴다.
5. 필요한 증거를 봤다는 사실과 그 증거를 올바르게 적용했다는 사실을 별도로 채점한다. 하나의 gold trajectory와 정확히 같은 tool 순서를 강제하지 않는다.
6. 모든 agent baseline은 같은 tool 권한, 시간·token·검색·fetch 예산과 frozen corpus를 사용한다. live web은 변동성 측정용 별도 track으로 보고한다. 선택된 실패 문제만 main 성능 추정에 섞지 않는다.
7. stateful task는 실행마다 독립 사본을 사용하고 원본 hash 불변을 확인한다. read-only evidence task도 cache와 episode 로그를 분리해 이전 정답이 다음 task로 새지 않게 한다.
8. pilot에서는 20~30개 task로 사람 작성·교차 검증·반론 확인·라벨 수정 시간을 재고, 그 실측치로 데이터 규모와 인력 계획을 정한다. 기존 논문의 작성 단가를 복잡도가 다른 새 task에 그대로 적용하지 않는다.

## 수작업과 분담에 대한 근거

K-BrowseComp는 사람이 문제·정답·source chain을 만들고 최종 review로 모호한 대체 답을 점검한다. 저자들이 아닌 참여자 보수는 10~15개 작성에 10만원, 약 4시간으로 보고된다. 이는 새 scholarly task의 보장된 작업량이 아니라 비교용 기존 사례다. [논문 Appendix A](https://arxiv.org/html/2606.02404v1#A1)

새 LinkPaper task에서는 source 수집·parser 실행·hash 기록은 자동화하되 다음 부분은 수작업이 필요하다: source 이용 조건 확인, 한국어 질문의 자연스러움/지역 맥락 판정, 주장과 근거 span의 entailment/contradiction 판정, 가능한 대안 답 탐색, 문항 family 간 누출·near duplicate 검토, 평가 실패의 adjudication. 문서/질문 작성자와 독립 reviewer를 분리하고 불일치율 및 수정 이력을 보존한다. 첫 저자는 김수용으로 고정하되, 다른 이름이나 저자 순서는 자료에 근거 없이 만들지 않는다.

KoTAU git history에는 Dasol Choi/최다솔, Lee Dong-geon, Sohyun Sim, Sungho Park/gigio1023, YONGSANG 등의 commit author 표기가 있었다. 이들은 해당 프로젝트의 기여자 표기일 뿐 요청한 새 논문의 공저자 명단이라는 근거가 없다. Git email은 보고서에 옮기지 않았다. 사용자 공저자 명단은 별도 확인이 필요하다.

역할 기반 분담 초안: ① 김수용: 연구 질문/프로토콜·평가 구현·최종 조정, ② 출처/라이선스 담당: source registry와 수집/권리 판정, ③ 문항/한국어 담당: 자체 task와 자연스러움, ④ 독립 근거 주석 담당: gold span·대안 답·라벨 교차 검토, ⑤ 실험 담당: baseline/ablation/예산 로그, ⑥ 통계/재현성 담당: split audit·CI·결과 재현. 실제 인원에 맞춰 역할을 겸임하더라도 자신의 문항을 유일한 reviewer로 확정하지 않게 한다.

## 수행하지 않은 것과 남은 검증

이 감사는 read-only repository/content 검토다. KoTAU의 private HF DB나 실험용 API key를 사용하지 않았고 live agent eval·대규모 crawling·성능 숫자 재생산을 실행하지 않았다. main에 공인 grader가 없는 상태에서 성공률을 꾸며 쓰지 않았다. 원문·기존 문제·제3자 논문/페이지 사본은 새 저장소에 복사하지 않았다. 1티어 main 채택이나 절대적인 선행연구 부재를 보증할 수 없으므로 새 설계의 novelty matrix·provenance audit·실제 실험 결과로 주장을 검증해야 한다.
