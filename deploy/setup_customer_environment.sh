#!/usr/bin/env bash
# ==============================================================================
# Enterprise Collaborate Portal: 고객 환경 원클릭 자동 셋업 및 초기화 스크립트
# ==============================================================================

set -e

echo "=================================================================="
echo "🚀 [Enterprise AI Meeting Notes] 고객사 환경 초기 설정"
echo "=================================================================="

# 1. GCP 프로젝트 ID 입력 또는 환경변수 감지
PROJECT_ID="${1:-${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}}"
REGION="${2:-${GCP_REGION:-us-central1}}"

if [ -z "${PROJECT_ID}" ]; then
  read -p "📌 GCP 프로젝트 ID를 입력하세요: " PROJECT_ID
fi

if [ -z "${PROJECT_ID}" ]; then
  echo "❌ GCP 프로젝트 ID가 필요합니다."
  exit 1
fi

BUCKET_NAME="${PROJECT_ID}-meet-audio-temp"

echo "📌 Target Project : ${PROJECT_ID}"
echo "📍 Target Region  : ${REGION}"
echo "🪣 Target Bucket  : gs://${BUCKET_NAME}"
echo "------------------------------------------------------------------"

# 2. 필수 GCP API 활성화
echo "🔌 1. 필수 Google Cloud API 활성화 중..."
gcloud services enable \
  run.googleapis.com \
  apigateway.googleapis.com \
  servicemanagement.googleapis.com \
  servicecontrol.googleapis.com \
  aiplatform.googleapis.com \
  speech.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  --project="${PROJECT_ID}"

# 3. GCS 임시 버킷 생성 및 1일 수명주기(Lifecycle) 설정 (Zero Retention)
echo "🪣 2. GCS 오디오 임시 버킷 확인 및 생성..."
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
  
  # 1일 자동 삭제 수명주기 설정
  cat << 'LIFECYCLE_EOF' > /tmp/gcs_lifecycle_rule.json
{
  "rule": [
    {
      "action": {"type": "Delete"},
      "condition": {"age": 1}
    }
  ]
}
LIFECYCLE_EOF
  gcloud storage buckets update "gs://${BUCKET_NAME}" --lifecycle-file=/tmp/gcs_lifecycle_rule.json
  rm -f /tmp/gcs_lifecycle_rule.json
  echo "   ✅ GCS 버킷 생성 및 1일 자동 파기 수명주기 적용 완료"
fi

# 4. .env 파일 생성
echo "📝 3. .env 환경설정 파일 자동 생성..."
cat << ENV_EOF > .env
GCP_PROJECT_ID=${PROJECT_ID}
GCP_LOCATION=global
TEMP_GCS_BUCKET=${BUCKET_NAME}
GEMINI_MODEL_NAME=gemini-3.7-flash
LOCAL_API_SERVER_URL=http://localhost:9090
ENV_EOF

echo "=================================================================="
echo "🎉 [환경 초기화 완료] 이제 아래 명령어로 즉시 배포할 수 있습니다:"
echo "   1) Cloud Run 배포     : ./deploy/deploy_backend.sh ${PROJECT_ID} ${REGION}"
echo "   2) API Gateway 배포   : ./deploy/deploy_gateway.sh ${PROJECT_ID} ${REGION}"
echo "=================================================================="
