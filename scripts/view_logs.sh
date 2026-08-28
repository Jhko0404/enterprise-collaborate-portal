#!/usr/bin/env bash
# ==============================================================================
# 리테일 회사 AI 협업포털 - 실시간 통합 로그 및 에러 분석 도구 (Log Diagnostics CLI)
# ==============================================================================

set -e

PROJECT_ID="project-elevate-007"
REGION="us-central1"
SERVICE_NAME="coway-meet-notes-service"
LOCAL_LOG_PATH="/tmp/collaborate_portal_app.log"
UVICORN_LOG_PATH="/tmp/collaborate_portal_uvicorn.log"

MODE="${1:---help}"

show_help() {
  echo "=================================================================="
  echo "🔍 [리테일 회사 AI 협업포털] 실시간 로그 & 오류 진단 CLI"
  echo "=================================================================="
  echo "사용법: ./scripts/view_logs.sh [옵션]"
  echo ""
  echo "옵션:"
  echo "  --local        : 로컬 서버 전체 실시간 로그 스트리밍 (tail -f)"
  echo "  --local-errors : 로컬 서버 오류(ERROR/WARN)만 실시간 필터링"
  echo "  --cloud        : Cloud Run 프로덕션 전체 실시간 로그 스트리밍"
  echo "  --cloud-errors : Cloud Run 오류(ERROR/WARN/CRITICAL)만 필터링 조회"
  echo "  --api          : 백엔드 진단 REST API에서 최근 구조화 에러 로그 JSON 조회"
  echo "  --help         : 사용법 안내"
  echo "=================================================================="
}

case "${MODE}" in
  --local)
    echo "📄 [로컬 로그 스트리밍] ${LOCAL_LOG_PATH} ..."
    if [ -f "${LOCAL_LOG_PATH}" ]; then
      tail -n 50 -f "${LOCAL_LOG_PATH}"
    elif [ -f "${UVICORN_LOG_PATH}" ]; then
      tail -n 50 -f "${UVICORN_LOG_PATH}"
    else
      echo "⚠️ 로컬 로그 파일이 아직 생성되지 않았습니다."
    fi
    ;;

  --local-errors)
    echo "🚨 [로컬 오류 로그 필터링] ERROR/WARNING 추적 중..."
    tail -n 200 -f "${LOCAL_LOG_PATH}" 2>/dev/null | grep --color=always -E "ERROR|CRITICAL|WARNING|Exception|Traceback|413|500|404"
    ;;

  --cloud)
    echo "☁️ [Cloud Run 실시간 로그 스트리밍] 서비스: ${SERVICE_NAME} (리전: ${REGION}) ..."
    gcloud beta run services logs tail "${SERVICE_NAME}" \
      --project="${PROJECT_ID}" \
      --region="${REGION}"
    ;;

  --cloud-errors)
    echo "🚨 [Cloud Run 최근 오류 로그 조회] 심각도: WARNING / ERROR / CRITICAL ..."
    gcloud logging read \
      "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND severity>=WARNING" \
      --project="${PROJECT_ID}" \
      --limit=30 \
      --format="table(timestamp,severity,textPayload,jsonPayload.message)"
    ;;

  --api)
    echo "🌐 [REST API 구조화 로그 조회] GET /api/v1/system/logs?level=ERROR ..."
    curl -s "http://localhost:9090/api/v1/system/logs?level=ERROR&limit=10" | python3 -m json.tool || \
    curl -s "https://coway-agent-gateway-7p7fk8nj.uc.gateway.dev/api/v1/system/logs?level=ERROR&limit=10" | python3 -m json.tool
    ;;

  *)
    show_help
    ;;
esac
