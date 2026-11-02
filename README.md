<div align="center">
<img src="https://capsule-render.vercel.app/api?type=transparent&color=auto&height=300&section=header&text=🔗%20LinkPaper&fontSize=90&fontColor=8b5cf6&animation=fadeIn" />

**지식그래프가 제공하는 풍부한 컨텍스트를 통해 논문을 더 깊이 이해하도록 돕는 AI 논문 분석 서비스**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.139-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-1.3-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://github.com/langchain-ai/langchain)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-8.1-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vite.dev)
[![Qdrant](https://img.shields.io/badge/Qdrant-1.18-DC244C?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.26-4581C3?style=flat-square&logo=neo4j&logoColor=white)](https://neo4j.com)
[![Docker](https://img.shields.io/badge/Docker-29.6-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

🔬[LinkMind LAB research blog](https://linkmind.tistory.com/)


</div>

> **2026-11-02 연구 확장 v2:** [한국어 학술 에이전트 벤치마크](docs/research/korean-agent-20261102/README.md)는 **필요한 논문 수를 알려주지 않은 상태에서 하나 또는 여러 논문의 근거를 찾아 연결하는 QA**다. **영어가 다수인 영어·한국어 다분야 논문**을 사용한다. [여섯 과제 유형](docs/research/korean-agent-20261102/TASK_SUITE_KO.md)에 단일/다중 문헌 연결·비교·수치·상충/충분성·결과 원천을 포함하며, GLRS는 결과 원천 하위 track 전용이다. 저장된 archive와 benchmark 도중 외부 논문 검색·수집·열람을 비교하고, 수집 snapshot·replay·실패·비용을 남긴다. [실제 CSV 작성 예시](collection_examples/20261102/csv_labeling/README_KO.md), 5인 검수·실험 계획과 [GPU 매뉴얼](docs/research/korean-agent-20261102/GPU_EXECUTION_KO.md)을 제공한다. 현재는 프로토타입이며 실제 gold·본 성능·메인 학회 채택은 검증 전이다.

### 📖 Introduction

논문을 이해하는 것은 하나의 문서를 읽는 것으로 끝나지 않습니다. 연구자는 선행 연구를 확인하고, 관련 연구를 비교하며, 후속 연구를 탐색하는 과정을 통해 비로소 연구의 전체 맥락을 이해합니다.

기존 AI 논문 리딩 서비스인 **Moonlight**는 논문의 내용을 쉽게 이해하도록 돕지만, 개별 논문에 초점을 맞추고 있어 해당 논문을 깊이 이해하는 데 필요한 관련 연구의 배경지식과 연구 맥락을 함께 제공하기에는 한계가 있습니다.

특히 연구자가 궁금해하는 질문은 의미적으로 유사한 논문을 검색하는 것만으로 해결되지 않는 경우가 많습니다. *"이 논문은 기존 연구와 무엇이 다른가?"*, *"이 논문의 한계를 해결한 후속 연구는 무엇인가?"*, *"이 연구는 어떤 연구 흐름 속에서 등장했는가?"*와 같은 질문에 답하려면 개별 논문의 내용뿐 아니라 **논문 간의 인용 관계와 연구 흐름을 함께 이해**해야 합니다. 즉, **논문 간 관계를 연결하여 하나의 문맥으로 탐색할 수 있는 구조**가 필요합니다.

**LinkPaper**는 이러한 문제를 해결하기 위해 논문을 깊이 이해하는 데 필요한 관련 연구의 배경지식까지 함께 탐색할 수 있는 환경을 제공합니다. 이를 위해 논문, 저자, 키워드, 인용 관계를 **지식그래프**로 구축하고, **GraphRAG**를 활용하여 그래프 탐색과 의미 기반 검색을 통해 논문에 대한 입체적인 이해를 제공합니다.

궁극적으로 LinkPaper는 단순한 논문 챗봇을 넘어, 논문 간의 연결 관계를 바탕으로 연구의 맥락 속에서 논문을 이해하도록 돕는 서비스를 지향합니다.

---

### ✨ Key Features

#### 💬 Paper Q&A
선택한 논문의 내용을 기반으로 질의응답을 제공하여 논문의 복잡한 개념과 세부 내용을 이해할 수 있습니다.

#### 🌐 GraphRAG-based Research Q&A
관련 논문과 인용 관계가 저장된 지식그래프 기반 GraphRAG를 활용하여, 현재 논문을 더 깊이 이해할 수 있는 심층 질의응답을 제공합니다.

#### 🧭 Research Flow Exploration
선행 연구, 후속 연구, 관련 논문의 연결 관계를 탐색하며 하나의 논문이 연구 분야에서 어떤 위치와 의미를 가지는지 이해할 수 있습니다.
> 💡 **예시 질문**
> - 이 논문에 소개된 ~라는 개념을 다른 논문에선 어떻게 설명하고 있지?
> - 이 논문의 한계를 해결한 후속 연구는 무엇인가?
> - 이 연구는 어떤 연구 흐름 속에서 등장했는가?

---

### 🎬 Demo

> 🚧 Coming Soon

#### Demo Contents

- 🔍 Hugging Face Papers에 등록된 논문 검색
- 📄 논문 기반 AI 챗봇
- 🌐 GraphRAG가 제공하는 컨텍스트 기반 심층 질의응답

---

### 🏗️ Architecture

#### Component Diagram

<div align="center">
  <img src="docs/component_diagram.svg" alt="LinkPaper Component Diagram" width="800" />
</div>

실행 계층은 두 개로 분리한다. `indexing/`은 스케줄에 따라 데이터를
전처리하고 Neo4j·Qdrant에 적재하는 오프라인 엔진이며, `backend/`는 완성된
인덱스를 읽어 사용자 검색과 GraphRAG 요청을 처리하는 온라인 API다.

---

### 📂 Project Structure

```text
linkpaper/

├── backend/
│   ├── api/
│   ├── graph/
│   ├── retrieval/
│   ├── llm/
│   └── app/
│
├── frontend/
│   ├── src/
│   └── public/
│
├── docs/
│   ├── images/
│   ├── architecture.md
│   ├── graph-schema.md
│   ├── evaluation.md
│   ├── benchmark.md
│   └── api.md
│
├── docker/
│
├── scripts/
│
├── backend/          # 사용자 요청을 처리하는 온라인 FastAPI 서버
├── indexing/         # 주기 실행 전처리·Neo4j/Qdrant 적재 엔진
├── evaluation/       # 검색·추출·생성 평가 하네스
├── frontend/         # 사용자 웹 애플리케이션
├── docs/             # 요구사항, 데이터·검색 아키텍처와 스키마
├── scripts/          # 개발·운영 보조 스크립트
├── docker-compose.yml
└── README.md
```

---

### 🚀 Usage

> **Requirements**: Docker Engine 20.10+ / Docker Compose V2 · 메모리 8GB 이상

```bash
git clone https://github.com/linkmind-ai/linkpaper.git

cd linkpaper

cp .env.example .env
# .env에 OPENAI_API_KEY 등 필요한 키를 채워주세요

docker compose up -d
```

실행 후 http://localhost:5173 에서 확인할 수 있습니다.

---

### 👥 Team (원프로젝트 기여자 기록)

이번 벤치마크·논문의 저자 계획은 **김수용(1저자), 정상헌·남두현·오창원·이상민(순위 미정)**이다. 기존 서비스의 아래 직무표와 구분하며 새 분담은 [연구 작업표](docs/research/korean-agent-20261102/TEAM_AND_DATA_KO.md)를 따른다.

| 이름 | 역할 | 담당 업무 |
|------|------|-----------|
| 정상헌 | PM / Data | 프로젝트 관리, 요구사항 정의, 데이터 수집 및 전처리 |
| 김대건 | Backend / GraphRAG | GraphRAG 파이프라인 및 FastAPI 개발 |
| 김수용 | Evaluation | GraphRAG 평가 및 벤치마크 구축 |
| 남두현 | Graph DB | 지식 그래프 구축 및 벡터 인덱싱 |
| 오창원 | Frontend | 프론트엔드 개발 및 백엔드 연동 |
| 홍예린 | Infrastructure | Docker, 모델 서빙 및 인프라 운영 |

---

### 🧪 Research Direction

현재 방향은 **주요 학회 main track 수준의 검증을 목표로 하는 학술 근거 연결 agent benchmark**이며 [최신 연구 설계](docs/research/korean-agent-20261102/README.md)를 따릅니다. 필요한 문헌 수를 알려주지 않고, 하나 또는 여러 논문의 근거를 찾아 연결해 답하는 능력을 평가합니다. 저장된 논문과 외부 발견·수집이 필요한 환경을 구분하며, 결과 계보는 여러 하위 과제 중 하나입니다. 신규성·사람 gold·본 실험은 검증할 과제이며 학회 채택을 보장하지 않습니다.

이전 NeurIPS 2027 벤치마크·평가 트랙 제안과 전체 근거를 미리 주는 packet 실험은 [과거 연구 문서](docs/research/neurips-2027/README.md)와 [packet 실행 안내](evaluation/RESEARCH.md)에 보존했습니다. 현재 도구 agent 설정과 구분합니다. 로컬 로더의 단일 GPU 선택, 여러 worker 및 외부 tensor-parallel 서버 실행은 [최신 GPU 매뉴얼](docs/research/korean-agent-20261102/GPU_EXECUTION_KO.md)을 따릅니다. 가상 fixture는 실행 검증용입니다.

### 📚 References

#### Papers

- Lewis et al., *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks* (2020)
- Microsoft Research, *From Local to Global: A GraphRAG Approach to Query-Focused Summarization* (2024)

#### Related Services

- [Moonlight](https://www.themoonlight.io/ko) — AI 기반 논문 요약 및 리딩 서비스
- [AlphaXIV-Open](https://github.com/AsyncFuncAI/alphaxiv-open) — arXiv 논문에 대한 AI 질의응답을 GraphRAG 기반으로 제공하는 오픈소스

---

### 🤝 Contributing

Issue와 Pull Request는 언제든지 환영합니다.

기능 추가나 큰 변경 사항은 먼저 Issue를 통해 논의한 후 진행해 주세요.
