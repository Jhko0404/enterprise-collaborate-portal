#!/usr/bin/env python3
"""
📅 Google Calendar 연동 서비스 헬퍼 모듈
- 기능:
  1. 사용자 캘린더 일정 목록 조회 (timeMin, timeMax)
  2. 회의 제목, 일시, 참석자 명단 문자열 파싱
  3. Google Meet 회의 코드 및 Space ID 추출
"""

import datetime
from typing import Dict, Any, List, Optional
import os


class CalendarService:
    def __init__(self, service=None):
        self.service = service

    def parse_event_details(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """캘린더 이벤트 객체에서 AI 회의록 생성에 필요한 필드를 추출 및 가공합니다."""
        event_id = event.get("id")
        summary = event.get("summary", "제목 없는 회의")
        description = event.get("description", "")
        
        # 시작 및 종료 일시 파싱
        start_obj = event.get("start", {})
        end_obj = event.get("end", {})
        start_time = start_obj.get("dateTime", start_obj.get("date", ""))
        end_time = end_obj.get("dateTime", end_obj.get("date", ""))
        
        # Google Meet 화상회의 정보 추출
        meet_link = event.get("hangoutLink", "")
        conference_data = event.get("conferenceData", {})
        entry_points = conference_data.get("entryPoints", [])
        for ep in entry_points:
            if ep.get("entryPointType") == "video":
                meet_link = ep.get("uri", meet_link)

        meet_code = ""
        if "meet.google.com/" in meet_link:
            meet_code = meet_link.split("meet.google.com/")[-1].split("?")[0]

        # 참석자 명단 파싱
        raw_attendees = event.get("attendees", [])
        attendee_list = []
        for att in raw_attendees:
            name = att.get("displayName")
            email = att.get("email", "")
            if name:
                attendee_list.append(f"{name} ({email})" if email else name)
            elif email:
                attendee_list.append(email)

        attendees_str = ", ".join(attendee_list) if attendee_list else "참석자 정보 없음"

        return {
            "event_id": event_id,
            "title": summary,
            "description": description,
            "start_time": start_time,
            "end_time": end_time,
            "meet_link": meet_link,
            "meet_code": meet_code,
            "attendees_list": attendee_list,
            "attendees_str": attendees_str,
            "has_meet": bool(meet_link)
        }
