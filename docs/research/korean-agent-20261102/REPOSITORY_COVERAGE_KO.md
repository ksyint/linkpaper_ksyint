# 저장소·파일·브랜치 조사 범위

기준일 2026-11-02. 권한으로 관측 가능한 현재 branch tip과 로컬 파일을 조사했다. 삭제된 과거 branch나 접근 불가능한 저장소 이력까지 복구했다는 뜻은 아니다.

| 대상 | 범위 | 전수 목록 |
|---|---|---|
| linkmind-ai/linkpaper | 원격 10개 branch, SHA·모든 tracked path·blob | [상세 감사](audits/upstream/UPSTREAM_AND_FORK_AUDIT_KO.md), [branches](audits/upstream/branches.json), [파일 CSV](audits/upstream/branch_files.csv) |
| ksyint/linkpaper_ksyint | 조사 시작 시 원격 main + research/neurips-2027-benchmark-proposal 2개 | 위 동일 inventory에 repository별 포함 |
| 로컬 KoTAU | local21 + origin21 refs, 21개 고유 head, 81,082 branch-file 항목 | [상세 감사](audits/local/LOCAL_BENCHMARK_AUDIT_KO.md), [refs](audits/local/kotau_branches.json), [파일 gzip JSONL](audits/local/kotau_branch_file_inventory.jsonl.gz) |
| KoTAU 현재 디렉터리 | .git 외673개와 git 메타데이터70개, 기존 변경1개 | [filesystem](audits/local/kotau_filesystem_inventory.json), [원래 상태](audits/local/kotau_worktree_status.txt) |
| K-BrowseComp-main.zip | 101개 엔트리(파일80/디렉터리21)와 archive hash | [전체 엔트리](audits/local/kbrowsecomp_zip_inventory.json), [summary](audits/local/inventory_summary.json) |

두 LinkPaper 저장소는 합계 12개의 repository×branch 항목, 2,362개의 branch×file 항목, 381개 고유 blob이다. 같은 commit이 양쪽 저장소에 있으므로 이를 서로 독립인 12개 코드베이스로 세지 않는다. KoTAU의 42refs도 42개 독립 버전이라는 뜻이 아니다.

텍스트 코드·설계 문서는 읽고 Python 구문·심볼·구조를 조사했다. KoTAU 과거 branch의 방대한 raw/압축/제3자 PDF·이미지는 종류·크기·hash와 프로그램 스캔으로 범위를 확인했다. 원문 페이지나 raw record 전부를 사람이 의미적으로 읽었다고 표현하지 않는다. ZIP에는 Git 이력이 없으므로 ZIP만으로 원격의 다른 branch를 조사했다고 하지 않는다. `.env`·key 값·개인 이메일 등 비밀 내용은 보고서로 옮기지 않았다.

## 확인한 구현 차이

- LinkPaper main의 주요 online route는 501 scaffold다. 실서비스가 완성된 agent라고 가정하지 않는다.
- indexing/evaluation 자산과 공통 문헌·chunk ID는 실제 재사용 지점이다.
- feat/pipline은 미병합된 단일 논문 RAG/SSE 작업으로 main과 구분한다. 모든 branch를 무조건 합치면 계약 불일치를 함께 가져온다.
- 기존 fork 연구 branch는 영어 evidence packet 연구다. 이번 도구 agent 환경은 별도 모듈로 추가한다.
- KoTAU main의 label/grader는 미합의다. proposal branch를 확정된 benchmark 결과로 인용하지 않는다. inspector reset/load_task 도구가 agent에게 노출되지 않도록 구분하는 설계만 비교했다.
- K-BrowseComp의 한국어·멀티홉·중간 근거 chain은 기존 기여다. 문항·prompt·데이터를 복제하지 않았다.

원본 KoTAU의 변경 `dataset/lodging/scripts/yanolja_followup.sh`는 보존했다. 새 결과는 별도 fork checkout/branch에만 작성한다. 상위 프로젝트와 AlphaXIV-Open 관련 출처·MIT 고지는 유지한다.

## 범위 재현

각 clone에서 `git fetch --all --prune`, `git for-each-ref refs/heads refs/remotes`, 각 ref의 `git ls-tree -r -l`, `git status --porcelain`을 기록하고, ZIP central directory와 파일 hash를 대조한다. 실제 branch SHA와 파일 크기는 위 machine-readable 목록을 기준으로 한다. 새 연구 branch의 변경 범위는 이 branch의 commit diff와 함께 검토한다.

감사 보고서 말미의 초기 역할 초안/인원 확인 문장은 조사 당시 기록이다. 현재 연구의 저자와 배분은 최신 [TEAM_AND_DATA_KO.md](TEAM_AND_DATA_KO.md)를 따른다.
