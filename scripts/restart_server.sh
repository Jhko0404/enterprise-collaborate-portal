#!/usr/bin/env bash
# ==============================================================================
# 코웨이 AI 협업포털 서버 재기동 스크립트 (restart_server.sh)
# ==============================================================================
# 기능:
# 1. 9090 포트 및 기존 uvicorn 프로세스 감지
# 2. 기존 프로세스 안전 종료 (SIGTERM -> SIGKILL)
# 3. 가상환경(.venv) 확인 및 최신 uvicorn 서버 실행
# ==============================================================================

set -e

# 스크립트 위치 기준 프로젝트 루트 경로 계산
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

export GOOGLE_API_USE_CLIENT_CERTIFICATE=false
export GOOGLE_API_USE_MTLS_ENDPOINT=never

PORT=9090
HOST="0.0.0.0"

echo "=================================================================="
echo "🔄 [서버 재기동] 코웨이 AI 협업포털 백엔드 서버"
echo "=================================================================="
echo "📁 프로젝트 루트: ${PROJECT_ROOT}"
echo "🌐 바인딩 주소  : http://${HOST}:${PORT}"
echo "------------------------------------------------------------------"

# 1. 기존 실행 중인 프로세스 탐색 (포트 9090 또는 uvicorn app.main:app)
echo "🔍 1. 기존 실행 중인 서버 프로세스 확인 중..."
PIDS=$(pgrep -f "uvicorn app.main:app" || true)

# lsof / fuser로 포트 점유 프로세스 추가 확인
PORT_PIDS=$(lsof -ti :${PORT} 2>/dev/null || true)
ALL_PIDS=$(echo -e "${PIDS}\n${PORT_PIDS}" | sed '/^$/d' | sort -u)

if [ -n "${ALL_PIDS}" ]; then
    echo "⚠️  기존 실행 중인 프로세스 발견 (PID: $(echo ${ALL_PIDS} | tr '\n' ' '))"
    echo "🛑 2. 프로세스 종료 진행 중..."
    
    # 1차 부드러운 종료 (SIGTERM)
    for PID in ${ALL_PIDS}; do
        if kill -0 "${PID}" 2>/dev/null; then
            kill -15 "${PID}" 2>/dev/null || true
        fi
    done
    sleep 1.5

    # 2차 강제 종료 (SIGKILL) - 미종료 프로세스 대상
    for PID in ${ALL_PIDS}; do
        if kill -0 "${PID}" 2>/dev/null; then
            echo "   강제 종료(SIGKILL) 적용: PID ${PID}"
            kill -9 "${PID}" 2>/dev/null || true
        fi
    done
    sleep 0.5
    echo "   ✅ 기존 프로세스 종료 완료."
else
    echo "ℹ️  실행 중인 기존 프로세스가 없습니다."
fi

# 2. 가상환경(.venv) 확인
echo "------------------------------------------------------------------"
echo "📦 3. 파이썬 가상환경(.venv) 검증..."
if [ -f "${PROJECT_ROOT}/.venv/bin/python" ]; then
    PYTHON_BIN="${PROJECT_ROOT}/.venv/bin/python"
    echo "   ✅ 가상환경 파이썬 확인: ${PYTHON_BIN}"
else
    echo "   ⚠️ .venv 가상환경이 없습니다. 시스템 python3을 사용합니다."
    PYTHON_BIN="python3"
fi

# 3. 서버 실행 모드 분기 (백그라운드 vs 포그라운드)
echo "------------------------------------------------------------------"
if [ "$1" == "--bg" ] || [ "$1" == "--daemon" ]; then
    echo "🚀 4. 백그라운드 데몬 모드로 서버를 시작합니다..."
    setsid "${PYTHON_BIN}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" </dev/null > /tmp/collaborate_portal_uvicorn.log 2>&1 &
    sleep 2
    
    if pgrep -f "uvicorn app.main:app" > /dev/null; then
        echo "   ✅ 서버가 백그라운드에서 정상 실행 중입니다!"
        echo "   📄 실시간 로그 확인: tail -f /tmp/collaborate_portal_uvicorn.log"
        echo "   🌐 웹 브라우저 접속: http://${HOST}:${PORT}"
    else
        echo "   ❌ 서버 시작 실패. 로그를 확인하세요: cat /tmp/collaborate_portal_uvicorn.log"
        exit 1
    fi
else
    echo "🚀 4. 포그라운드 모드로 서버를 시작합니다. (종료: Ctrl + C)"
    echo "=================================================================="
    exec "${PYTHON_BIN}" -m uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
fi
