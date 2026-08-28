# 📹 Google Meet API v2 고객 맞춤형 실전 가이드
> **Google Workspace Meet 회의 공간 생성, 녹화본 자동 수집, 참석자 이력 및 AI 회의록 연동 가이드**

---

## 📌 1. 개요 및 비즈니스 가치 (Why Google Meet API v2?)

코웨이 AI 협업포털은 **Google Meet REST API v2**를 통해 회의 공간(Space) 자동 생성부터 회의 종료 후 생성된 **클라우드 녹화본(Drive 비디오)과 참석자 명단을 사람의 개입 없이 100% 자동 수집**하여 AI 회의록 파이프라인으로 연결합니다.

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   📹 Google Meet API v2 연동 흐름                                      │
├─────────────────────────┬─────────────────────────┬─────────────────────────┬──────────────────────────┤
│ 1. 회의 공간(Space) 생성│ 2. 회의 진행 & 녹화 완료│ 3. 녹화본 Drive ID 추출 │ 4. Vertex AI 회의록 완성 │
│ "spaces.create"         │ "conferenceRecords"     │ "recordings.list"       │ "Gemini 3.7 Flash 분석"  │
│ ➔ 1초 만에 Meet 링크 발급│ ➔ 참석자/시간 자동 기록 │ ➔ Google Drive 비디오 연동│ ➔ 화자분리 & 맞춤형 회의록│
└─────────────────────────┴─────────────────────────┴─────────────────────────┴──────────────────────────┘
```

### 🔑 핵심 연계 데이터 매핑
1. **회의 공간 링크 (`meetingUri` / `meetingCode`)** ➔ 캘린더 일정 및 사내 메신저 초대 링크로 즉시 배포
2. **클라우드 녹화본 (`driveDestination.file`)** ➔ Google Drive에 저장된 MP4 영상을 백엔드로 자동 인입
3. **실제 참석자 목록 (`participants`)** ➔ 실제 회의에 접속한 사람들의 입장/퇴장 시간 및 화자 라벨 매핑에 활용
4. **실시간 발화 턴 (`transcriptEntries`)** ➔ 실시간 음성 자막 데이터를 Gemini 3.7 Flash의 전사 보조 데이터로 활용

---

## 📚 2. 주요 Meet API 리스트별 Input & Output 상세 가이드

Google Meet API v2는 크게 **1) 회의 공간 관리(Spaces)**와 **2) 회의 기록/아티팩트 관리(Conference Records)**의 2개 도메인으로 나뉩니다.

---

### 1️⃣ `spaces.create` — 새 회의 공간 생성 & Meet 링크 발급 (⭐ 핵심 API)
> 코웨이 전용 Google Meet 회의방을 동적으로 생성하고, 고유 회의 링크(`https://meet.google.com/...`)와 회의 코드를 발급합니다.

* **HTTP Method & Endpoint**: `POST https://meet.googleapis.com/v2/spaces`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/meetings.space.created`

#### 📥 Input (요청 본문 Body)
| 필드명 | 타입 | 필수 여부 | 기본값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `config.accessType` | String | 선택 | `OPEN` | 회의 입장 보안 정책 (`OPEN`: 누구나, `TRUSTED`: 사내 조직원, `RESTRICTED`: 초대된 사람만) |
| `config.entryPointAccess` | String | 선택 | `ALL` | 참여 방법 (`ALL`: 화상/전화 접속 허용) |

```json
{
  "config": {
    "accessType": "TRUSTED",
    "entryPointAccess": "ALL"
  }
}
```

#### 📤 Output (응답 데이터 구조 및 예시)
```json
{
  "name": "spaces/xyz-uvwx-rst",
  "meetingUri": "https://meet.google.com/xyz-uvwx-rst",
  "meetingCode": "xyz-uvwx-rst",
  "config": {
    "accessType": "TRUSTED",
    "entryPointAccess": "ALL"
  },
  "activeConference": {}
}
```

---

### 2️⃣ `conferenceRecords.list` — 완료된 회의 기록 목록 조회
> 특정 회의 공간이나 특정 기간 동안 진행된 실제 회의 세션 이력(`conferenceRecords`)을 조회합니다.

* **HTTP Method & Endpoint**: `GET https://meet.googleapis.com/v2/conferenceRecords`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/meetings.space.readonly`

