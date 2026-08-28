from pydantic import BaseModel, Field
from typing import List, Optional

class ActionItemModel(BaseModel):
    item_no: int = Field(description="항목 번호")
    task_description: str = Field(description="수행할 실행 과제 내용")
    assignee: str = Field(description="담당자 이름 (예: 홍길동)")
    due_date: str = Field(description="완료 목표 기한 (예: 2026-09-01)")
    priority: Optional[str] = Field(default="MEDIUM", description="우선순위 (HIGH / MEDIUM / LOW)")

class AgendaDiscussionModel(BaseModel):
    agenda_number: int = Field(description="안건 번호")
    agenda_title: str = Field(description="안건 제목")
    summary: str = Field(description="안건 논의 요약")
    key_points: List[str] = Field(default_factory=list, description="주요 논의 포인트")

class SpeakerHighlightModel(BaseModel):
    speaker_label: str = Field(description="화자 라벨 (예: [참석자 1] 또는 식별된 이름)")
    main_arguments: str = Field(description="해당 화자의 주요 발언 요약")

class TranscriptTurn(BaseModel):
    timestamp: str = Field(default="[00:00:00]", description="발언 타임스탬프 (예: [00:01:20])")
    speaker: str = Field(description="발언자 이름 또는 화자 라벨")
    text: str = Field(description="실제 발언 텍스트 전문")

class MeetingNotesLLMSchema(BaseModel):
    """LLM이 순수 데이터 객체로 생성하는 구조화 스키마 (마크다운 중복 제외로 토큰 절약 및 파싱 오류 방지)"""
    meeting_title: str = Field(description="회의 제목")
    template_type: str = Field(default="CFT_REGULAR", description="적용된 템플릿 유형")
    executive_summary: str = Field(description="3~5줄 분량의 핵심 요약")
    key_decisions: List[str] = Field(default_factory=list, description="주요 결정사항 목록")
    agenda_discussions: List[AgendaDiscussionModel] = Field(default_factory=list, description="안건별 논의 내용")
    action_items: List[ActionItemModel] = Field(default_factory=list, description="실행 과제 목록")
    speaker_highlights: List[SpeakerHighlightModel] = Field(default_factory=list, description="화자별 주요 발언")

class MeetingNotesResponse(MeetingNotesLLMSchema):
    formatted_markdown: str = Field(default="", description="완전한 서식이 적용된 마크다운 회의록 전문")

class MeetingFullPackage(BaseModel):
    notes: MeetingNotesResponse
    transcript_markdown: str = Field(description="화자 분리가 적용된 전체 대화 전문 스크립트 마크다운")

class ResumableSessionRequest(BaseModel):
    filename: str = Field(description="업로드할 파일명 (예: meeting.mp4)")
    content_type: Optional[str] = Field(default="application/octet-stream", description="MIME Content Type")
    origin: Optional[str] = Field(default=None, description="브라우저 Origin (CORS 검증용)")

class ResumableSessionResponse(BaseModel):
    status: str = "SUCCESS"
    upload_url: str
    gcs_uri: str
    blob_name: str
    bucket: str

class ProcessGCSMediaRequest(BaseModel):
    gcs_uri: str = Field(description="GCS 업로드 완료 URI (gs://...)")
    filename: str = Field(description="원본 파일명")
    title: str = Field(default="리테일 회사 미디어 회의", description="회의 제목")
    attendees: str = Field(default="참석자 미입력", description="참석자 명단")
    template_type: str = Field(default="CFT_REGULAR", description="회의록 템플릿")
