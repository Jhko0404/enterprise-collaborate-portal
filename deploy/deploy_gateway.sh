#!/usr/bin/env bash
# ==============================================================================
# 2. Google Cloud API Gateway (Agent Gateway) 배포 및 라우팅 스크립트
# ==============================================================================

set -e

# 0. 프로젝트 및 환경 설정 감지
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs -d '\n')
fi

PROJECT_ID="${1:-${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}}"
REGION="${2:-${GCP_REGION:-us-central1}}"
API_ID="${GCP_API_ID:-enterprise-agent-api}"
GATEWAY_ID="${GCP_GATEWAY_ID:-enterprise-agent-gateway}"
SERVICE_NAME="${CLOUD_RUN_SERVICE_NAME:-enterprise-meet-notes-service}"
CONFIG_ID="ent-cfg-$(date +%Y%m%d%H%M%S)"
GATEWAY_SA="agent-gateway-sa@${PROJECT_ID}.iam.gserviceaccount.com"

if [ -z "${PROJECT_ID}" ]; then
  echo "❌ GCP 프로젝트 ID를 찾을 수 없습니다. 인자로 전달하거나 (.env / gcloud config) 설정하세요."
  echo "사용법: ./deploy/deploy_gateway.sh [PROJECT_ID] [REGION]"
  exit 1
fi

echo "=================================================================="
echo "🛡️ [2단계] Google Cloud Agent Gateway 배포 및 연동"
echo "=================================================================="
echo "📌 프로젝트 ID : ${PROJECT_ID}"
echo "📍 리전        : ${REGION}"
echo "🚪 게이트웨이  : ${GATEWAY_ID}"
echo "🔑 서비스 계정 : ${GATEWAY_SA}"
echo "------------------------------------------------------------------"

# 1. 필수 GCP API 활성화
echo "🔌 1. 필수 GCP API 활성화 중..."
gcloud services enable \
  apigateway.googleapis.com \
  servicemanagement.googleapis.com \
  servicecontrol.googleapis.com \
  run.googleapis.com \
  --project="${PROJECT_ID}"

# 2. API Gateway 전용 서비스 계정 생성 및 권한 부여
echo "👤 2. API Gateway 전용 서비스 계정 확인 및 생성..."
if ! gcloud iam service-accounts describe "${GATEWAY_SA}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud iam service-accounts create agent-gateway-sa \
    --display-name="Agent Gateway Ingress Service Account" \
    --project="${PROJECT_ID}"
fi

# Cloud Run Invoker 권한 부여 (Zero-Trust 백엔드 호출용)
echo "🔒 3. Cloud Run 백엔드 Invoker IAM 권한 부여 중..."
gcloud run services add-iam-policy-binding "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --member="serviceAccount:${GATEWAY_SA}" \
  --role="roles/run.invoker"

# 3. 백엔드 URL 획득 및 OpenAPI 스펙 치환
BACKEND_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format="value(status.url)")

if [ -z "${BACKEND_URL}" ]; then
  echo "❌ Cloud Run 백엔드(${SERVICE_NAME}) URL을 찾을 수 없습니다. 1단계를 먼저 실행하세요."
  exit 1
fi

echo "🌐 백엔드 Cloud Run URL: ${BACKEND_URL}"
TEMP_OPENAPI_SPEC="/tmp/openapi2-agentgateway-resolved.yaml"
sed "s|\${BACKEND_CLOUD_RUN_URL}|${BACKEND_URL}|g" deploy/openapi2-agentgateway.yaml > "${TEMP_OPENAPI_SPEC}"

# 4. API 리소스 생성 (존재하지 않을 경우)
echo "📑 4. API Gateway API 리소스 생성..."
if ! gcloud api-gateway apis describe "${API_ID}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud api-gateway apis create "${API_ID}" \
    --project="${PROJECT_ID}" \
    --display-name="Enterprise Collaborate Portal Agent API"
fi

# 5. API Config 생성
echo "⚙️ 5. 새 API Config 생성 중 (${CONFIG_ID})..."
gcloud api-gateway api-configs create "${CONFIG_ID}" \
  --api="${API_ID}" \
  --openapi-spec="${TEMP_OPENAPI_SPEC}" \
  --project="${PROJECT_ID}" \
  --backend-auth-service-account="${GATEWAY_SA}"

# 6. Gateway 생성 또는 업데이트
echo "🚀 6. API Gateway 배포 및 바인딩 중..."
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

# 7. 배포된 공개 Gateway URL 조회
GATEWAY_URL=$(gcloud api-gateway gateways describe "${GATEWAY_ID}" \
  --location="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(defaultHostname)")

echo "=================================================================="
echo "🎉 [Agent Gateway 배포 완료]"
echo "=================================================================="
echo "🌐 공용 접속 Gateway URL: https://${GATEWAY_URL}"
echo "📍 GCP 콘솔 확인 경로: APIs & Services ➔ API Gateway ➔ ${GATEWAY_ID}"
echo "🔒 백엔드 보호: Cloud Run은 완전히 비공개이며, 게이트웨이 OIDC를 통해서만 안전하게 접근 가능합니다."
echo "=================================================================="
