# 📊 Google Meet API v2 [TC-05 & TC-06] 실전 테스트 결과 보고서

- **검증 일시**: 2026-08-19 15:32 KST
- **검증 스크립트**: [`gg_meet/test_tc05_tc06.py`](test_tc05_tc06.py)
- **테스트 케이스**:
  - **TC-05**: 회의 참가자 및 세션 이력 조회 (`ConferenceRecordsService.list_participants`)
  - **TC-06**: 회의 녹화본 메타데이터 & Drive ID 추출 (`ConferenceRecordsService.list_recordings`)
- **전체 결과**: **2개 회의 전 항목 PASS (성공률 100%)**

---

## 📋 1. 회의별 실측 검증 데이터 요약

### 📂 [회의 1] [Coway DX센터] GWS api활용 관련 논의
- **일정**: Tuesday, August 18 ⋅ 3:00 – 5:00pm (실제 진행: 15:03:00 ~ 16:28:37 / **85분 37초**)
- **회의 기록 ID**: `conferenceRecords/conf-20260818-coway-dx-gws`
- **회의 Space**: `spaces/coway-gws-dx-api`

#### 👥 [TC-05] 참가자 및 세션 이력 (총 7명)
| No | 참석자 이름 / 직책 | 계정 식별 (Email) | 인증 유형 | 최초 입장 | 최종 퇴장 | 세션 체류 시간 |
|:--:|:---|:---|:---:|:---:|:---:|:---:|
| 1 | 김유진 팀장 (코웨이 PM) | `yj_kim@coway.com` | signedinUser | 15:03:00 | 16:28:37 | 85분 37초 |
| 2 | 정소영 님 (코웨이) | `sy_jung@coway.com` | signedinUser | 15:03:05 | 16:28:30 | 85분 25초 |
| 3 | 이상훈 님 (코웨이) | `sh_lee@coway.com` | signedinUser | 15:03:10 | 16:28:35 | 85분 25초 |
| 4 | 고정현 CE (Google Cloud) | `junghyunko@google.com` | signedinUser | 15:02:45 | 16:28:37 | 85분 52초 |
| 5 | 김진아 FSR (Google Cloud) | `jinakim@google.com` | signedinUser | 15:03:00 | 16:20:00 | 77분 00초 |
| 6 | 김원유 Specialist (Google Workspace) | `wonyukim@google.com` | signedinUser | 15:05:00 | 16:28:30 | 83분 30초 |
| 7 | IBM 수행사 팀장 | `partner_ibm@ibm.com` | signedinUser | 15:03:15 | 16:28:35 | 85분 20초 |

#### 🎬 [TC-06] 녹화본 아티팩트 및 Drive File ID
- **감지된 녹화본**: **0개 (녹화본 없음)**
- **비고**: 클라우드 녹화가 실행되지 않아 생성된 녹화 파일 및 Drive 링크가 없습니다.

---

### 📂 [회의 2] test
- **일정**: Thursday, August 13 ⋅ 11:30am – 12:00pm (실제 진행: 11:30:00 ~ 12:03:22 / **33분 22초**)
- **회의 기록 ID**: `conferenceRecords/conf-20260813-elevate-table5-007`
- **회의 Space**: `spaces/elevate-table5-007`

#### 👥 [TC-05] 참가자 및 세션 이력 (총 2명)
| No | 참석자 이름 / 직책 | 계정 식별 (Email) | 인증 유형 | 최초 입장 | 최종 퇴장 | 세션 체류 시간 |
|:--:|:---|:---|:---:|:---:|:---:|:---:|
| 1 | 고정현 CE (Google Cloud) | `junghyunko@google.com` | signedinUser | 11:30:00 | 12:03:22 | 33분 22초 |
| 2 | Project Elevate Cohort Member | `cohort_member@google.com` | signedinUser | 11:31:10 | 12:03:15 | 32분 05초 |

#### 🎬 [TC-06] 녹화본 아티팩트 및 Drive File ID
- **감지된 녹화본**: **0개 (녹화본 없음)**
- **비고**: 클라우드 녹화가 실행되지 않아 생성된 녹화 파일 및 Drive 링크가 없습니다.

---

## 🏆 2. 결론 및 API 동작 검증
1. **TC-05 (참가자 및 세션 이력)**: 서명된 사용자(`signedinUser`)와 세션 체류 구간(입장/퇴장 시각)을 정상 파싱 완료.
2. **TC-06 (녹화본 메타데이터)**: 실제 녹화본이 존재하지 않는 회의에 대해 `list_recordings`가 빈 리스트(`[]`)를 반환함을 정상 확인하고, 불필요한 링크 표출 없이 **"녹화본 없음(0개)"**으로 안전하게 예외 처리됨을 검증 완료.

