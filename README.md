# 🎮 LLM 기반 NPC 동적 기억 퀘스트 시스템

> **2025년 2학기 소프트웨어융합학과 게임 캡스톤 디자인**  
> NPC가 플레이어와의 상호작용을 기억하고, 연속성 있는 퀘스트를 동적으로 생성하는 AI 시스템

[![Unity](https://img.shields.io/badge/Unity-2022.3-black?logo=unity)](https://unity.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Google-Gemini_2.5-orange?logo=google)](https://ai.google.dev/)

---

## 📋 목차

- [프로젝트 개요](#-프로젝트-개요)
- [시스템 아키텍처](#-시스템-아키텍처)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [설치 및 실행](#-설치-및-실행)
- [프로젝트 구조](#-프로젝트-구조)
- [팀 구성](#-팀-구성)
- [라이선스](#-라이선스)

---

## 🎯 프로젝트 개요

기존 게임의 NPC는 정해진 스크립트에 의존하여 플레이어와의 이전 대화나 행동을 **기억하지 못합니다**. 이는 반복적이고 단조로운 게임 경험을 야기하는 주요 원인이었습니다.

본 프로젝트는 **LLM(Large Language Model)**과 **RAG(Retrieval-Augmented Generation)** 기술을 활용하여, NPC가 과거 상호작용을 기억하고 이를 기반으로 **연속성 있는 퀘스트를 자동 생성**하는 시스템을 제안합니다.

### ✨ 핵심 가치

- 🧠 **NPC 기억 시스템**: 인간의 기억 체계를 모방한 계층적 메모리 아키텍처
- ⚡ **동적 퀘스트 생성**: 게임 컨텍스트와 NPC 기억을 반영한 실시간 퀘스트 생성
- 🎭 **캐릭터 자동 생성**: 2줄의 Seed Description으로 완전한 NPC 캐릭터 시트 생성
- 🔍 **시맨틱 검색**: 과거 대화도 의미 기반으로 검색하여 서사적 연속성 확보

---

## 🏗 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Unity Client (C#)                           │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │
│  │   SQLite DB  │   │QuestRequester│   │    Quest Manager UI      │ │
│  │ (정적 게임     │   │  (HTTP 통신) │   │     (퀘스트 진행/완료)      │ │
│  │   데이터)     │   └──────┬───────┘   └──────────────────────────┘ │
│  └──────────────┘          │ REST API                               │
└────────────────────────────┼────────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│CharacterMemory  │ │    Backend2     │ │   Google AI     │
│    System       │ │ (캐릭터 시트 생성) │ │   Gemini API    │
│   :8123         │ │      :8001      │ │                 │
├─────────────────┤ └─────────────────┘ └─────────────────┘
│ Recent Memory   │          ▲                  ▲
│ (In-Memory FIFO)│          │                  │
├─────────────────┤          └──────────────────┘
│ Buffer (JSON)   │              LLM 호출
├─────────────────┤
│ Long-term Memory│
│ (ChromaDB Vector│
│      DB)        │
└─────────────────┘
```

---

## 🚀 주요 기능

### 1. 계층적 메모리 아키텍처

인간의 기억 체계(단기 → 장기)를 모방한 3단계 구조:

| 계층          | 저장소            | 용량        | 특징                        |
| ------------- | ----------------- | ----------- | --------------------------- |
| **단기 기억** | In-Memory (deque) | 5개/NPC     | O(1) 접근, FIFO             |
| **버퍼**      | JSON 파일         | 10개 임계치 | 자동 임베딩 트리거          |
| **장기 기억** | ChromaDB          | 무제한      | 시맨틱 검색 (코사인 유사도) |

### 2. 동적 퀘스트 생성

```
플레이어 입력 → 메모리 검색 → 게임 컨텍스트 수집 → LLM 프롬프트 조립 → 퀘스트 JSON 생성
```

- **환각(Hallucination) 방지**: 게임 DB에 존재하는 리소스만 AI에게 노출
- **Bridge Rule**: 모든 대화는 다음 목표와 인과관계 설명 필수
- **Structured Output**: JSON 스키마 강제로 파싱 오류 최소화

### 3. 캐릭터 자동 생성 (Seed-to-Sheet)

**입력**:

```
ID: npc_elda_mage
Description: 지식을 찾아 떠도는 신비로운 마법사
```

**출력**: 완전한 NPC 캐릭터 시트 (이름, 나이, 성격, 말투, 목표, 관계 등)

---

## 🛠 기술 스택

| 분류                  | 기술                                              |
| --------------------- | ------------------------------------------------- |
| **게임 클라이언트**   | Unity 2022, C#, SQLite                            |
| **백엔드 서버**       | Python 3.10, FastAPI, Uvicorn                     |
| **벡터 데이터베이스** | ChromaDB (HNSW 인덱스)                            |
| **텍스트 임베딩**     | sentence-transformers (all-MiniLM-L6-v2, 384차원) |
| **LLM API**           | Google Vertex AI (Gemini 2.5 Flash Lite)          |
| **통신**              | RESTful API, JSON                                 |

---

## 📦 설치 및 실행

### 사전 요구사항

- **Unity** 2022.3 LTS 이상
- **Python** 3.10 이상
- **Google Cloud** 계정 (Vertex AI API 활성화)

### 1. 저장소 클론

```bash
git clone https://github.com/your-repo/25_SWCON36701_GameCapstoneDesign.git
cd 25_SWCON36701_GameCapstoneDesign
```

### 2. CharacterMemorySystem 서버 실행

```bash
cd CharacterMemorySystem
pip install -r requirements.txt
python main.py
# 서버 실행: http://localhost:8123
```

### 3. Backend2 (캐릭터 시트 생성) 서버 실행

```bash
cd Backend
pip install -r requirements.txt
python main.py
# 서버 실행: http://localhost:8001
```

### 4. Unity 프로젝트 열기

1. Unity Hub에서 프로젝트 폴더 열기
2. `Assets/Scenes/MainScene.unity` 로드
3. Play 버튼 클릭

---

## 📁 프로젝트 구조

```
25_SWCON36701_GameCapstoneDesign/
├── Assets/                          # Unity 게임 에셋
│   ├── Scripts/
│   │   ├── Quest/                   # 퀘스트 시스템
│   │   │   ├── QuestRequester.cs    # 서버 통신
│   │   │   ├── QuestInputGenerator.cs # 컨텍스트 수집
│   │   │   └── QuestManager.cs      # 퀘스트 관리
│   │   └── Database/
│   │       └── DatabaseInitializer.cs # SQLite 자동 구축
│   └── StreamingAssets/
│       └── npcs/                    # NPC JSON 데이터
│
├── CharacterMemorySystem/           # NPC 메모리 백엔드
│   ├── main.py                      # FastAPI 진입점
│   ├── services/
│   │   ├── recent_memory.py         # 단기 기억 서비스
│   │   ├── longterm_memory.py       # 장기 기억 서비스
│   │   ├── memory_manager.py        # 메모리 통합 관리
│   │   └── quest_generator.py       # 퀘스트 생성 서비스
│   └── utils/
│       └── embeddings.py            # 임베딩 서비스 (싱글톤)
│
├── Backend/                         # 캐릭터 시트 생성 백엔드
│   ├── main.py
│   └── services/
│       └── prompt_builder.py        # 프롬프트 빌더
│
└── doscs/                           # 문서
    ├── 참고논문/                    # 참고 논문 PDF
    └── 서식 및 제출 내용/
        └── 게임콘텐츠 캡스톤디자인 최종보고서.md
```

---

## 👥 팀 구성

| 이름   | 역할 | 담당 업무                                                                         |
| ------ | ---- | --------------------------------------------------------------------------------- |
| 이재혁 | 팀장 | 캐릭터 시트 생성 백엔드, NPC 메모리 시스템 (단기/장기 기억), 시스템 아키텍처 설계 |
| 강채원 | 팀원 | Unity-서버 통신 구현, 시스템 프롬프트 설계, 퀘스트 반환 및 메모리 업데이트        |
| 김민   | 팀원 | SQLite 데이터베이스 구축, 퀘스트 요청 데이터 구조 설계, 정적 게임 데이터 관리     |

---

## 📄 라이선스

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📚 참고 문헌

- Lewis, P., et al. (2020). _Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks_. NeurIPS 2020.
- Park, J. S., et al. (2023). _Generative Agents: Interactive Simulacra of Human Behavior_. ACM UIST '23.
- Reimers, N., & Gurevych, I. (2019). _Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks_. EMNLP 2019.

---

<p align="center">
  <b>🎮 게임 콘텐츠 캡스톤 디자인 2025</b><br>
  <i>경희대학교 소프트웨어융합학과</i>
</p>
