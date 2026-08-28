import os
from pydantic_settings import BaseSettings
from pydantic import Field

# CloudTop 환경 호환성을 위해 client cert 자동 비활성화
os.environ.setdefault("GOOGLE_API_USE_CLIENT_CERTIFICATE", "false")

class Settings(BaseSettings):
    GCP_PROJECT_ID: str = Field(default="your-gcp-project-id", env="GCP_PROJECT_ID")
    GCP_LOCATION: str = Field(default="global", env="GCP_LOCATION")
    TEMP_GCS_BUCKET: str = Field(default="your-gcp-project-id-meet-audio-temp", env="TEMP_GCS_BUCKET")
    
    # Deployed Service & Gateway Endpoints
    CLOUD_RUN_SERVICE_URL: str = Field(
        default="http://localhost:9090",
        env="CLOUD_RUN_SERVICE_URL"
    )
    AGENT_GATEWAY_URL: str = Field(
        default="http://localhost:9090",
        env="AGENT_GATEWAY_URL"
    )

    # Gemini Model Parameters
    GEMINI_MODEL_NAME: str = "gemini-3.7-flash"
    GEMINI_TEMPERATURE: float = 0.2
    GEMINI_MAX_OUTPUT_TOKENS: int = 4096
    
    # OAuth Credentials & Token Paths
    CREDENTIALS_FILE_PATH: str = "credentials.json"
    TOKEN_FILE_PATH: str = "token.json"
    
    # Audio & Temp Settings
    TEMP_DIR_CLEANUP: bool = True
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHANNELS: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
