# ==============================================================================
# Enterprise AI 협업포털 Cloud Run 프로덕션 Dockerfile
# ==============================================================================

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# 1. 필수 시스템 패키지 및 ffmpeg 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. 파이썬 의존성 패키지 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. 소스 코드 및 정적 자산 복사
COPY app/ app/
COPY static/ static/
COPY data/ data/
COPY run_server.sh .
COPY scripts/ scripts/

# 4. 권한 및 템플릿 디렉토리 생성
RUN mkdir -p data/outputs/notes data/outputs/transcripts data/templates data/input_media && \
    chmod -R 755 /app

EXPOSE 8080

# 5. Cloud Run 엔트리포인트 실행 (멀티 프로세스 워커 및 비동기 처리 최적화)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2", "--limit-concurrency", "50"]