#### 📥 Input (요청 파라미터)
| 파라미터명 | 타입 | 필수 여부 | 예시 값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `filter` | String | 선택 | `space.name="spaces/xyz-uvwx-rst"` | 특정 회의 공간 또는 시작/종료 기간 필터링 |
| `pageSize` | Integer | 선택 | `10` | 한 번에 가져올 최대 회의 기록 수 |
| `pageToken` | String | 선택 | `"next_page_token_..."` | 다음 페이지 조회를 위한 토큰 |

#### 📤 Output (응답 데이터 구조 및 예시)
```json
{
  "conferenceRecords": [
    {
      "name": "conferenceRecords/conf_20260820_98765",
      "startTime": "2026-08-20T14:00:15.123Z",
      "endTime": "2026-08-20T15:00:30.456Z",
      "space": "spaces/xyz-uvwx-rst",
      "expireTime": "2026-09-19T15:00:30.456Z"
    }
  ]
}
```

---

### 3️⃣ `recordings.list` — 클라우드 녹화본 비디오 조회 및 Drive ID 획득 (⭐ 핵심 API)
> Google Meet 녹화가 완료된 후 클라우드에 생성된 영상 파일의 **Google Drive File ID**와 녹화 상태를 조회합니다.

* **HTTP Method & Endpoint**: `GET https://meet.googleapis.com/v2/conferenceRecords/{recordId}/recordings`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/meetings.conference.media.readonly`

#### 📥 Input (요청 파라미터)
| 파라미터명 | 타입 | 필수 여부 | 예시 값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `parent` | String | **필수** | `conferenceRecords/conf_20260820_98765` | 상위 회의 기록 고유 리소스 경로 |

#### 📤 Output (응답 데이터 구조 및 예시)
```json
{
  "recordings": [
    {
      "name": "conferenceRecords/conf_20260820_98765/recordings/rec_001",
      "state": "ENDED",
      "startTime": "2026-08-20T14:01:00Z",
      "endTime": "2026-08-20T14:59:45Z",
      "driveDestination": {
        "file": "1AbCdEfGhIjKlMnOpQrStUvWxYz_12345",
        "exportUri": "https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz_12345/view"
      }
    }
  ]
}
```
> 💡 **연계 포인트**: 추출된 `driveDestination.file` (Google Drive ID)을 통해 백엔드가 영상을 즉시 다운로드하여 오디오 분리(FFmpeg) 및 회의록 생성 파이프라인을 가동합니다.

---

### 4️⃣ `participants.list` — 실제 회의 참석자 및 접속 시간 이력 조회
> 회의에 실제 입장한 참석자들의 Google 계정 프로필, 입장 시각, 퇴장 시각을 정밀하게 조회합니다.

* **HTTP Method & Endpoint**: `GET https://meet.googleapis.com/v2/conferenceRecords/{recordId}/participants`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/meetings.space.readonly`

#### 📥 Input (요청 파라미터)
| 파라미터명 | 타입 | 필수 여부 | 예시 값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `parent` | String | **필수** | `conferenceRecords/conf_20260820_98765` | 대상 회의 기록 리소스 경로 |

#### 📤 Output (응답 데이터 구조 및 예시)
```json
{
  "participants": [
    {
      "name": "conferenceRecords/conf_20260820_98765/participants/part_user_01",
      "signedinUser": {
        "user": "users/1122334455",
        "displayName": "김유진 팀장"
      },
      "earliestStartTime": "2026-08-20T14:00:15Z",
      "latestEndTime": "2026-08-20T15:00:20Z"
    },
    {
      "name": "conferenceRecords/conf_20260820_98765/participants/part_user_02",
      "signedinUser": {
        "user": "users/9988776655",
        "displayName": "고정현 CE"
      },
      "earliestStartTime": "2026-08-20T14:00:20Z",
      "latestEndTime": "2026-08-20T15:00:30Z"
    }
  ]
}
```

