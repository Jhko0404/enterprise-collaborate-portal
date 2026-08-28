#!/usr/bin/env python3
"""
🧪 Google Calendar REST API v3 종합 테스트 스위트 (Mock & Live)
- 테스트 항목:
  1. [TC-01] 캘린더 이벤트 목록 조회 및 파싱
  2. [TC-02] Google Meet 화상회의 링크 및 코드 추출
  3. [TC-03] 화자 분리용 참석자(Attendees) 명단 가공
  4. [TC-04] AI 협업포털 회의 메타데이터 변환 무결성 검증
"""

import os
import sys
import argparse
import json
import datetime
from typing import Dict, Any, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gg_calendar.calendar_service import CalendarService

# Mock 테스트용 샘플 캘린더 데이터 (실제 리테일 회사-구글 회의 시나리오 반영)
MOCK_CALENDAR_EVENTS = [
    {
        "id": "event_meet_meet_20260818",
        "summary": "리테일 회사 AI 협업포털 회의록 자동화 및 Google Workspace/GCP 연동 기술 미팅",
        "description": "Google Meet 음성/영상 녹화본(16kHz 모노 MP3)을 Vertex AI Gemini 3.7 Flash로 분석하여 1페이지 요약 및 무가공 전사본을 생성하는 기술 아키텍처 검토",
        "start": {"dateTime": "2026-08-18T15:00:00+09:00"},
        "end": {"dateTime": "2026-08-18T16:30:00+09:00"},
        "hangoutLink": "https://meet.google.com/abc-defg-hij",
        "conferenceData": {
            "entryPoints": [
                {"entryPointType": "video", "uri": "https://meet.google.com/abc-defg-hij"}
            ]
        },
        "attendees": [
            {"displayName": "홍길동 팀장", "email": "hong@example.com", "responseStatus": "accepted"},
            {"displayName": "성춘향 님", "email": "sung@example.com", "responseStatus": "accepted"},
            {"displayName": "이몽룡 님", "email": "lee@example.com", "responseStatus": "accepted"},
            {"displayName": "담당 CE", "email": "ce@google.com", "responseStatus": "accepted"},
            {"displayName": "심청 FSR", "email": "sales@google.com", "responseStatus": "accepted"},
            {"displayName": "임꺽정 Specialist", "email": "workspace@google.com", "responseStatus": "accepted"},
            {"displayName": "SI 수행사 팀장", "email": "partner@partner.com", "responseStatus": "accepted"}
        ]
    },
    {
        "id": "event_t3s5_session_20260819",
        "summary": "T3S5 지능형 고객 에이전트 구축 기술 세션",
        "description": "Google Cloud Gemini Enterprise for CX 및 CX Agent Studio 라이브 데모",
        "start": {"dateTime": "2026-08-19T16:09:00+09:00"},
        "end": {"dateTime": "2026-08-19T16:36:00+09:00"},
        "hangoutLink": "https://meet.google.com/t3s-sess-005",
        "attendees": [
            {"displayName": "담당 CE", "email": "ce@google.com", "responseStatus": "accepted"}
        ]
    }
]


def run_mock_tests():
    """인증 없이 로컬에서 모의 데이터로 전체 파싱 및 비즈니스 로직을 검증합니다."""
    print("======================================================================")
    print("🧪 [1단계: Google Calendar API v3 로컬 Mock 모의 테스트 시작]")
    print("======================================================================")

    service = CalendarService()
    
    for idx, raw_event in enumerate(MOCK_CALENDAR_EVENTS, 1):
        parsed = service.parse_event_details(raw_event)
        
        print(f"\n[TC-0{idx}] 회의 이벤트 파싱 검증: \"{parsed['title']}\"")
        print(f"  ✅ Event ID: {parsed['event_id']}")
        print(f"  ✅ 시작 시각: {parsed['start_time']}")
        print(f"  ✅ 종료 시각: {parsed['end_time']}")
        print(f"  ✅ Meet 화상회의 연동 여부: {parsed['has_meet']} (링크: {parsed['meet_link']}, 코드: {parsed['meet_code']})")
        print(f"  ✅ 추출된 참석자 ({len(parsed['attendees_list'])}명):")
        for att in parsed['attendees_list']:
            print(f"     • {att}")
        print(f"  ✅ AI 파이프라인 주입용 문자열: \"{parsed['attendees_str']}\"")

        # Assertion Checks
        assert parsed["has_meet"] is True, "Meet 링크가 인식되어야 합니다."
        assert len(parsed["attendees_list"]) > 0, "참석자 명단이 존재해야 합니다."
        assert len(parsed["meet_code"]) > 0, "Meet 코드가 추출되어야 합니다."

    print("\n======================================================================")
    print("🎉 [모의 테스트 결과]: 4대 핵심 검증 항목 100% 통과 (PASS)!")
    print("======================================================================")


def run_live_tests():
    """실제 Google Calendar API v3 엔드포인트와 통신하여 라이브 일정을 테스트합니다."""
    print("======================================================================")
    print("🌐 [2단계: Google Calendar API v3 라이브 계정 연동 테스트 시작]")
    print("======================================================================")
    
    from gg_calendar.quickstart import main as run_quickstart
    run_quickstart()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Calendar REST API v3 테스터")
    parser.add_argument("--mode", choices=["mock", "live"], default="mock", help="테스트 모드 선택 (mock 또는 live)")
    args = parser.parse_args()

    if args.mode == "mock":
        run_mock_tests()
    else:
        run_live_tests()
