import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from app.core.config import settings
from app.core.exceptions import AuthenticationError

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/documents",
]

class AuthService:
    @staticmethod
    def get_credentials(allow_interactive: bool = True) -> Credentials:
        """OAuth 2.0 User Consent 기반 인증 토큰 획득 및 갱신 (token.json 캐싱)"""
        creds = None
        if os.path.exists(settings.TOKEN_FILE_PATH):
            try:
                creds = Credentials.from_authorized_user_file(settings.TOKEN_FILE_PATH, SCOPES)
            except Exception:
                creds = None

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    creds = None
            
            if not creds:
                if not allow_interactive:
                    raise AuthenticationError("OAuth 인증 토큰(token.json)이 유효하지 않습니다.")
                
                if not os.path.exists(settings.CREDENTIALS_FILE_PATH):
                    raise AuthenticationError(
                        f"'{settings.CREDENTIALS_FILE_PATH}' 파일이 필요합니다. GCP 콘솔에서 OAuth 클라이언트 ID(데스크톱 앱)를 다운로드하여 저장하십시오."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(settings.CREDENTIALS_FILE_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(settings.TOKEN_FILE_PATH, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        return creds
