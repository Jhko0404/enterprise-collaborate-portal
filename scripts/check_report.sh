#!/bin/bash
# 회의록 및 STT 진행 상황 진단 래퍼 스크립트
# 사용법: ./scripts/check_report.sh [검색어 또는 리포트ID]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

"$PYTHON_BIN" "$SCRIPT_DIR/check_report_stt_progress.py" "$@"
