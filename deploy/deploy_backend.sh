#!/usr/bin/env bash
# ==============================================================================
# 1. Cloud Run 백엔드 빌드 및 배포 스크립트 (Zero-Trust 프라이빗 백엔드)
# ==============================================================================

set -e

# 0. 프로젝트 및 환경 설정 감지
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -d '\n')
fi

PROJECT_ID="${1:-${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}}"
REGION="${2:-${GCP_REGION:-us-central1}}"
SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-enterprise-meet-notes-service}"
BUCKET_NAME="${TEMP_GCS_BUCKET:-${PROJECT_ID}-meet-audio-temp}"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest"

if [ -z "${PROJECT_ID}" ]; then
  echo "❌ GCP 프로젝트 ID를 찾을 수 없습니다. 인자로 전달하거나 (.env / gcloud config) 설정하세요."
  echo "사용법: ./deploy/deploy_backend.sh [PROJECT_ID] [REGION]"
  exit 1
fi

echo "=================================================================="
echo "🚀 [1단계] Cloud Run 백엔드 빌드 및 배포"
echo "=================================================================="
echo "📌 프로젝트 ID : ${PROJECT_ID}"
echo "📍 리전        : ${REGION}"
echo "📦 서비스명    : ${SERVICE_NAME}"
echo "☁️ 임시 버킷   : gs://${BUCKET_NAME}"
echo "------------------------------------------------------------------"

# 1. 임시 미디어 GCS 버킷 (기존 버킷 사용)
echo "🪣 1. 임시 GCS 오디오 버킷: gs://${BUCKET_NAME}"

# 2. Cloud Build 컨테이너 빌드
echo "🔨 2. Cloud Build 컨테이너 이미지 빌드 중..."
cp deploy/Dockerfile ./Dockerfile
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --tag="${IMAGE_NAME}" .

# 3. Cloud Run 배포 (미인증 접근 차단: --no-allow-unauthenticated & 고동시성 자동 스케일아웃)
echo "☁️ 3. Cloud Run 배포 진행 중 (고동시성 멀티 인스턴스 자동 스케일링 설정)..."
gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --image="${IMAGE_NAME}" \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --cpu-boost \
  --execution-environment=gen2 \
  --timeout=600 \
  --concurrency=20 \
  --min-instances=1 \
  --max-instances=20 \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=global,GEMINI_MODEL_NAME=gemini-3.7-flash,TEMP_GCS_BUCKET=${BUCKET_NAME}"


# 3. 백엔드 URL 추출
BACKEND_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format="value(status.url)")

echo "------------------------------------------------------------------"
echo "✅ Cloud Run 백엔드 배포 완료!"
echo "🌐 내부 백엔드 URL: ${BACKEND_URL}"
echo "🔒 미인증 접근 상태: 차단됨 (--no-allow-unauthenticated)"
echo "------------------------------------------------------------------"
