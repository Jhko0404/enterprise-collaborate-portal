#!/usr/bin/env python3
"""
🎬 Google Meet 회의 녹화본 조회 스크립트 (Simple Recording Checker)
- 경로: /usr/local/google/home/junghyunko/git/2026-AI/collaborate-portal/gg_meet/get_meeting_recordings.py
- 지원 조회 방식:
  1. Google Meet API v2 기반 조회 (ConferenceRecords -> Recordings)
  2. Google Drive API v3 기반 조회 (Drive 내 Meet Recordings 영상 파일 검색)
"""

import os
import sys
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

SCOPES = [
    "https://www.googleapis.com/auth/meetings.conference.media.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]

def get_credentials(token_file: str = "token.json", creds_file: str = "credentials.json"):
    """
    Credentials 획득 (우선순위: token.json -> credentials.json OAuth -> ADC)
    """
    token_path = os.path.join(ROOT_DIR, token_file)
    creds_path = os.path.join(ROOT_DIR, creds_file)

    # 1. 기존 발급된 OAuth token.json 확인
    if os.path.exists(token_path):
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if creds and creds.valid:
                return creds
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, "w", encoding="utf-8") as f:
                    f.write(creds.to_json())
                return creds
        except Exception:
            pass

    # 2. OAuth 클라이언트 credentials.json이 있는 경우 브라우저 플로우 실행
    if os.path.exists(creds_path):
        from google_auth_oauthlib.flow import InstalledAppFlow
        print("🌐 [OAuth 2.0] credentials.json을 감지하여 브라우저 계정 인증을 시작합니다...")
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        creds = flow.run_local_server(port=8085)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"✅ 인증 토큰 저장 완료: {token_path}")
        return creds

    # 3. Application Default Credentials (ADC) 확인
    try:
        import google.auth
        import google.auth.transport.requests
        adc_creds, project_id = google.auth.default(scopes=SCOPES)
        req = google.auth.transport.requests.Request()
        adc_creds.refresh(req)
        if adc_creds and adc_creds.valid:
            print(f"🔑 [ADC 인증] Google Cloud Application Default Credentials 사용 (Project: {project_id})")
            return adc_creds
    except Exception:
        pass

    # 4. 인증 정보가 모두 없는 경우 상세 가이드 출력
    print("=" * 75)
    print("⚠️ [Google Workspace / Meet API 인증 자격증명 필요]")
    print("=" * 75)
    print("Google Meet 및 Drive API를 호출하려면 아래 2가지 방법 중 하나를 선택해 주세요:\n")
    print("💡 [방법 1: OAuth 2.0 클라이언트 ID (가장 권장 - 개인 드라이브/미트 접근)]")
    print("  1. GCP 콘솔 접속: https://console.cloud.google.com/apis/credentials?project=jhk-ai-sandbox-378741")
    print("  2. '사용자 인증 정보 만들기' ➔ 'OAuth 클라이언트 ID' (유형: 데스크톱 앱) 생성")
    print("  3. 다운로드한 JSON 파일을 다음 경로에 'credentials.json' 이름으로 저장:")
    print(f"     👉 {creds_path}\n")
    print("💡 [방법 2: gcloud ADC 재인증]")
    print("  터미널에서 아래 명령어 실행:")
    print("  $ gcloud auth application-default login --project=jhk-ai-sandbox-378741")
    print("=" * 75 + "\n")
    return None

