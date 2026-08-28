#!/usr/bin/env bash
# ==============================================================================
# 🚀 Enterprise AI Collaborate Portal - 원클릭 통합 배포 스크립트 (Quickstart)
# ==============================================================================
# 이 스크립트는 프로젝트 설정, 필수 API 활성화, GCS 버킷 생성, Cloud Run 백엔드 배포,
# API Gateway 연동까지 모든 과정을 한 번에 자동으로 완료합니다.
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

# 1. 환경 설정 감지
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -d '\n')
fi

PROJECT_ID="${1:-${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}}"
REGION="${2:-${GCP_REGION:-us-central1}}"
SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-enterprise-meet-notes-service}"
BUCKET_NAME="${TEMP_GCS_BUCKET:-${PROJECT_ID}-meet-audio-temp}"
API_ID="${GCP_API_ID:-enterprise-agent-api}"
GATEWAY_ID="${GCP_GATEWAY_ID:-enterprise-agent-gateway}"
GATEWAY_SA="agent-gateway-sa@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/cloud-run-source-deploy/${SERVICE_NAME}:latest"

echo "=================================================================="
echo "🌟 [Enterprise AI 협업포털] 원클릭 통합 배포 시작"
echo "=================================================================="
echo "📌 프로젝트 ID : ${PROJECT_ID}"
echo "📍 리전        : ${REGION}"
echo "📦 Cloud Run   : ${SERVICE_NAME}"
echo "🚪 Gateway     : ${GATEWAY_ID}"
echo "☁️ 임시 버킷   : gs://${BUCKET_NAME}"
echo "=================================================================="

if [ -z "${PROJECT_ID}" ] || [ "${PROJECT_ID}" == "(unset)" ]; then
  echo "❌ GCP 프로젝트 ID가 설정되지 않았습니다."
  echo "사용법: ./deploy/quickstart.sh [GCP_PROJECT_ID] [REGION]"
  echo "또는 .env 파일에 GCP_PROJECT_ID를 작성해 주세요."
  exit 1
fi

# 2. 필수 Google Cloud API 활성화
echo "🔌 1/5. 필수 Google Cloud API 활성화 중..."
gcloud services enable \
  run.googleapis.com \
  apigateway.googleapis.com \
  servicemanagement.googleapis.com \
  servicecontrol.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  speech.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}"

# 3. GCS 임시 미디어 버킷 생성 (존재하지 않을 경우)
echo "🪣 2/5. 임시 GCS 미디어 버킷 확인 및 생성..."
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "  버킷 신규 생성: gs://${BUCKET_NAME}"
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi

# 4. Cloud Run 백엔드 컨테이너 빌드 및 배포
echo "🔨 3/5. Cloud Build 컨테이너 빌드 및 Cloud Run 비공개 배포 중..."
cp deploy/Dockerfile ./Dockerfile
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --tag="${IMAGE_NAME}" .

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

BACKEND_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format="value(status.url)")

echo "  Cloud Run 내부 URL: ${BACKEND_URL}"

# 5. API Gateway 전용 서비스 계정 및 IAM 바인딩
echo "👤 4/5. API Gateway 서비스 계정 및 Invoker IAM 설정 중..."
if ! gcloud iam service-accounts describe "${GATEWAY_SA}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create agent-gateway-sa \
    --display-name="Agent Gateway Ingress Service Account" \
    --project="${PROJECT_ID}"
fi

gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${GATEWAY_SA}" \
  --role="roles/run.invoker"

# 6. API Gateway 배포 및 라우팅 바인딩
echo "🚪 5/5. Google Cloud API Gateway 생성 및 라우팅 연동 중..."
CONFIG_ID="ent-cfg-$(date +%Y%m%d%H%M%S)"
TEMP_OPENAPI_SPEC="/tmp/openapi2-agentgateway-resolved.yaml"
sed "s|\${BACKEND_CLOUD_RUN_URL}|${BACKEND_URL}|g" deploy/openapi2-agentgateway.yaml > "${TEMP_OPENAPI_SPEC}"

if ! gcloud api-gateway apis describe "${API_ID}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud api-gateway apis create "${API_ID}" \
    --project="${PROJECT_ID}" \
    --display-name="Enterprise Collaborate Portal Agent API"
fi

gcloud api-gateway api-configs create "${CONFIG_ID}" \
  --api="${API_ID}" \
  --openapi-spec="${TEMP_OPENAPI_SPEC}" \
  --project="${PROJECT_ID}" \
  --backend-auth-service-account="${GATEWAY_SA}"

if ! gcloud api-gateway gateways describe "${GATEWAY_ID}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud api-gateway gateways create "${GATEWAY_ID}" \
    --api="${API_ID}" \
    --api-config="${CONFIG_ID}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}"
else
  gcloud api-gateway gateways update "${GATEWAY_ID}" \
    --api="${API_ID}" \
    --api-config="${CONFIG_ID}" \
    --location="${REGION}" \
    --project="${PROJECT_ID}"
fi

GATEWAY_URL=$(gcloud api-gateway gateways describe "${GATEWAY_ID}" \
  --location="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(defaultHostname)")

echo ""
echo "=================================================================="
echo "🎉 [Coway AI 협업포털 배포 완료!]"
echo "=================================================================="
echo "🌐 서비스 접속 URL : https://${GATEWAY_URL}"
echo "📍 Cloud Run 백엔드: 비공개 보호 완료 (Zero-Trust IAM 연동)"
echo "💡 브라우저에서 위 URL로 접속하여 바로 AI 회의록 분석을 시작하세요!"
echo "=================================================================="
