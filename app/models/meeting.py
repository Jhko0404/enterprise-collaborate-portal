from pydantic import BaseModel, Field
from typing import List, Optional

class AttendeeModel(BaseModel):
    name: str = Field(description="참석자 이름")
    email: Optional[str] = Field(default="", description="참석자 이메일")
    role: Optional[str] = Field(default="", description="직책 또는 부서")

class MeetingMetadata(BaseModel):
    event_id: str
    title: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    attendees: List[str] = []
    drive_file_id: Optional[str] = None
    template_type: str = "CFT_REGULAR"
