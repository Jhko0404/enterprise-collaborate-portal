import os
import subprocess
import logging

os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"

logger = logging.getLogger("collaborate-portal")

def get_google_credentials():
    """
    Cloud Run 및 로컬 개발 환경 모두에서 안전하게 GCP 인증 자격을 획득하는 헬퍼 함수
    1. Cloud Run 환경 (K_SERVICE 환경변수 존재): ADC(google.auth.default) 즉시 반환 (0ms)
    2. 로컬 환경: ADC 시도 후 필요 시 gcloud 활성 세션 토큰 폴백
    """
    # 1. Cloud Run / Google Cloud 서버리스 환경: 표준 ADC 즉시 반환 (서브프로세스 호출 절대 금지)
    if os.environ.get("K_SERVICE") or os.environ.get("K_REVISION") or os.environ.get("GAE_INSTANCE"):
        try:
            import google.auth
            creds, _ = google.auth.default()
            return creds
        except Exception:
            return None

    # 2. 로컬 개발 환경: 표준 ADC 우선 확인
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            import google.auth
            creds, _ = google.auth.default()
            return creds
        except Exception:
            pass

    # 3. gcloud CLI 세션 토큰 폴백 (타임아웃 1초)
    try:
        import shutil
        if shutil.which("gcloud"):
            token_out = subprocess.check_output(
                ["gcloud", "auth", "print-access-token"],
                stderr=subprocess.DEVNULL,
                timeout=1
            ).decode("utf-8").strip()
            if token_out:
                from google.oauth2 import credentials
                return credentials.Credentials(token_out)
    except Exception:
        pass

    try:
        import google.auth
        creds, _ = google.auth.default()
        return creds
    except Exception as e:
        logger.warning(f"GCP 인증 자격 획득 실패: {e}")
        return None
