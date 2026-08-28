# 📅 Google Calendar API v3 고객 맞춤형 실전 가이드
> **Google Workspace 캘린더 연동, 회의 일정 조회 및 AI 회의록 메타데이터 매핑 가이드**

---

## 📌 1. 개요 및 비즈니스 가치 (Why Google Calendar API?)

리테일 회사 AI 협업포털은 **Google Calendar API v3**를 통해 사용자가 매번 번거롭게 회의명, 일시, 참석자 명단을 수동으로 입력할 필요 없이, **캘린더에 등록된 회의 일정을 1초 만에 불러와 AI 회의록에 자동 매핑**합니다.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 📅 Google Calendar API 연동 흐름                                       │
├─────────────────────────┬─────────────────────────┬─────────────────────────┬──────────────────────────┤
│ 1. 캘린더 일정 자동 수집 │ 2. 참석자 & Meet 링크 추출│ 3. Vertex AI 회의록 생성│ 4. 캘린더에 회의록 자동 첨부│
│ "오늘 진행된 회의 선택"  │ "참석자 명단 자동 세팅"  │ "화자 분리 및 안건 요약"│ "일정 설명란에 요약본 업데이트"│
└─────────────────────────┴─────────────────────────┴─────────────────────────┴──────────────────────────┘
```

### 🔑 핵심 연계 데이터 매핑
1. **회의 제목 (`summary`)** ➔ 생성될 AI 회의록의 공식 타이틀로 자동 반영
2. **회의 일시 (`start`, `end`)** ➔ 회의 진행 시간(예: 총 30분) 및 메타 정보 자동 계산
3. **참석자 명단 (`attendees`)** ➔ 다중 화자 분리(Diarization) 모델에 **참석자 이름 매핑 후보군**으로 자동 제공
4. **Google Meet 링크 (`conferenceData`)** ➔ Google Meet API v2와 결합하여 **녹화본 영상/음성 자동 추적**

---

## 📚 2. 주요 Calendar API 리스트별 Input & Output 상세 가이드

---

### 1️⃣ `calendarList.list` — 사용자의 캘린더 목록 조회
> 사용자가 접근 가능한 캘린더(기본 캘린더, 팀 공유 캘린더, 프로젝트 캘린더 등) 목록을 가져옵니다.

* **HTTP Method & Endpoint**: `GET https://www.googleapis.com/calendar/v3/users/me/calendarList`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/calendar.readonly`

#### 📥 Input (요청 파라미터)
| 파라미터명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `minAccessRole` | String | 선택 | `reader` | 최소 접근 권한 (`freeBusyReader`, `reader`, `writer`, `owner`) |
| `showHidden` | Boolean | 선택 | `false` | 숨겨진 캘린더 포함 여부 |
| `maxResults` | Integer | 선택 | `100` | 한 번에 가져올 최대 캘린더 개수 |

#### 📤 Output (응답 데이터 구조 및 예시)
```json
{
  "kind": "calendar#calendarList",
  "items": [
    {
      "id": "user@example.com",
      "summary": "홍길동 팀장 (기본 캘린더)",
      "primary": true,
      "timeZone": "Asia/Seoul",
      "accessRole": "owner"
    },
    {
      "id": "c_188abc..._enterprise.com@group.calendar.google.com",
      "summary": "리테일 회사 AI TFT 공유 캘린더",
      "primary": false,
      "timeZone": "Asia/Seoul",
      "accessRole": "writer"
    }
  ]
}
```

---

### 2️⃣ `events.list` — 회의 일정 목록 조회 (핵심 API ⭐)
> 특정 기간(예: 오늘, 이번 주) 동안 진행된 회의 목록을 조회하여 회의록 생성 대상 이벤트를 선택합니다.

* **HTTP Method & Endpoint**: `GET https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/calendar.events.readonly`