---

### 5️⃣ `transcriptEntries.list` — 실시간 전사 턴 및 발화 텍스트 조회
> Google Meet 자체 실시간 자막 기능으로 캡처된 발화자별 세부 대화 문장과 타임스탬프 목록을 조회합니다.

* **HTTP Method & Endpoint**: `GET https://meet.googleapis.com/v2/conferenceRecords/{recordId}/transcripts/{transcriptId}/entries`
* **필수 권한 (Scope)**: `https://www.googleapis.com/auth/meetings.conference.transcripts.readonly`

#### 📥 Input (요청 파라미터)
| 파라미터명 | 타입 | 필수 여부 | 예시 값 | 설명 |
| :--- | :---: | :---: | :---: | :--- |
| `parent` | String | **필수** | `conferenceRecords/.../transcripts/trans_001` | 대상 전사본 리소스 경로 |

#### 📤 Output (응답 데이터 구조 및 예시)
```json
{
  "transcriptEntries": [
    {
      "name": "conferenceRecords/.../transcripts/trans_001/entries/entry_01",
      "participant": "conferenceRecords/.../participants/part_user_01",
      "text": "오늘 회의에서는 코웨이 AI 협업포털 회의록 자동화 아키텍처를 점검하겠습니다.",
      "languageCode": "ko-KR",
      "startTime": "2026-08-20T14:01:05.120Z",
      "endTime": "2026-08-20T14:01:10.540Z"
    }
  ]
}
```

---

## 🛠️ 3. Python SDK 연동 코드 예제 (`google-apps-meet`)

```python
from google.apps import meet_v2
from google.oauth2.credentials import Credentials

# 1. OAuth 2.0 클라이언트 초기화
creds = Credentials.from_authorized_user_file("token.json")
spaces_client = meet_v2.SpacesServiceClient(credentials=creds)
conf_client = meet_v2.ConferenceRecordsServiceClient(credentials=creds)

# 2. 신규 회의 공간 생성
space = spaces_client.create_space(
    request=meet_v2.CreateSpaceRequest(
        space=meet_v2.Space(
            config=meet_v2.SpaceConfig(access_type=meet_v2.SpaceConfig.AccessType.TRUSTED)
        )
    )
)
print(f"✅ 회의방 생성: {space.meeting_uri} (코드: {space.meeting_code})")

# 3. 회의 종료 후 녹화본 Drive 파일 ID 자동 수집
records = conf_client.list_conference_records(
    request=meet_v2.ListConferenceRecordsRequest(
        filter=f"space.name="{space.name}"",
        page_size=1
    )
)

for rec in records:
    print(f"📁 회의 기록 발견: {rec.name}")
    recordings = conf_client.list_recordings(parent=rec.name)
    for recording in recordings:
        if recording.state == meet_v2.Recording.State.ENDED and recording.drive_destination:
            drive_file_id = recording.drive_destination.file
            print(f"🎬 녹화 완료! Drive File ID: {drive_file_id}")
            # 👉 백엔드 회의록 생성 파이프라인으로 drive_file_id 전달
```

---

## 🚨 4. 주요 HTTP 에러 코드 및 트러블슈팅

| HTTP 상태 코드 | 원인 (Cause) | 해결 방안 (Solution) |
| :--- | :--- | :--- |
| **`403 Permission Denied`** | OAuth Scope 미부여 또는 Google Workspace 계정 권한 부족 | 1) `meetings.space.created` 및 `meetings.conference.media.readonly` Scope 확인<br/>2) Google Workspace 관리 콘솔에서 Meet 녹화 권한 활성화 여부 확인 |
| **`404 Not Found`** | 존재하지 않는 회의 공간 또는 회의 기록 ID | 생성된 `space.name` (`spaces/{spaceId}`) 문자열 형식 재확인 |
| **`Recording State: RECORDING`** | 회의 녹화가 진행 중이거나 Google Drive 인코딩 처리 중 | `recording.state == ENDED`가 될 때까지 30초 간격 폴링(Polling) 대기 |
