import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.storage_service import GCSStorageService
from app.core.config import settings

def test_gcs_storage():
    print("=== [테스트 2: Cloud Storage 임시 업로드 및 0-Day 보안 삭제 테스트] ===")
    
    # 1. 임시 더미 오디오 파일 생성
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        tf.write(b"RIFF" + b"\x00" * 100) # 더미 오디오 바이트
        dummy_file = tf.name

    try:
        # 2. GCS 업로드 검증
        print(f"1. GCS 버킷({settings.TEMP_GCS_BUCKET})으로 업로드 실행 중...")
        gcs_uri = GCSStorageService.upload_temp_audio(dummy_file)
        print(f"   ✅ 업로드 완료 URI: {gcs_uri}")
        assert gcs_uri.startswith(f"gs://{settings.TEMP_GCS_BUCKET}/"), "올바르지 않은 GCS URI 반환"

        # 3. 버킷 내 객체 존재 및 메타데이터 검증
        client = GCSStorageService.get_client()
        blob_name = gcs_uri.replace(f"gs://{settings.TEMP_GCS_BUCKET}/", "")
        bucket = client.bucket(settings.TEMP_GCS_BUCKET)
        blob = bucket.blob(blob_name)
        
        assert blob.exists(), "업로드된 Blob이 GCS 상에 존재하지 않음"
        blob.reload()
        print(f"2. GCS 객체 검증 성공:")
        print(f"   - Blob 이름: {blob.name}")
        print(f"   - Content-Type: {blob.content_type} (기대값: audio/wav)")
        print(f"   - 크기: {blob.size} bytes")
        assert blob.content_type == "audio/wav", "Content-Type이 audio/wav가 아님"

        # 4. 즉시 삭제 (0-Day Retention) 검증
        print("3. GCSStorageService.delete_temp_audio() 즉시 삭제 실행...")
        del_result = GCSStorageService.delete_temp_audio(gcs_uri)
        assert del_result is True, "삭제 결과가 True가 아님"
        
        # 5. 삭제 확인 검증
        assert not blob.exists(), "삭제 후에도 Blob이 여전히 존재함"
        print("   ✅ GCS 객체 즉시 삭제 확인 완료 (Zero Data Retention 검증 통과)")
        print(">>> [테스트 2 성공] GCS 스토리지 보안 및 라이프사이클 검증 완료!\n")

    finally:
        if os.path.exists(dummy_file):
            os.remove(dummy_file)

if __name__ == "__main__":
    test_gcs_storage()
