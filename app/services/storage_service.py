import os
import uuid
from datetime import datetime
from google.cloud import storage
from app.core.config import settings
from app.core.exceptions import StorageError
from app.core.auth_utils import get_google_credentials

MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
}

class GCSStorageService:
    @classmethod
    def get_client(cls) -> storage.Client:
        creds = get_google_credentials()
        if creds:
            return storage.Client(project=settings.GCP_PROJECT_ID, credentials=creds)
        return storage.Client(project=settings.GCP_PROJECT_ID)

    @classmethod
    def upload_temp_audio(cls, local_file_path: str, blob_name: str = None) -> str:
        """GCS 임시 버킷에 오디오 업로드 후 gs:// URI 반환 (청크 업로드 및 타임아웃 600초 적용)"""
        try:
            client = cls.get_client()
            bucket = client.bucket(settings.TEMP_GCS_BUCKET)
            
            ext = os.path.splitext(local_file_path)[1].lower() or ".wav"
            if not blob_name:
                blob_name = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"

            content_type = MIME_MAP.get(ext, "audio/wav")
            blob = bucket.blob(blob_name, chunk_size=8 * 1024 * 1024) # 8MB Chunk
            blob.upload_from_filename(local_file_path, content_type=content_type, timeout=600)
            
            gcs_uri = f"gs://{settings.TEMP_GCS_BUCKET}/{blob_name}"
            return gcs_uri
        except Exception as e:
            raise StorageError(f"GCS 오디오 업로드 실패: {e}")

    @classmethod
    def upload_file(cls, local_file_path: str, blob_name: str = None) -> str:
        """upload_temp_audio의 별칭 메서드"""
        return cls.upload_temp_audio(local_file_path, blob_name)

    @classmethod
    def create_resumable_upload_session(cls, filename: str, content_type: str = "application/octet-stream", origin: str = None) -> dict:
        """GCS 직접 이어올리기(Resumable Upload) 세션 URL 발급"""
        try:
            client = cls.get_client()
            bucket = client.bucket(settings.TEMP_GCS_BUCKET)
            safe_name = os.path.basename(filename).replace(" ", "_")
            blob_name = f"direct_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}_{safe_name}"
            blob = bucket.blob(blob_name)
            
            ext = os.path.splitext(filename)[1].lower()
            effective_content_type = MIME_MAP.get(ext, content_type or "application/octet-stream")
            
            # GCS Resumable Upload에서 브라우저 CORS PUT 요청을 허용하기 위해 origin 파라미터 전달
            effective_origin = origin if (origin and origin != "*") else "https://enterprise-agent-gateway.uc.gateway.dev"
            session_url = blob.create_resumable_upload_session(
                content_type=effective_content_type,
                origin=effective_origin
            )
            
            gcs_uri = f"gs://{settings.TEMP_GCS_BUCKET}/{blob_name}"
            return {
                "upload_url": session_url,
                "gcs_uri": gcs_uri,
                "blob_name": blob_name,
                "bucket": settings.TEMP_GCS_BUCKET
            }
        except Exception as e:
            raise StorageError(f"GCS Resumable 세션 발급 실패: {e}")

    @classmethod
    def download_to_file(cls, gcs_uri: str, local_path: str) -> str:
        """GCS 파일을 로컬 경로로 다운로드"""
        try:
            path_parts = gcs_uri.replace("gs://", "").split("/", 1)
            bucket_name, blob_name = path_parts
            client = cls.get_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.download_to_filename(local_path)
            return local_path
        except Exception as e:
            raise StorageError(f"GCS 파일 다운로드 실패: {e}")

    @classmethod
    def delete_temp_audio(cls, gcs_uri: str) -> bool:
        """작업 완료 후 GCS 임시 파일 즉시 삭제 (Zero Data Retention)"""
        try:
            if not gcs_uri or not gcs_uri.startswith("gs://"):
                return False
            path_parts = gcs_uri.replace("gs://", "").split("/", 1)
            if len(path_parts) != 2:
                return False
            bucket_name, blob_name = path_parts
            client = cls.get_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            if blob.exists():
                blob.delete()
            return True
        except Exception:
            return False
