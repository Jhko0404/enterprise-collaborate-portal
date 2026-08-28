#!/usr/bin/env python3
"""
📅 Google Calendar API v3 Python Quickstart (공식 표준 예제)
공식 문서: https://developers.google.com/workspace/calendar/api/quickstart/python
"""

import datetime
import os.path
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 읽기 전용 권한 범위
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    """사용자의 캘린더에서 다음 10개 일정을 조회하여 출력합니다."""
    creds = None
    token_path = os.path.join(ROOT_DIR, "token.json")
    creds_path = os.path.join(ROOT_DIR, "credentials.json")

    # 1. 기존 token.json 확인
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # 2. 유효한 토큰이 없으면 로그인 인증 절차 진행
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print(f"❌ [오류] {creds_path} 파일이 필요합니다.")
                print("   GCP Console > API 및 서비스 > 사용자 인증 정보에서 OAuth 클라이언트 ID(데스크톱 앱)를 다운로드하세요.")
                return
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=8088)
        # 토큰 저장
        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        print(f"✅ 인증 성공! 토큰 저장: {token_path}")

    try:
        service = build("calendar", "v3", credentials=creds)

        # 현재 시각 이후의 다가오는 일정 10개 조회
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print("\n📅 [Google Calendar] 다가오는 10개 회의 일정 조회 중...")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("ℹ️ 예정된 회의 일정이 없습니다.")
            return

        print(f"총 {len(events)}개의 일정을 발견했습니다:\n")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get("summary", "(제목 없음)")
            meet_link = event.get("hangoutLink", "없음")
            attendees = [a.get("email") for a in event.get("attendees", []) if "email" in a]
            
            print(f"• 📌 [{start}] {summary}")
            print(f"   - Meet 링크: {meet_link}")
            if attendees:
                print(f"   - 참석자 ({len(attendees)}명): {', '.join(attendees[:4])}{' 외' if len(attendees) > 4 else ''}")
            print()

    except HttpError as error:
        print(f"❌ API 오류 발생: {error}")


if __name__ == "__main__":
    main()