#### 📥 Input (요청 파라미터)
| 파라미터명 | 타입 | 필수 여부 | 예시 값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `calendarId` | String | **필수** | `primary` | 대상 캘린더 ID (`primary`는 내 기본 캘린더) |
| `timeMin` | String (ISO 8601) | 선택 | `2026-08-20T00:00:00Z` | 조회 시작 일시 (이 시간 이후 일정) |
| `timeMax` | String (ISO 8601) | 선택 | `2026-08-20T23:59:59Z` | 조회 종료 일시 (이 시간 이전 일정) |
| `singleEvents` | Boolean | 권장 | `true` | 반복 일정을 개별 인스턴스로 분리하여 반환 |
| `orderBy` | String | 선택 | `startTime` | 정렬 기준 (`startTime`은 `singleEvents=true` 필수) |
| `q` | String | 선택 | `"CFT"` | 검색 키워드 필터링 |

#### 📤 Output (응답 데이터 구조 및 예시)
```json
{
  "kind": "calendar#events",
  "summary": "홍길동 팀장 캘린더",
  "items": [
    {
      "id": "evt_meet_20260820_01",
      "summary": "리테일 회사 AI 협업포털 주간 정기 미팅",
      "description": "Google Meet 기반 회의록 자동화 및 화자 분리 아키텍처 점검",
      "start": {
        "dateTime": "2026-08-20T14:00:00+09:00",
        "timeZone": "Asia/Seoul"
      },
      "end": {
        "dateTime": "2026-08-20T15:00:00+09:00",
        "timeZone": "Asia/Seoul"
      },
      "hangoutLink": "https://meet.google.com/abc-defg-hij",
      "conferenceData": {
        "entryPoints": [
          {
            "entryPointType": "video",
            "uri": "https://meet.google.com/abc-defg-hij",
            "label": "meet.google.com/abc-defg-hij"
          }
        ],
        "conferenceSolution": {
          "name": "Google Meet"
        }
      },
      "attendees": [
        {
          "displayName": "홍길동 팀장",
          "email": "hong@example.com",
          "responseStatus": "accepted"
        },
        {
          "displayName": "성춘향 님",
          "email": "sung@example.com",
          "responseStatus": "accepted"
        },
        {
          "displayName": "담당 CE",
          "email": "ce@google.com",
          "responseStatus": "accepted"
        }
      ]
    }
  ]
}
```

---

### 3️⃣ `events.get` — 특정 회의 단건 상세 조회
> 선택된 특정 회의의 전체 메타데이터(전체 참석자, 상세 설명, 첨부 문서 등)를 단건으로 정밀 조회합니다.

* **HTTP Method & Endpoint**: `GET https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events/{eventId}`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/calendar.events.readonly`

#### 📥 Input (요청 파라미터)
| 파라미터명 | 타입 | 필수 여부 | 예시 값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `calendarId` | String | **필수** | `primary` | 대상 캘린더 ID |
| `eventId` | String | **필수** | `evt_meet_20260820_01` | 조회할 이벤트 고유 ID |

#### 📤 Output (응답 데이터 구조 및 예시)
* 단일 `Event` 리소스의 완전한 JSON 객체를 반환합니다. (제목, 시작/종료 일시, 회의 주최자 `organizer`, 참석자 목록 `attendees`, 화상회의 코드 `conferenceData`)

---

### 4️⃣ `events.patch` — 생성된 회의록 요약본 캘린더 일정에 자동 첨부
> AI가 생성한 **1페이지 핵심 요약**과 **Action Items**를 해당 캘린더 일정 설명란(`description`)에 자동으로 추가합니다.

* **HTTP Method & Endpoint**: `PATCH https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events/{eventId}`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/calendar.events`

#### 📥 Input (요청 본문 Body)
```json
{
  "description": "📌 [AI 협업포털 회의록 자동 요약]

🎯 핵심 결정사항:
1. Vertex AI Gemini 3.7 Flash 글로벌 화자 분리 엔진 도입 확정
2. GCS Direct Resumable Upload 방식으로 대용량 미디어 전송 최적화

📋 Action Items:
- [성춘향 님] DWD 서비스 계정 권한 연동 (~08/25)
- [담당 CE] GCS 버킷 생성 및 라이프사이클 정책 배포 (~08/22)

👉 전체 회의록 보기: https://enterprise-agent-gateway.uc.gateway.dev"
}
```

#### 📤 Output (응답 데이터)
* 수정된 `description`이 반영된 `Event` 리소스 객체 반환 (`HTTP 200 OK`)

---

