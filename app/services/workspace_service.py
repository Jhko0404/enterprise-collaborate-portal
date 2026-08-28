import io
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from app.services.auth_service import AuthService
from app.core.exceptions import WorkspaceAPIError

class WorkspaceService:
    def __init__(self, allow_interactive: bool = True):
        self.creds = AuthService.get_credentials(allow_interactive=allow_interactive)
        self.calendar_client = build("calendar", "v3", credentials=self.creds)
        self.drive_client = build("drive", "v3", credentials=self.creds)
        self.docs_client = build("docs", "v1", credentials=self.creds)

    def list_recorded_meetings(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """최근 회의 목록 조회"""
        try:
            events_result = self.calendar_client.events().list(
                calendarId="primary",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            
            meetings = []
            for ev in events:
                attendees = [a.get("email", "") for a in ev.get("attendees", [])]
                meetings.append({
                    "event_id": ev.get("id"),
                    "title": ev.get("summary", "제목 없음"),
                    "start_time": ev.get("start", {}).get("dateTime"),
                    "attendees": attendees
                })
            return meetings
        except Exception as e:
            raise WorkspaceAPIError(f"Google Calendar 목록 조회 실패: {e}")

    def download_drive_video(self, file_id: str, destination_path: str) -> str:
        """Google Drive 비디오 파일 스트리밍 다운로드"""
        try:
            request = self.drive_client.files().get_media(fileId=file_id)
            with io.FileIO(destination_path, "wb") as fh:
                downloader = MediaIoBaseDownload(fh, request, chunksize=10*1024*1024) # 10MB chunk
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            return destination_path
        except Exception as e:
            raise WorkspaceAPIError(f"Google Drive 파일 다운로드 실패 (ID: {file_id}): {e}")

    def create_meeting_doc(self, title: str, markdown_content: str) -> str:
        """Google Docs 회의록 문서 생성 및 본문 입력"""
        try:
            doc = self.docs_client.documents().create(body={"title": f"[회의록] {title}"}).execute()
            doc_id = doc.get("documentId")

            requests = [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": markdown_content
                    }
                }
            ]
            self.docs_client.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
            return f"https://docs.google.com/document/d/{doc_id}/edit"
        except Exception as e:
            raise WorkspaceAPIError(f"Google Docs 생성 실패: {e}")
