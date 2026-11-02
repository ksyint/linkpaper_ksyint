# 원천별 권리 증거와 배포 범위

이 폴더의 원문 PDF·전체 추출문·페이지 렌더링은 로컬에만 보관한다. 레포에는 메타데이터, 짧은 위치 설명, 여기서 작성한 질문·관계 후보와 수집 스크립트만 배포한다. “공개 다운로드 가능”과 “무제한 재배포·학습 가능”을 같은 뜻으로 쓰지 않는다. 개별 그림·사진·인용 자료에는 다른 권리가 적용될 수 있다.

| 원천 | 확인한 1차 증거 | 현재 기록과 남은 확인 |
|---|---|---|
| `ioffe15`, `finn17a`, `chen20j`, `wang20k` | 각 공식 논문 페이지와 PDF 첫 페이지의 저자 copyright. [PMLR의 현행 출판 동의서](https://proceedings.mlr.press/pmlr-license-agreement.pdf) p.1 §2–3은 CC BY 4.0 및 원 출판·논문 링크 표기를 규정한다. | **현행 출판사 정책이라는 증거**다. 2015/2017/2020 각 역사적 파일의 개별 동의서나 명시적 라이선스 버전까지 확보한 것은 아니다. `license_spdx=null`, 정책 증거만 확인한 pending 상태로 기록했다. 현재 정책을 근거로 과거 논문마다 4.0임을 확정하지 않는다. 정식 재배포 전에 해당 버전의 권리 근거를 보완한다. |
| `min2024` | [공식 PDF](https://tkips.kips.or.kr/digital-library/manuscript/file/101425/11-SDE-24M-05-043E-%EB%AF%BC%EC%88%98%EC%98%81_553-558.pdf) p.1 하단, [CC BY-NC 3.0](https://creativecommons.org/licenses/by-nc/3.0/) 표시 | 비영리 제한을 명시한다. 아무 이용에도 적합한 permissive corpus라고 묶지 않는다. 상업 이용을 포함한 벤치마크 배포·서비스 범위와 별도 허락 필요 여부를 검토하기 전에는 정식 corpus 편입하지 않는다. 메타데이터만 공개한다. |
| `eriksen2014` | [공식 article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0111913) front matter와 PDF p.1은 CC0 public domain dedication을 명시한다. | 개별 article의 CC0 증거를 확인했다. PLOS라는 사이트 이름만 보고 CC BY로 기입하지 않았다. 출처는 학술 재현성을 위해 계속 표기하고 제3자 자산은 따로 확인한다. |
| `mora2011` | [공식 article](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.1001127)의 Copyright 문단과 PDF p.1은 Creative Commons Attribution License를 명시한다. | 해당 문단에는 버전 번호가 없다. `license_spdx=null`, `license_assertion`에 Attribution과 버전 미표시 사실을 기록했다. 현행 PLOS 정책을 소급하여 4.0으로 단정하지 않는다. |

메타데이터의 `rights_status`는 수집 담당자의 증거 정리다. 권리자에게 받은 개별 허락이나 법적 판단을 대신하지 않는다. 모든 레코드의 `benchmark_eligible=false`는 라벨·출처 계보·권리·문항 검수가 아직 끝나지 않았음을 함께 나타낸다. 검수되지 않은 자료를 평가 gold라고 표시하지 않는다.
