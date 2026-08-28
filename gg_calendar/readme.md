# 📅 Google Calendar REST API v3 실전 개발 및 테스트 가이드

> **문서 버전**: v1.0  
> **대상 서비스**: Google Calendar API v3 (`calendarList`, `events`)  
> **연계 파이프라인**: Google Meet API v2, Vertex AI Gemini 3.7 Flash 회의록 자동화  
> **공식 레퍼런스**: [Google Workspace Calendar Python Quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python)

---

## 💡 1. 핵심 아키텍처 & 인증 원리 (GCP 계정과 캘린더 계정의 관계)

### ❓ "GCP 콘솔 계정과 캘린더를 소유한 구글 계정이 다른 경우 어떻게 인증하나요?"

```
┌──────────────────────────────────────────────┐
│ ☁️ Google Cloud Project (your-gcp-project-id) │
│   • GCP 콘솔 관리자 (admin@company.com)       │
│   • 역할: Calendar API 활성화 및             │
│          OAuth 2.0 클라이언트 앱(credentials.json) 발급 │
└──────────────────────────────────────────────┘
                       │ (OAuth 2.0 Client ID / Secret 발급)
                       ▼
┌──────────────────────────────────────────────┐
│ 🖥️ 협업포털 애플리케이션 (Local / Cloud Run)     │
│   • credentials.json 보유                     │
└──────────────────────────────────────────────┘
                       │ (브라우저 사용자 동의 창 호출: InstalledAppFlow)
                       ▼
┌──────────────────────────────────────────────┐
│ 👤 실제 캘린더 소유자 계정 (예: user@example.com) │
│   • 캘린더 접근 권한 승인 (OAuth Consent)      │
│   • ➔ token.json 발급 (Refresh & Access Token)│
└──────────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ 📅 Google Calendar API v3                    │
│   • token.json의 토큰으로 대상 사용자의       │
│     회의 일정, 참석자 명단, Meet 링크 조회    │
└──────────────────────────────────────────────┘
```

* **GCP 콘솔 로그인 계정(Project Owner)**:
  - 오직 **API 활성화** 및 OAuth 클라이언트(`credentials.json`)를 생성하는 **"인프라 관리자"** 역할입니다.
* **캘린더 데이터를 조회할 대상 계정(End-User)**:
  - 브라우저 로그인 팝업이 뜰 때 **실제 캘린더를 가진 계정(Gmail, 리테일 회사 Workspace 등)**으로 로그인하여 권한을 승인합니다.
  - 승인 즉시 해당 계정의 **`token.json`**이 생성되어 안전하게 저장됩니다.
* **결론**: **GCP 프로젝트 소유자 계정과 캘린더 사용자 계정은 완전히 달라도 되며, `token.json`에 저장된 사용자 권한으로 캘린더 데이터를 조회**합니다.

---

## 🔑 2. 필수 OAuth 2.0 권한 범위 (Scopes)

| Scope URI | 권한 수준 | 설명 |
| :--- | :---: | :--- |
| `https://www.googleapis.com/auth/calendar.readonly` | Read-Only | 사용자의 모든 캘린더 및 일정 목록 조회 |
| `https://www.googleapis.com/auth/calendar.events.readonly` | Read-Only | 사용자의 일정(이벤트) 상세, 참석자, Meet 링크 조회 |
| `https://www.googleapis.com/auth/calendar.events` | Read/Write | (선택) AI 회의록 요약본을 캘린더 일정 설명에 자동 첨부 |

---

## 🛠️ 3. 디렉토리 구성 및 스크립트 안내

```text
gg_calendar/
├── CALENDAR_API_USER_GUIDE.md# 📘 캘린더 API 리스트별 Input/Output 상세 가이드
├── readme.md                 # 📖 본 개발 및 테스트 가이드 문서
├── STEP_BY_STEP_TEST_GUIDE.md# 🧪 단계별 테스트 절차서
├── quickstart.py             # 🚀 구글 공식 표준 Calendar API 퀵스타트
├── test_calendar_api.py      # 🧪 Mock & Live 종합 테스트 스위트
└── calendar_service.py       # ⚙️ 협업포털 연동용 재사용 캘린더 서비스 모듈
```

---

## 🚀 4. 단계별 테스트 실행 방법

### 1단계: 로컬 Mock 모의 테스트 (인증 없이 즉시 실행)
Google 인증 토큰이 없는 환경에서도 캘린더 데이터 모델 파싱 및 Meet 회의 연동 로직을 100% 검증합니다:
```bash
.venv/bin/python gg_calendar/test_calendar_api.py --mode mock
```

### 2단계: 실제 구글 계정 Live 연동 테스트
`credentials.json`이 프로젝트 루트에 위치한 상태에서 브라우저 인증을 거쳐 실제 캘린더 일정을 조회합니다:
```bash
.venv/bin/python gg_calendar/test_calendar_api.py --mode live
```

---

## 📊 5. 협업포털 AI 회의록 파이프라인과의 연계 데이터

Google Calendar API를 통해 회의록 생성 시 필요한 핵심 메타데이터를 자동 주입합니다:

1. **회의 제목 (`event.summary`)**: AI 회의록 메인 타이틀 자동 설정
2. **회의 일시 (`event.start`, `event.end`)**: 회의 진행 시간 계산 및 메타 배너 표시
3. **참석자 명단 (`event.attendees`)**: 화자 분리(Diarization) 모델에 제공할 **참석자 후보군 명단** 자동 생성
4. **Google Meet 링크 (`event.conferenceData` / `event.hangoutLink`)**: Meet API v2와 결합하여 회의 녹화본 및 전사본 자동 추적
