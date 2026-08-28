import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from collections import deque
from typing import List, Dict, Optional, Any

# Maximum log events to keep in the in-memory circular buffer
MAX_RING_BUFFER_SIZE = 500

class RingBufferLogHandler(logging.Handler):
    """
    실시간 웹 UI 및 진단 API에서 빠른 조회가 가능하도록
    최근 500개의 로그 이벤트를 메모리 링 버퍼에 구조화하여 보관하는 핸들러
    (collections.deque의 원자적 CPython 연산으로 완전 스레드 안전)
    """
    def __init__(self, capacity: int = MAX_RING_BUFFER_SIZE):
        super().__init__()
        self.buffer = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord):
        try:
            exc_text = None
            if record.exc_info:
                exc_text = self.formatException(record.exc_info)
            
            entry = {
                "id": f"log_{int(record.created * 1000)}_{int(record.msecs)}",
                "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "func": record.funcName,
                "line": record.lineno,
                "exception": exc_text
            }
            self.buffer.append(entry)
        except Exception:
            pass

    def get_logs(
        self,
        level: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        logs = list(self.buffer)
        logs.reverse()

        if level and level.upper() != "ALL":
            lvl_upper = level.upper()
            if lvl_upper == "ERROR":
                logs = [l for l in logs if l["level"] in ("ERROR", "CRITICAL")]
            elif lvl_upper == "WARN" or lvl_upper == "WARNING":
                logs = [l for l in logs if l["level"] in ("WARNING", "ERROR", "CRITICAL")]
            else:
                logs = [l for l in logs if l["level"] == lvl_upper]

        if search:
            s_lower = search.lower().strip()
            logs = [
                l for l in logs
                if s_lower in l["message"].lower() 
                or s_lower in l["logger"].lower() 
                or (l["exception"] and s_lower in l["exception"].lower())
            ]

        return logs[:limit]

    def clear(self):
        self.buffer.clear()

# Global ring handler instance
ring_handler = RingBufferLogHandler(MAX_RING_BUFFER_SIZE)

def setup_logging(log_dir: str = "logs", app_name: str = "collaborate-portal") -> logging.Logger:
    """
    통합 로깅 시스템 초기화:
    1. 콘솔 (stdout) - GCP Cloud Logging 및 터미널 출력
    2. 로테이팅 파일 (logs/app.log & /tmp/collaborate_portal_app.log)
    3. 인메모리 링 버퍼 (웹 진단 UI 및 REST API용)
    """
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs("/tmp", exist_ok=True)

    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(module)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)

    tmp_file_handler = RotatingFileHandler(
        "/tmp/collaborate_portal_app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    tmp_file_handler.setFormatter(log_format)
    tmp_file_handler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(tmp_file_handler)
        root_logger.addHandler(ring_handler)

    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(logging.DEBUG)

    return app_logger

logger = setup_logging()

def get_system_logs(level: Optional[str] = None, search: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    return ring_handler.get_logs(level=level, search=search, limit=limit)

def clear_system_logs():
    ring_handler.clear()