def query_via_meet_api(creds, max_records: int = 10):
    """방법 1: Google Meet API v2를 통한 최근 회의 녹화본 조회"""
    print("\n" + "=" * 70)
    print(f"📹 [방법 1] Google Meet API v2 기반 최근 {max_records}개 회의 녹화본 조회")
    print("=" * 70)

    try:
        from google.apps import meet_v2
        client = meet_v2.ConferenceRecordsServiceClient(credentials=creds)

        # 1. 최근 회의 기록 목록 가져오기
        req = meet_v2.ListConferenceRecordsRequest(page_size=max_records)
        records_pager = client.list_conference_records(request=req)
        
        found_records = list(records_pager)
        if not found_records:
            print("ℹ️ 최근 생성된 회의 기록(Conference Records)이 없습니다.")
            return

        print(f"총 {len(found_records)}개의 회의 기록을 조회했습니다:\n")

        for idx, rec in enumerate(found_records, 1):
            st = rec.start_time.strftime("%Y-%m-%d %H:%M:%S") if rec.start_time else "시작시각 미정"
            et = rec.end_time.strftime("%Y-%m-%d %H:%M:%S") if rec.end_time else "진행 중"
            
            print(f"[{idx}] 📁 회의 기록: {rec.name}")
            print(f"    • 일시: {st} ~ {et}")
            print(f"    • 연결 공간(Space): {rec.space}")

            # 2. 해당 회의의 녹화본 조회
            try:
                recordings = list(client.list_recordings(parent=rec.name))
                if not recordings:
                    print("    • 🎬 녹화본: ❌ 없음 (녹화 미실행)")
                else:
                    for r_idx, r in enumerate(recordings, 1):
                        print(f"    • 🎬 녹화본 [{r_idx}]: 상태={r.state.name}")
                        if r.drive_destination and r.drive_destination.file:
                            print(f"        - Google Drive File ID: {r.drive_destination.file}")
                            print(f"        - 바로가기 링크: {r.drive_destination.export_uri}")
            except Exception as e:
                print(f"    • 🎬 녹화본 조회 중 에러: {e}")
            print()

    except Exception as e:
        print(f"❌ Google Meet API 조회 실패: {e}")

def query_via_drive_api(creds, max_files: int = 10):
    """방법 2: Google Drive API v3를 통한 'Meet Recordings' 폴더/영상 파일 직접 검색"""
    print("\n" + "=" * 70)
    print(f"💾 [방법 2] Google Drive API v3 기반 Meet 녹화 파일 검색 (최대 {max_files}개)")
    print("=" * 70)

    try:
        from googleapiclient.discovery import build
        service = build("drive", "v3", credentials=creds)

        # 비디오 파일 및 Meet 녹화 관련 파일 검색 쿼리
        query = "trashed = false and (mimeType contains 'video/' or name contains 'Recording' or name contains 'MEET')"
        results = service.files().list(
            q=query,
            pageSize=max_files,
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        files = results.get("files", [])
        if not files:
            print("ℹ️ Google Drive 내에서 Meet 녹화본 파일을 찾을 수 없습니다.")
            return

        print(f"총 {len(files)}개의 녹화/비디오 파일이 발견되었습니다:\n")
        for idx, f in enumerate(files, 1):
            size_mb = float(f.get("size", 0)) / (1024 * 1024) if "size" in f else 0.0
            print(f"[{idx}] 🎥 파일명: {f.get('name')}")
            print(f"    • 🎯 Google Drive File ID: {f.get('id')}")
            print(f"    • 용량: {size_mb:.2f} MB")
            print(f"    • 생성일시: {f.get('createdTime')}")
            print(f"    • 재생/조회 링크: {f.get('webViewLink')}")
            print()

    except Exception as e:
        print(f"❌ Google Drive API 조회 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description="Google Meet 녹화본 간편 조회 도구")
    parser.add_argument(
        "--mode", choices=["all", "meet", "drive"], default="all",
        help="조회 방식 선택 (meet: Meet API v2, drive: Drive API v3, all: 둘 다 실행)"
    )
    parser.add_argument("--limit", type=int, default=5, help="조회할 최대 목록 개수 (기본값: 5)")
    args = parser.parse_args()

    creds = get_credentials()
    if not creds:
        return

    if args.mode in ["all", "meet"]:
        query_via_meet_api(creds, max_records=args.limit)

    if args.mode in ["all", "drive"]:
        query_via_drive_api(creds, max_files=args.limit)

if __name__ == "__main__":
    main()