### 5️⃣ `events.insert` — 후속 회의(Follow-up Meeting) 자동 등록 & Google Meet 링크 발급
> 회의록에서 도출된 차기 회의 일정을 Google 캘린더에 원클릭으로 등록하고, **Google Meet 화상회의 링크를 즉시 자동 발급**합니다.

* **HTTP Method & Endpoint**: `POST https://www.googleapis.com/calendar/v3/calendars/{calendarId}/events?conferenceDataVersion=1`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/calendar.events`

#### 📥 Input (요청 본문 Body)
```json
{
  "summary": "[후속 회의] 리테일 회사 AI 협업포털 2차 아키텍처 점검",
  "description": "1차 회의 Action Items 진행 경과 점검 및 Cloud Run 프로덕션 배포 검토",
  "start": {
    "dateTime": "2026-08-25T14:00:00+09:00",
    "timeZone": "Asia/Seoul"
  },
  "end": {
    "dateTime": "2026-08-25T15:00:00+09:00",
    "timeZone": "Asia/Seoul"
  },
  "attendees": [
    {"email": "hong@example.com"},
    {"email": "sung@example.com"},
    {"email": "ce@google.com"}
  ],
  "conferenceData": {
    "createRequest": {
      "requestId": "sample-req-20260825-01",
      "conferenceSolutionKey": {
        "type": "hangoutsMeet"
      }
    }
  }
}
```

#### 📤 Output (응답 데이터)
```json
{
  "id": "evt_meet_20260825_followup",
  "status": "confirmed",
  "htmlLink": "https://www.google.com/calendar/event?eid=...",
  "hangoutLink": "https://meet.google.com/xyz-uvwx-rst",
  "conferenceData": {
    "entryPoints": [
      {
        "entryPointType": "video",
        "uri": "https://meet.google.com/xyz-uvwx-rst"
      }
    ]
  }
}
```

---

## 🛠️ 3. Python 연동 코드 예제 (Quickstart)

```python
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime

# 1. OAuth 토큰으로 Calendar API 클라이언트 생성
creds = Credentials.from_authorized_user_file("token.json", ["https://www.googleapis.com/auth/calendar.readonly"])
service = build("calendar", "v3", credentials=creds)

# 2. 오늘 진행된 회의 목록 조회
now = datetime.datetime.utcnow().isoformat() + "Z"
events_result = service.events().list(
    calendarId="primary",
    timeMin=now,
    maxResults=10,
    singleEvents=True,
    orderBy="startTime"
).execute()

events = events_result.get("items", [])

# 3. 회의 메타데이터 추출
for event in events:
    title = event.get("summary", "제목 없음")
    start = event["start"].get("dateTime", event["start"].get("date"))
    meet_link = event.get("hangoutLink", "Meet 링크 없음")
    attendees = [att.get("displayName", att.get("email")) for att in event.get("attendees", [])]
    
    print(f"📌 회의: {title}")
    print(f"   ⏰ 일시: {start}")
    print(f"   📹 Meet: {meet_link}")
    print(f"   👥 참석자: {", ".join(attendees)}\n")
```

---

## 🚨 4. 주요 HTTP 에러 코드 및 트러블슈팅

| HTTP 상태 코드 | 원인 (Cause) | 해결 방안 (Solution) |
| :--- | :--- | :--- |
| **`401 Unauthorized`** | Access Token 만료 또는 유효하지 않은 인증 | `token.json`의 Refresh Token으로 자동 갱신(`creds.refresh(Request())`)하거나 재로그인 |
| **`403 Forbidden`** | OAuth Scope 권한 부족 또는 API 비활성화 | 1) GCP 콘솔에서 `Google Calendar API` 활성화 확인<br/>2) 올바른 Scope(`calendar.readonly` / `calendar.events`) 요청 확인 |
| **`404 Not Found`** | 존재하지 않는 `calendarId` 또는 `eventId` | `calendarId="primary"` 확인 및 유효한 이벤트 ID 파라미터 검증 |
| **`400 Bad Request`** | 날짜 포맷 오류 또는 잘못된 쿼리 파라미터 | `timeMin`/`timeMax`가 ISO 8601 형식(`YYYY-MM-DDTHH:MM:SSZ`)인지 확인 |
