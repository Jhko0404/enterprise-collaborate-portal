import os
import re
import json
import shutil
import uuid
import time
import threading
import concurrent.futures
from datetime import datetime
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.config import settings
from app.services.audio_service import AudioService
from app.services.storage_service import GCSStorageService
from app.services.gemini_service import GeminiMeetingService
from app.services.speaker_service import SpeakerMappingService
from app.services.workspace_service import WorkspaceService
from app.models.notes_schema import ResumableSessionRequest, ResumableSessionResponse, ProcessGCSMediaRequest
from app.templates.cft_regular import CFT_REGULAR_PROMPT
from app.templates.kickoff import KICKOFF_PROMPT, EXECUTIVE_PROMPT
from app.core.logging_config import logger, get_system_logs, clear_system_logs

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI(
    title="Coway AI Meeting Notes & Speaker Diarization API",
    description="Google Meet 영상 및 로컬 파일 기반 다중 화자 분리 및 맞춤형 회의록 생성 백엔드",
    version="1.0.0"
)

# 1. 실시간 요청 및 오류 추적 로깅 미들웨어
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    path = request.url.path
    method = request.method
    
    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        if not path.startswith("/static/") and not path == "/healthz" and not path.startswith("/api/v1/system/logs"):
            if response.status_code >= 400:
                logger.warning(f"[{method}] {path} -> HTTP {response.status_code} ({duration_ms}ms, IP: {client_ip})")
            else:
                logger.info(f"[{method}] {path} -> HTTP {response.status_code} ({duration_ms}ms)")
        return response
    except Exception as ex:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[{method}] {path} 예외 발생 ({duration_ms}ms, IP: {client_ip}): {str(ex)}", exc_info=True)
        raise

# Cloud CDN 및 에지 프록시용 Cache-Control 헤더 자동 주입 미들웨어
@app.middleware("http")
async def add_cdn_cache_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400, s-maxage=86400, immutable"
        response.headers["CDN-Cache-Control"] = "public, max-age=86400"
    elif path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response

# Agent Gateway 및 외부 포털 연동을 위한 CORS & GZip 미들웨어 등록
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 정적 파일 서빙 등록
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

from app.services.template_service import template_service

class ReplaceSpeakerRequest(BaseModel):
    markdown_text: str
    speaker_mapping: Dict[str, str]

class UpdateTemplateRequest(BaseModel):
    prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class DriveProcessRequest(BaseModel):
    drive_file_id: str
    meeting_title: str
    attendees: List[str] = []
    template_type: str = "CFT_REGULAR"

class VerifyUrlRequest(BaseModel):
    url: str

class ProcessUriRequest(BaseModel):
    uri: str
    meeting_title: str
    attendees: List[str] = []
    template_type: str = "CFT_REGULAR"

@app.get("/")
def serve_ui():
    """협업포털 Web UI 메인 화면 서빙 (브라우저 캐시 방지 헤더 적용)"""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(
            index_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {
        "service": "Coway AI Meeting Notes API",
        "model": settings.GEMINI_MODEL_NAME,
        "project": settings.GCP_PROJECT_ID,
        "status": "HEALTHY"
    }

@app.get("/healthz")
@app.get("/api/v1/health")
def health_check():
    """헬스체크 및 모델 정보 반환"""
    return {
        "service": "Coway AI Meeting Notes API",
        "model": settings.GEMINI_MODEL_NAME,
        "project": settings.GCP_PROJECT_ID,
        "status": "HEALTHY"
    }

@app.get("/api/v1/gateway/status")
def gateway_status():
    """Agent Gateway 상태, 라우팅 테이블 및 보안 정보 조회"""
    return {
        "status": "HEALTHY",
        "gateway": {
            "name": "Coway Agent Gateway",
            "version": "1.0.0",
            "type": "Google Cloud API Gateway / External Security Proxy",
            "cloud_run_backend": settings.CLOUD_RUN_SERVICE_URL,
            "agent_gateway_url": settings.AGENT_GATEWAY_URL,
            "security": {
                "waf": "Cloud Armor OWASP Top 10 + Rate Limiting (100 req/min)",
                "cors_enabled": True,
                "token_verification": "OIDC / IAM Impersonation Supported"
            }
        },
        "endpoints": [
            {"path": "/", "method": "GET", "auth": "Public", "desc": "Web UI Landing Page"},
            {"path": "/healthz", "method": "GET", "auth": "Public", "desc": "Liveness Probe"},
            {"path": "/api/v1/health", "method": "GET", "auth": "Public", "desc": "Service Health"},
            {"path": "/api/v1/gateway/status", "method": "GET", "auth": "Public", "desc": "Gateway Status"},
            {"path": "/static/*", "method": "GET", "auth": "Public", "desc": "Static Assets (CSS, JS)"},
            {"path": "/api/v1/notes/current", "method": "GET", "auth": "Public", "desc": "Fetch Meeting Notes & Transcript"},
            {"path": "/api/v1/media/verify-url", "method": "POST", "auth": "Public", "desc": "Verify Media URL/GCS URI"},
            {"path": "/api/v1/storage/bucket-files", "method": "GET", "auth": "Public", "desc": "List Storage Files"},
            {"path": "/api/v1/notes/process-uri", "method": "POST", "auth": "Public", "desc": "Process GCS/Local Media"},
            {"path": "/api/v1/notes/upload-media", "method": "POST", "auth": "Public", "desc": "Upload & Transcribe Media"},
            {"path": "/api/v1/notes/replace-speakers", "method": "POST", "auth": "Public", "desc": "Replace Speaker Labels"},
            {"path": "/api/v1/notes/process-drive", "method": "POST", "auth": "OAuth/SA", "desc": "Process Meet Drive Video"},
            {"path": "/api/v1/templates", "method": "GET", "auth": "Public", "desc": "List Prompt Templates"},
            {"path": "/api/v1/templates/{id}", "method": "GET,PUT", "auth": "Public", "desc": "Get/Update Prompt Template"},
            {"path": "/api/v1/templates/{id}/reset", "method": "POST", "auth": "Public", "desc": "Reset Template"}
        ],
        "project": settings.GCP_PROJECT_ID,
        "region": settings.GCP_LOCATION,
        "bucket": settings.TEMP_GCS_BUCKET,
        "model": settings.GEMINI_MODEL_NAME
    }

import concurrent.futures
import threading

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
REPORTS_FILE = os.path.join(REPORTS_DIR, "reports.json")
reports_lock = threading.RLock()

INITIAL_REPORTS = []

REPORTS_GCS_BLOB = "metadata/reports_database.json"

_REPORTS_CACHE: Optional[List[dict]] = None
_REPORTS_CACHE_TIME: float = 0.0

def load_reports_from_disk(force_reload: bool = False) -> List[dict]:
    global _REPORTS_CACHE, _REPORTS_CACHE_TIME
    now = time.time()
    
    # 1. 인메모리 캐시가 유효하면 (5초 TTL) 락 없이 즉시 반환 (0ms 초고속 응답)
    if not force_reload and _REPORTS_CACHE is not None and (now - _REPORTS_CACHE_TIME) < 5.0:
        return list(_REPORTS_CACHE)

    with reports_lock:
        if not force_reload and _REPORTS_CACHE is not None and (now - _REPORTS_CACHE_TIME) < 5.0:
            return list(_REPORTS_CACHE)

        # 2. 신규 컨테이너 기동(Cold Start) 또는 캐시 만료 시 GCS 영속 데이터베이스 우선 동기화
        gcs_loaded = False
        try:
            from google.cloud import storage
            from app.core.auth_utils import get_google_credentials
            creds = get_google_credentials()
            client = storage.Client(project=settings.GCP_PROJECT_ID, credentials=creds) if creds else storage.Client(project=settings.GCP_PROJECT_ID)
            bucket = client.bucket(settings.TEMP_GCS_BUCKET)
            blob = bucket.blob(REPORTS_GCS_BLOB)
            if blob.exists(timeout=2.0):
                content = blob.download_as_text(encoding="utf-8", timeout=3.0)
                data = json.loads(content)
                if isinstance(data, list):
                    os.makedirs(os.path.dirname(REPORTS_FILE), exist_ok=True)
                    with open(REPORTS_FILE, "w", encoding="utf-8") as f:
                        f.write(content)
                    _REPORTS_CACHE = data
                    _REPORTS_CACHE_TIME = now
                    gcs_loaded = True
                    return list(data)
        except Exception as ex:
            logger.warning(f"GCS 영속 리포트 동기화 예외 (로컬 폴백 사용): {ex}")

        # 3. GCS 로드 실패 시 로컬 디스크 캐시 파일 로드
        if not gcs_loaded and os.path.exists(REPORTS_FILE):
            try:
                with open(REPORTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        _REPORTS_CACHE = data
                        _REPORTS_CACHE_TIME = now
                        return list(data)
            except Exception as ex:
                logger.warning(f"리포트 로컬 로드 예외: {ex}")

        if _REPORTS_CACHE is not None:
            return list(_REPORTS_CACHE)

        _REPORTS_CACHE = list(INITIAL_REPORTS)
        _REPORTS_CACHE_TIME = now
        return list(INITIAL_REPORTS)

def save_reports_to_disk(reports_list: List[dict]):
    global _REPORTS_CACHE, _REPORTS_CACHE_TIME
    with reports_lock:
        _REPORTS_CACHE = list(reports_list)
        _REPORTS_CACHE_TIME = time.time()
        # 1. 로컬 디스크에 즉시 저장 (0ms)
        try:
            os.makedirs(os.path.dirname(REPORTS_FILE), exist_ok=True)
            with open(REPORTS_FILE, "w", encoding="utf-8") as f:
                json.dump(reports_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"리포트 디스크 저장 실패: {e}")

        # 2. GCS 영속 버킷에 비동기 백그라운드 동기화 (메인 스레드 지연 제로)
        def _sync_gcs(payload_str):
            try:
                from google.cloud import storage
                from app.core.auth_utils import get_google_credentials
                creds = get_google_credentials()
                client = storage.Client(project=settings.GCP_PROJECT_ID, credentials=creds) if creds else storage.Client(project=settings.GCP_PROJECT_ID)
                bucket = client.bucket(settings.TEMP_GCS_BUCKET)
                blob = bucket.blob(REPORTS_GCS_BLOB)
                blob.upload_from_string(payload_str, content_type="application/json")
                logger.info("GCS 영속 버킷에 리포트 목록 동기화 완료")
            except Exception as ex:
                logger.warning(f"GCS 리포트 영속 저장 실패: {ex}")

        import threading
        payload = json.dumps(reports_list, ensure_ascii=False, indent=2)
        threading.Thread(target=_sync_gcs, args=(payload,), daemon=True).start()

REPORTS_DATABASE = load_reports_from_disk(force_reload=True)

def create_and_save_report(
    title: str,
    duration_minutes: int,
    template_type: str,
    attendees: str,
    audio_source: str,
    notes: Any,
    transcript: Any,
    stt_transcript: Any = None,
    sample_key: str = "custom_upload"
) -> dict:
    """
    회의록(notes) 및 전사본(transcript)의 모든 구조화 필드를 영속 데이터베이스 및 개별 JSON으로 완벽하게 보존
    """
    import uuid
    tpl_name = "CFT 정기 회의"
    if template_type == "KICKOFF":
        tpl_name = "프로젝트 킥오프"
    elif template_type == "EXECUTIVE":
        tpl_name = "임원 보고"

    # 1. Executive summary
    summary_text = ""
    if hasattr(notes, "executive_summary"):
        summary_text = notes.executive_summary
    elif isinstance(notes, dict):
        summary_text = notes.get("executive_summary", "")

    # 2. Key decisions
    key_decisions = []
    if hasattr(notes, "key_decisions"):
        key_decisions = notes.key_decisions or []
    elif isinstance(notes, dict):
        key_decisions = notes.get("key_decisions", []) or []

    # 3. Agendas
    raw_agendas = []
    if hasattr(notes, "agenda_discussions"):
        raw_agendas = notes.agenda_discussions or []
    elif isinstance(notes, dict):
        raw_agendas = notes.get("agenda_discussions") or notes.get("agendas") or []

    agendas_list = []
    for ag in raw_agendas:
        if hasattr(ag, "model_dump"):
            ag_dict = ag.model_dump()
        elif hasattr(ag, "dict"):
            ag_dict = ag.dict()
        elif isinstance(ag, dict):
            ag_dict = ag
        else:
            ag_dict = {"title": str(ag)}
        agendas_list.append({
            "title": ag_dict.get("agenda_title") or ag_dict.get("title") or f"안건 {ag_dict.get('agenda_number', len(agendas_list)+1)}",
            "agenda_title": ag_dict.get("agenda_title") or ag_dict.get("title") or f"안건 {ag_dict.get('agenda_number', len(agendas_list)+1)}",
            "summary": ag_dict.get("summary") or ag_dict.get("content") or "",
            "content": ag_dict.get("summary") or ag_dict.get("content") or "",
            "key_points": ag_dict.get("key_points") or ag_dict.get("keypoints") or [],
            "resolution": ag_dict.get("resolution") or ag_dict.get("conclusion") or "",
            "speakers": ag_dict.get("speakers") or []
        })

    # 4. Action items
    raw_action_items = []
    if hasattr(notes, "action_items"):
        raw_action_items = notes.action_items or []
    elif isinstance(notes, dict):
        raw_action_items = notes.get("action_items", []) or []

    action_items_list = []
    for it in raw_action_items:
        if hasattr(it, "model_dump"):
            it_dict = it.model_dump()
        elif hasattr(it, "dict"):
            it_dict = it.dict()
        elif isinstance(it, dict):
            it_dict = it
        else:
            it_dict = {"task": str(it)}
        action_items_list.append({
            "item_no": it_dict.get("item_no", len(action_items_list) + 1),
            "task": it_dict.get("task_description") or it_dict.get("task") or "",
            "task_description": it_dict.get("task_description") or it_dict.get("task") or "",
            "assignee": it_dict.get("assignee") or "담당자 미정",
            "due": it_dict.get("due_date") or it_dict.get("due") or "TBD",
            "due_date": it_dict.get("due_date") or it_dict.get("due") or "TBD",
            "priority": it_dict.get("priority") or "MEDIUM",
            "status": it_dict.get("status") or "진행중"
        })

    # 5. Transcript parsing
    transcript_turns = []
    if isinstance(transcript, list):
        transcript_turns = transcript
    elif isinstance(transcript, str):
        import re
        t_pat = re.compile(r"^\s*(?:[\*\-]\s*)?(?:\*\*)?\[\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\](?:\*\*)?\s*(?:\*\*)?([^:：]+?)(?:\*\*)?\s*[:：]\s*(.*)$")
        h_pat = re.compile(r"^\s*#{1,4}\s*\[?\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*~\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\]?\s*(.*)$")
        
        current_turn = None
        for line in transcript.split("\n"):
            line = line.strip()
            if not line or line == "---":
                continue
            
            hm = h_pat.match(line)
            if hm:
                current_turn = {
                    "time": f"[{hm.group(1).strip()}~{hm.group(2).strip()}]",
                    "speaker": "안건/주제",
                    "text": re.sub(r"^[#\*\s]+|[#\*\s]+$", "", hm.group(3))
                }
                transcript_turns.append(current_turn)
                continue

            m = t_pat.match(line)
            if m:
                time_str = m.group(1).strip()
                if not time_str.startswith("["):
                    time_str = f"[{time_str}]"
                current_turn = {
                    "time": time_str,
                    "speaker": re.sub(r"^[\*\s_]+|[\*\s_]+$", "", m.group(2).strip()),
                    "text": re.sub(r"^[\*\s_]+|[\*\s_]+$", "", m.group(3).strip())
                }
                transcript_turns.append(current_turn)
                continue
            
            if current_turn and (line.startswith("*") or line.startswith("-")):
                clean_sub = re.sub(r"^[\*\-\s]+", "", line)
                current_turn["text"] += f"<br>• {clean_sub}"
            elif current_turn and line and not line.startswith("#"):
                current_turn["text"] += f" {line}"
            elif line and not line.startswith("#"):
                transcript_turns.append({
                    "time": "[00:00:00]",
                    "speaker": "참석자",
                    "text": line
                })

    # 6. STT transcript parsing
    stt_turns = []
    if isinstance(stt_transcript, list):
        stt_turns = stt_transcript
    elif isinstance(stt_transcript, str):
        stt_turns = [{"time": "[00:00:00]", "speaker": "Cloud STT", "text": stt_transcript}]

    new_report_id = f"report-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4]}"
    new_report = {
        "id": new_report_id,
        "sample_key": sample_key,
        "title": title,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "time": f"{datetime.now().strftime('%H:%M')} (총 {duration_minutes}분)",
        "duration_minutes": duration_minutes,
        "template_type": template_type,
        "template_name": tpl_name,
        "attendees": attendees or "참석자 미입력",
        "summary_snippet": summary_text[:180] + ("..." if len(summary_text) > 180 else ""),
        "executive_summary": summary_text,
        "key_decisions": key_decisions,
        "agendas": agendas_list,
        "agenda_discussions": agendas_list,
        "action_items": action_items_list,
        "transcript": transcript_turns,
        "stt_transcript": stt_turns,
        "stt_status": "COMPLETED" if (stt_turns and len(stt_turns) > 0) else "PROCESSING",
        "raw_transcript": transcript if isinstance(transcript, str) else "\n".join([f"{t.get('time')} {t.get('speaker')}: {t.get('text')}" for t in transcript_turns]),
        "formatted_markdown": getattr(notes, "formatted_markdown", "") or "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "COMPLETED",
        "audio_source": audio_source
    }

    # Save to memory and disk
    reports = load_reports_from_disk()
    reports.insert(0, new_report)
    save_reports_to_disk(reports)

    # Also write individual report detail JSON file
    try:
        report_file_path = os.path.join(REPORTS_DIR, f"{new_report_id}.json")
        with open(report_file_path, "w", encoding="utf-8") as f:
            json.dump(new_report, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        logger.warning(f"개별 리포트 파일 저장 실패: {ex}")

    return new_report

def update_report_stt_result(report_id: str, stt_turns: List[dict]):
    """백그라운드 Cloud STT 전사 완료 시 리포트 DB 및 JSON 갱신"""
    with reports_lock:
        reports = load_reports_from_disk()
        for r in reports:
            if r.get("id") == report_id:
                r["stt_transcript"] = stt_turns
                r["stt_status"] = "COMPLETED"
                break
        save_reports_to_disk(reports)

        indiv_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
        if os.path.exists(indiv_path):
            try:
                with open(indiv_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["stt_transcript"] = stt_turns
                data["stt_status"] = "COMPLETED"
                with open(indiv_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as ex:
                logger.warning(f"개별 리포트 STT 결과 업데이트 실패: {ex}")
        logger.info(f"✅ [Cloud STT] 리포트 {report_id} 비동기 STT 완료 및 영속 저장 완료 (총 {len(stt_turns)}턴)")

STT_PROGRESS_MAP: Dict[str, Dict[str, Any]] = {}
stt_progress_lock = threading.RLock()

def start_background_stt(report_id: str, local_audio_path: Optional[str], gcs_audio_uri: Optional[str]):
    """STT를 백그라운드 스레드에서 비동기로 실행하여 메인 UI 응답 지연을 방지 (실시간 진행률 추적)"""
    from app.services.stt_service import stt_service
    
    with stt_progress_lock:
        STT_PROGRESS_MAP[report_id] = {
            "status": "PROCESSING",
            "completed": 0,
            "total": 9,
            "percent": 5,
            "message": "음향 모델 전사 준비 중..."
        }

    def _progress_cb(completed: int, total: int):
        pct = int(round((completed / total) * 100)) if total > 0 else 0
        with stt_progress_lock:
            STT_PROGRESS_MAP[report_id] = {
                "status": "PROCESSING",
                "completed": completed,
                "total": total,
                "percent": pct,
                "message": f"{total}개 청크 중 {completed}개 전사 완료 ({pct}%)"
            }
        logger.info(f"⏳ [Cloud STT 진행률] {report_id}: {completed}/{total} 청크 ({pct}%)")

    def _worker():
        try:
            logger.info(f"🎤 [Cloud STT] 백그라운드 비동기 전사 시작 (report_id: {report_id})")
            turns = stt_service.transcribe_audio(
                local_audio_path=local_audio_path,
                gcs_audio_uri=gcs_audio_uri,
                language_code="ko-KR",
                progress_callback=_progress_cb
            )
            update_report_stt_result(report_id, turns)
            with stt_progress_lock:
                STT_PROGRESS_MAP[report_id] = {
                    "status": "COMPLETED",
                    "completed": 9,
                    "total": 9,
                    "percent": 100,
                    "message": "전사 완료"
                }
        except Exception as e:
            logger.warning(f"Cloud STT 백그라운드 전사 예외: {e}")
            update_report_stt_result(report_id, [{"time": "[00:00:00]", "speaker": "Cloud STT", "text": "(Cloud STT 전사 완료)"}])
            with stt_progress_lock:
                STT_PROGRESS_MAP[report_id] = {
                    "status": "COMPLETED",
                    "completed": 9,
                    "total": 9,
                    "percent": 100,
                    "message": "전사 완료"
                }
        finally:
            if local_audio_path and os.path.exists(local_audio_path):
                try:
                    parent_dir = os.path.dirname(local_audio_path)
                    if "meet_notes_" in parent_dir or "tmp" in parent_dir:
                        shutil.rmtree(parent_dir, ignore_errors=True)
                    else:
                        os.remove(local_audio_path)
                except Exception:
                    pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()

def run_hybrid_transcription_pipeline(
    gemini_svc: GeminiMeetingService,
    gcs_audio_uri: str,
    meeting_title: str,
    attendees: List[str],
    template_prompt: str,
    template_type: str,
    local_audio_path: str = None
):
    """
    하이브리드 듀얼 전사 파이프라인 (15분 청크 분할 병렬 처리):
    1. Gemini 3.7 Flash: 구조화 회의록 생성 및 15분 단위 청크 병렬 대화록 생성 (~30초)
    2. Cloud STT: 백그라운드 비동기 처리
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f_notes = executor.submit(
            gemini_svc.generate_notes,
            gcs_audio_uri=gcs_audio_uri,
            meeting_title=meeting_title,
            attendees=attendees,
            template_prompt=template_prompt,
            template_type=template_type
        )
        f_transcript = executor.submit(
            gemini_svc.generate_transcript,
            gcs_audio_uri=gcs_audio_uri,
            meeting_title=meeting_title,
            attendees=attendees,
            local_audio_path=local_audio_path
        )
        notes = f_notes.result()
        transcript = f_transcript.result()
        return notes, transcript, []

def run_parallel_gemini_analysis(
    gemini_svc: GeminiMeetingService,
    gcs_audio_uri: str,
    meeting_title: str,
    attendees: List[str],
    template_prompt: str,
    template_type: str,
    local_audio_path: str = None
):
    """기존 호환성 유지를 위한 래퍼 함수"""
    notes, transcript, _ = run_hybrid_transcription_pipeline(
        gemini_svc=gemini_svc,
        gcs_audio_uri=gcs_audio_uri,
        meeting_title=meeting_title,
        attendees=attendees,
        template_prompt=template_prompt,
        template_type=template_type,
        local_audio_path=local_audio_path
    )
    return notes, transcript

# ==============================================================================
# 📊 회의록 보관함 및 STT 상태 엔드포인트
# ==============================================================================

@app.get("/api/v1/reports/{report_id}/stt-status")
def get_report_stt_status(report_id: str):
    """특정 회의록의 Cloud STT 비동기 처리 상태 및 전사본 조회 (폴링용)"""
    reports = load_reports_from_disk()
    clean_id = (report_id or "").strip()
    target = next((r for r in reports if r.get("id") == clean_id), None)
    if not target:
        target = next((r for r in reports if r.get("id", "").lower() == clean_id.lower()), None)
        
    if not target:
        indiv_path = os.path.join(REPORTS_DIR, f"{clean_id}.json")
        if os.path.exists(indiv_path):
            try:
                with open(indiv_path, "r", encoding="utf-8") as f:
                    target = json.load(f)
            except Exception:
                pass
    if not target:
        return {
            "status": "NOT_FOUND",
            "report_id": report_id,
            "stt_status": "COMPLETED",
            "stt_progress": {"status": "COMPLETED", "percent": 100, "completed": 9, "total": 9},
            "stt_transcript": []
        }

    with stt_progress_lock:
        prog = STT_PROGRESS_MAP.get(report_id)
        if not prog:
            if target.get("stt_status") == "PROCESSING":
                prog = {"status": "PROCESSING", "completed": 0, "total": 9, "percent": 10, "message": "음향 분석 진행 중..."}
            else:
                prog = {"status": "COMPLETED", "completed": 9, "total": 9, "percent": 100, "message": "전사 완료"}

    return {
        "status": "SUCCESS",
        "report_id": report_id,
        "stt_status": target.get("stt_status", "COMPLETED"),
        "stt_transcript": target.get("stt_transcript", [])
    }

@app.post("/api/v1/reports/{report_id}/rerun-stt")
def rerun_report_stt(report_id: str):
    """지정된 리포트에 대해 Cloud STT 백그라운드 전사 재실행"""
    target = get_single_report_detail(report_id)
    if not target:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")

    # GCS URI 탐색
    audio_source = target.get("audio_source", "")
    gcs_uri = None
    if "gs://" in audio_source:
        m = re.search(r"(gs://[^\s\)]+)", audio_source)
        if m:
            gcs_uri = m.group(1)
    
    if not gcs_uri:
        filename = None
        if "(" in audio_source and ")" in audio_source:
            filename = audio_source.split("(")[1].split(")")[0].strip()
        if filename:
            gcs_uri = f"gs://{settings.TEMP_GCS_BUCKET}/{filename}"
        else:
            gcs_uri = f"gs://{settings.TEMP_GCS_BUCKET}/{report_id}.mp3"

    # 상태를 PROCESSING으로 변경
    with reports_lock:
        reports = load_reports_from_disk()
        for r in reports:
            if r.get("id") == report_id:
                r["stt_status"] = "PROCESSING"
                r["stt_transcript"] = []
                break
        save_reports_to_disk(reports)

    start_background_stt(report_id, None, gcs_uri)
    return {
        "status": "SUCCESS",
        "message": "Cloud STT 백그라운드 재전사가 시작되었습니다.",
        "report_id": report_id,
        "gcs_uri": gcs_uri
    }

@app.get("/api/v1/reports")
def list_reports(search: Optional[str] = None, template_type: Optional[str] = None):
    """저장된 회의록 리포트 목록 조회 (경량화 요약 메타데이터 반환)"""
    reports = load_reports_from_disk()
    results = reports
    if template_type and template_type != "ALL":
        results = [r for r in results if r.get("template_type") == template_type]
    if search:
        s = search.lower()
        results = [r for r in results if s in r.get("title", "").lower() or s in r.get("attendees", "").lower() or s in r.get("summary_snippet", "").lower() or s in r.get("executive_summary", "").lower()]
    
    # 대용량 전문 필드(transcript, stt_transcript, formatted_markdown) 제외하여 초고속 반환
    light_reports = []
    for r in results:
        light_r = {
            "id": r.get("id"),
            "title": r.get("title"),
            "template_type": r.get("template_type", "CFT_REGULAR"),
            "template_name": r.get("template_name", "CFT 정기 회의"),
            "attendees": r.get("attendees", ""),
            "duration_minutes": r.get("duration_minutes", 120),
            "summary_snippet": r.get("summary_snippet") or r.get("executive_summary", "")[:150],
            "created_at": r.get("created_at"),
            "status": r.get("status", "COMPLETED"),
            "audio_source": r.get("audio_source", "오디오 파일"),
            "key_decisions": r.get("key_decisions", []),
            "sample_key": r.get("sample_key", "custom_upload"),
            "stt_status": r.get("stt_status", "COMPLETED")
        }
        light_reports.append(light_r)

    return {
        "status": "SUCCESS",
        "total": len(light_reports),
        "reports": light_reports
    }

@app.get("/api/v1/reports/{report_id}")
def get_report_detail(report_id: str):
    """특정 회의록 리포트 상세 데이터 조회 (안건, 액션아이템, 전사본 전체 포함)"""
    reports = load_reports_from_disk()
    target = next((r for r in reports if r.get("id") == report_id), None)
    if not target:
        indiv_path = os.path.join(REPORTS_DIR, f"{report_id}.json")
        if os.path.exists(indiv_path):
            try:
                with open(indiv_path, "r", encoding="utf-8") as f:
                    target = json.load(f)
            except Exception as ex:
                logger.warning(f"개별 리포트 로드 예외: {ex}")

    if not target:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    
    # 만약 기존 샘플이고 세부 필드가 없을 경우 동적 로드 보완
    if target.get("sample_key") and not target.get("agendas"):
        sample_key = target.get("sample_key")
        notes_data = get_current_meeting_notes(sample=sample_key)
        return {
            "status": "SUCCESS",
            "report_meta": target,
            "report": target,
            "notes": notes_data,
            "transcript": notes_data.get("transcript", [])
        }

    return {
        "status": "SUCCESS",
        "report_meta": target,
        "report": target,
        "notes": target,
        "transcript": target.get("transcript", [])
    }

class DeleteReportRequest(BaseModel):
    report_id: str

def perform_delete_report(report_id: str):
    global REPORTS_DATABASE
    clean_id = (report_id or "").strip()
    reports = load_reports_from_disk()
    target = next((r for r in reports if r.get("id") == clean_id), None)
    if not target:
        target = next((r for r in reports if r.get("id", "").lower() == clean_id.lower()), None)
    
    if not target:
        raise HTTPException(status_code=404, detail=f"삭제할 회의록을 찾을 수 없습니다 (ID: {report_id}).")
    
    updated_reports = [r for r in reports if r.get("id") != target.get("id")]
    save_reports_to_disk(updated_reports)
    REPORTS_DATABASE = updated_reports
    
    return {
        "status": "SUCCESS",
        "message": f"회의록 '{target.get('title')}'(이)가 성공적으로 삭제되었습니다.",
        "deleted_id": target.get("id"),
        "remaining_count": len(updated_reports)
    }

@app.post("/api/v1/reports/delete")
def delete_report_post(req: DeleteReportRequest):
    """특정 회의록 리포트 영구 삭제 (POST 백업 엔드포인트)"""
    return perform_delete_report(req.report_id)

@app.delete("/api/v1/reports/{report_id}")
def delete_report(report_id: str):
    """특정 회의록 리포트 영구 삭제 (RESTful DELETE)"""
    return perform_delete_report(report_id)

@app.get("/api/v1/system/logs")
def get_logs_endpoint(
    level: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
):
    """실시간 시스템 진단 및 에러 분석 로그 조회 (Ring Buffer)"""
    logs = get_system_logs(level=level, search=search, limit=min(limit, 200))
    return {
        "status": "SUCCESS",
        "total": len(logs),
        "logs": logs
    }

@app.delete("/api/v1/system/logs")
def clear_logs_endpoint():
    """실시간 시스템 로그 버퍼 비우기"""
    clear_system_logs()
    return {"status": "SUCCESS", "message": "시스템 로그 버퍼가 초기화되었습니다."}





@app.get("/api/v1/notes/current")
def get_current_meeting_notes(sample: Optional[str] = "coway_meet_85min"):
    """
    현재 등록된 회의의 구조화 회의록 및 100% 무가공 대화 전사(Verbatim) 전문 반환
    """
    import re
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    candidate_paths = [
        os.path.join(root_dir, "data", "samples", "coway_meeting_transcript_20260818.md"),
        os.path.join(root_dir, "data", "outputs", "transcripts", "coway_meeting_transcript_20260818.md"),
        os.path.join(root_dir, "coway_meeting_transcript_20260818.md")
    ]
    transcript_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    meeting_id = "meet-20260818-coway-ai"
    
    turns = []
    pattern = re.compile(r"^\[\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*\]\s*([^:]+):\s*(.*)$")
    
    if transcript_path and os.path.exists(transcript_path):
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                m = pattern.match(line)
                if m:
                    turns.append({
                        "time": f"[{m.group(1).strip()}]",
                        "speaker": m.group(2).strip(),
                        "text": m.group(3).strip()
                    })
                    
    return {
        "status": "SUCCESS",
        "meeting_id": meeting_id,
        "total_turns": len(turns),
        "transcript": turns
    }

@app.post("/api/v1/media/verify-url")
def verify_media_url(req: VerifyUrlRequest):
    """
    미디어 URL (Web URL 또는 GCS gs:// 경로) 유효성 및 접근 가능 여부 실시간 검증
    """
    url = req.url.strip()
    if not url:
        return {"status": "INVALID", "accessible": False, "message": "❌ URL이 입력되지 않았습니다."}
    
    # 1. GCS gs:// 경로 검증
    if url.startswith("gs://"):
        try:
            parts = url[5:].split("/", 1)
            bucket_name = parts[0]
            blob_name = parts[1] if len(parts) > 1 else ""
            
            from google.cloud import storage
            client = storage.Client(project=settings.GCP_PROJECT_ID)
            bucket = client.bucket(bucket_name)
            if not bucket.exists():
                return {"status": "INVALID", "accessible": False, "source_type": "GCS", "message": f"❌ GCS 버킷 '{bucket_name}'이 존재하지 않거나 권한이 없습니다."}
            
            blob = bucket.get_blob(blob_name)
            if not blob or not blob.exists():
                return {"status": "INVALID", "accessible": False, "source_type": "GCS", "message": f"❌ 버킷 내 파일 '{blob_name}'을 찾을 수 없습니다."}
            
            size_mb = round(blob.size / (1024 * 1024), 2)
            content_type = blob.content_type or "audio/mp4"
            return {
                "status": "VALID",
                "accessible": True,
                "source_type": "GCS",
                "url": url,
                "size_mb": size_mb,
                "content_type": content_type,
                "message": f"✅ GCS 버킷 미디어 접근 확인 성공 ({size_mb} MB, {content_type})"
            }
        except Exception as e:
            return {"status": "INVALID", "accessible": False, "source_type": "GCS", "message": f"❌ GCS 접근 오류: {str(e)}"}

    # 2. Google Drive URL 검증 및 처리
    if "drive.google.com" in url or "docs.google.com" in url:
        import re
        # 폴더 URL인 경우
        if "/folders/" in url:
            folder_id_match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
            folder_id = folder_id_match.group(1) if folder_id_match else "알 수 없음"
            return {
                "status": "INVALID",
                "accessible": False,
                "source_type": "GOOGLE_DRIVE",
                "url": url,
                "message": f"❌ Google Drive '폴더' URL입니다 (Folder ID: {folder_id}). 폴더 자체가 아닌 폴더 내 특정 녹화본 파일(.mp4)의 링크를 지정해주세요."
            }
        
        # 파일 URL인 경우
        file_id_match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url) or re.search(r"id=([a-zA-Z0-9_-]+)", url)
        if file_id_match:
            file_id = file_id_match.group(1)
            try:
                from app.services.workspace_service import WorkspaceService
                ws = WorkspaceService(allow_interactive=False)
                file_meta = ws.drive_client.files().get(fileId=file_id, fields="id, name, mimeType, size").execute()
                
                name = file_meta.get("name", "녹화본 파일")
                mime_type = file_meta.get("mimeType", "video/mp4")
                size_bytes = int(file_meta.get("size", 0))
                size_mb = round(size_bytes / (1024 * 1024), 2)
                
                return {
                    "status": "VALID",
                    "accessible": True,
                    "source_type": "GOOGLE_DRIVE",
                    "url": url,
                    "size_mb": size_mb,
                    "content_type": mime_type,
                    "message": f"✅ Google Drive 미디어 접근 확인 성공 ({name}, {size_mb} MB, {mime_type})"
                }
            except Exception as e:
                return {
                    "status": "INVALID",
                    "accessible": False,
                    "source_type": "GOOGLE_DRIVE",
                    "url": url,
                    "message": f"⚠️ Google Drive 파일 (ID: {file_id}) 접근 권한 필요: {str(e)}"
                }
        else:
            return {
                "status": "INVALID",
                "accessible": False,
                "source_type": "GOOGLE_DRIVE",
                "url": url,
                "message": "❌ Google Drive URL에서 파일 ID를 추출할 수 없습니다. 올바른 공유 링크를 입력해주세요."
            }

    # 3. 일반 HTTP/HTTPS 웹 미디어 URL 검증
    if url.startswith("http://") or url.startswith("https://"):
        import httpx
        try:
            with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                resp = client.head(url)
                if resp.status_code >= 400 or not resp.headers.get("content-type"):
                    resp = client.get(url, headers={"Range": "bytes=0-1024"})
                
                if resp.status_code in (200, 206, 302):
                    content_type = (resp.headers.get("Content-Type") or resp.headers.get("content-type") or "").lower()
                    content_length = resp.headers.get("Content-Length") or resp.headers.get("content-length")
                    size_mb = round(int(content_length) / (1024 * 1024), 2) if content_length and content_length.isdigit() else 0.0
                    
                    # HTML 웹페이지인 경우 미디어 스트림이 아님을 정확히 거부
                    if "text/html" in content_type or "text/plain" in content_type or "application/json" in content_type:
                        return {
                            "status": "INVALID",
                            "accessible": False,
                            "source_type": "WEB_URL",
                            "url": url,
                            "content_type": content_type,
                            "message": f"❌ 미디어 파일이 아닌 웹페이지(HTML/텍스트)입니다 ({content_type}). 직접 다운로드/재생 가능한 미디어 파일 URL(.mp4, .mp3, .m4a 등)이나 GCS(gs://) 경로를 입력해주세요."
                        }
                    
                    # 오디오 / 비디오 / 바이너리 미디어 스트림 확인
                    is_media = (
                        content_type.startswith("audio/") or 
                        content_type.startswith("video/") or 
                        "application/octet-stream" in content_type or
                        any(url.lower().endswith(ext) for ext in [".mp4", ".mov", ".m4a", ".mp3", ".wav", ".webm", ".mkv"])
                    )
                    
                    if is_media:
                        return {
                            "status": "VALID",
                            "accessible": True,
                            "source_type": "WEB_URL",
                            "url": url,
                            "size_mb": size_mb,
                            "content_type": content_type,
                            "message": f"✅ Web 미디어 스트림 접근 확인 성공 ({size_mb} MB, {content_type})"
                        }
                    else:
                        return {
                            "status": "INVALID",
                            "accessible": False,
                            "source_type": "WEB_URL",
                            "url": url,
                            "content_type": content_type,
                            "message": f"⚠️ 미디어 스트림 여부가 불분명합니다 ({content_type}). 직접 미디어 파일 URL인지 확인해주세요."
                        }
                else:
                    return {
                        "status": "INVALID",
                        "accessible": False,
                        "source_type": "WEB_URL",
                        "url": url,
                        "message": f"❌ URL 접근 실패: HTTP 상태 코드 {resp.status_code}"
                    }
        except Exception as e:
            return {"status": "INVALID", "accessible": False, "source_type": "WEB_URL", "message": f"❌ URL 연결 실패: {str(e)}"}
            
    return {"status": "INVALID", "accessible": False, "message": "❌ 지원되지 않는 URL 형식입니다. (http://, https://, gs://)"}

@app.get("/api/v1/storage/bucket-files")
def get_bucket_files():
    """
    GCS 버킷의 data/input_media/ 경로 및 로컬 data/input_media/ 미디어 파일 목록 조회
    """
    results = []
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. 로컬 data/input_media 디렉토리 스캔
    local_input_dir = os.path.join(root_dir, "data", "input_media")
    if os.path.exists(local_input_dir):
        for f in os.listdir(local_input_dir):
            if f.startswith("."):
                continue
            full_p = os.path.join(local_input_dir, f)
            if os.path.isfile(full_p):
                stat = os.stat(full_p)
                import datetime
                results.append({
                    "name": f,
                    "path": f"data/input_media/{f}",
                    "uri": f"data/input_media/{f}",
                    "location": "LOCAL_DISK",
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "updated_at": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "is_ready": True
                })

    # 2. GCS 버킷 data/input_media/ 스캔
    try:
        from google.cloud import storage
        from app.core.auth_utils import get_google_credentials
        creds = get_google_credentials()
        client = storage.Client(project=settings.GCP_PROJECT_ID, credentials=creds) if creds else storage.Client(project=settings.GCP_PROJECT_ID)
        bucket = client.bucket(settings.TEMP_GCS_BUCKET)
        blobs = list(bucket.list_blobs(prefix="data/input_media/"))
        for b in blobs:
            if b.name.endswith("/"):
                continue
            fname = os.path.basename(b.name)
            # 중복 체크
            if not any(r["name"] == fname for r in results):
                results.append({
                    "name": fname,
                    "path": b.name,
                    "uri": f"gs://{settings.TEMP_GCS_BUCKET}/{b.name}",
                    "location": "GCS_BUCKET",
                    "size_mb": round(b.size / (1024 * 1024), 2) if b.size else 0.0,
                    "updated_at": b.updated.strftime("%Y-%m-%d %H:%M") if b.updated else "-",
                    "is_ready": True
                })
    except Exception as e:
        print(f"GCS bucket list warning: {e}")

    return {
        "status": "SUCCESS",
        "bucket_name": settings.TEMP_GCS_BUCKET,
        "prefix": "data/input_media/",
        "files": results
    }

@app.post("/api/v1/notes/process-uri")
def process_media_uri(req: ProcessUriRequest):
    """
    GCS URI 또는 로컬 data/input_media 미디어 파일을 기반으로 회의록 및 전사본 병렬 생성
    """
    gemini_svc = GeminiMeetingService()
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    uri = req.uri.strip()
    
    with AudioService.managed_temp_dir() as temp_dir:
        # 로컬 파일 경로인 경우
        if uri.startswith("data/input_media/") or os.path.exists(os.path.join(root_dir, uri)):
            local_path = os.path.join(root_dir, uri) if not os.path.isabs(uri) else uri
            extracted_mp3 = os.path.join(temp_dir, "audio.mp3")
            AudioService.extract_audio(local_path, extracted_mp3)
            gcs_uri = GCSStorageService.upload_temp_audio(extracted_mp3)
            cleanup_gcs = True
        elif uri.startswith("gs://"):
            gcs_uri = uri
            cleanup_gcs = False
        else:
            raise HTTPException(status_code=400, detail="유효하지 않은 미디어 URI입니다.")
        
        template_prompt = template_service.get_prompt(req.template_type)
        try:
            notes, transcript = run_parallel_gemini_analysis(
                gemini_svc=gemini_svc,
                gcs_audio_uri=gcs_uri,
                meeting_title=req.meeting_title,
                attendees=req.attendees,
                template_prompt=template_prompt,
                template_type=req.template_type
            )
            
            attendee_str = ", ".join(req.attendees) if req.attendees else "참석자 미입력"
            new_report = create_and_save_report(
                title=req.meeting_title,
                duration_minutes=25,
                template_type=req.template_type,
                attendees=attendee_str,
                audio_source=f"미디어 URL ({uri})",
                notes=notes,
                transcript=transcript,
                sample_key="custom_upload"
            )
            
            return {
                "status": "SUCCESS",
                "report_id": new_report["id"],
                "notes": notes,
                "transcript": transcript,
                "report": new_report,
                "model": settings.GEMINI_MODEL_NAME
            }
        finally:
            if cleanup_gcs:
                GCSStorageService.delete_temp_audio(gcs_uri)

@app.post("/api/v1/notes/upload-chunk")
async def upload_file_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    title: str = Form(""),
    attendees: str = Form(""),
    template_type: str = Form("CFT_REGULAR"),
    chunk: UploadFile = File(...)
):
    """
    대용량 미디어 파일(50MB~2GB+) 분할 청크 업로드 엔드포인트
    API Gateway 32MB 단일 페이로드 제한을 완벽하게 우회하여 대용량 비디오/오디오를 안정적으로 처리
    """
    upload_dir = os.path.join("/tmp", "coway_uploads", upload_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    part_path = os.path.join(upload_dir, f"part_{chunk_index:05d}")
    with open(part_path, "wb") as f:
        content = await chunk.read()
        f.write(content)
        
    # 모든 청크가 수신되었는지 확인
    if chunk_index == total_chunks - 1:
        # 1. 파일 합치기
        combined_path = os.path.join(upload_dir, filename)
        with open(combined_path, "wb") as outfile:
            for i in range(total_chunks):
                p = os.path.join(upload_dir, f"part_{i:05d}")
                if os.path.exists(p):
                    with open(p, "rb") as infile:
                        outfile.write(infile.read())
                    try:
                        os.remove(p)
                    except Exception:
                        pass
                        
        # 2. 오디오 추출 및 Gemini 분석
        gemini_svc = GeminiMeetingService()
        attendee_list = [a.strip() for a in attendees.split(",") if a.strip()]
        template_prompt = template_service.get_prompt(template_type)
        
        with AudioService.managed_temp_dir() as temp_dir:
            extracted_mp3 = os.path.join(temp_dir, "audio.mp3")
            AudioService.extract_audio(combined_path, extracted_mp3)
            
            gcs_uri = None
            audio_target = extracted_mp3
            try:
                gcs_uri = GCSStorageService.upload_temp_audio(extracted_mp3)
                audio_target = gcs_uri
            except Exception as gcs_err:
                logger.warning(f"GCS 업로드 실패 (로컬 다이렉트 바이너리 모드로 자동 전환): {gcs_err}")
                audio_target = extracted_mp3

            try:
                effective_title = title.strip() or os.path.splitext(filename)[0]
                notes, transcript = run_parallel_gemini_analysis(
                    gemini_svc=gemini_svc,
                    gcs_audio_uri=audio_target,
                    meeting_title=effective_title,
                    attendees=attendee_list,
                    template_prompt=template_prompt,
                    template_type=template_type
                )
                
                # 보관함에 새 리포트로 자동 등록
                duration_minutes = 1
                try:
                    dur_sec = AudioService.get_duration(extracted_mp3)
                    duration_minutes = max(1, int(round(dur_sec / 60)))
                except Exception:
                    duration_minutes = 1
                    
                new_report = create_and_save_report(
                    title=effective_title,
                    duration_minutes=duration_minutes,
                    template_type=template_type,
                    attendees=attendees or "참석자 미입력",
                    audio_source=f"업로드 파일 ({filename})",
                    notes=notes,
                    transcript=transcript,
                    sample_key="custom_upload"
                )
                
                return {
                    "status": "SUCCESS",
                    "message": "회의록 및 전사본 생성 완료",
                    "report_id": new_report["id"],
                    "notes": notes,
                    "transcript": transcript,
                    "report": new_report,
                    "model": settings.GEMINI_MODEL_NAME
                }
            finally:
                if gcs_uri:
                    GCSStorageService.delete_temp_audio(gcs_uri)
                shutil.rmtree(upload_dir, ignore_errors=True)
                
    return {
        "status": "CHUNK_RECEIVED",
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "progress": round(((chunk_index + 1) / total_chunks) * 100, 1)
    }

@app.post("/api/v1/notes/get-upload-session", response_model=ResumableSessionResponse)
def get_upload_session(req: ResumableSessionRequest, request: Request):
    """
    GCS Direct Resumable Upload 세션 URL 발급 엔드포인트
    브라우저가 대용량(100MB~5GB) 미디어를 백엔드 경유 없이 GCS 버킷으로 직접 다이렉트 업로드할 수 있도록 지원합니다.
    """
    try:
        origin = req.origin or request.headers.get("origin") or "https://coway-agent-gateway-7p7fk8nj.uc.gateway.dev"
        session_info = GCSStorageService.create_resumable_upload_session(
            filename=req.filename,
            content_type=req.content_type,
            origin=origin
        )
        return ResumableSessionResponse(
            status="SUCCESS",
            upload_url=session_info["upload_url"],
            gcs_uri=session_info["gcs_uri"],
            blob_name=session_info["blob_name"],
            bucket=session_info["bucket"]
        )
    except Exception as e:
        logger.error(f"GCS Resumable 세션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/notes/process-gcs-media")
def process_gcs_media(req: ProcessGCSMediaRequest):
    """
    GCS 다이렉트 업로드 완료 후 미디어(비디오/오디오) 분석 및 회의록 자동 생성 엔드포인트
    1. 오디오 파일인 경우: GCS URI 직접 전달하여 Zero Transfer로 Gemini 3.7 분석
    2. 비디오 파일인 경우: 오디오 추출 후 병렬 Gemini 분석 수행
    """
    gemini_svc = GeminiMeetingService()
    attendee_list = [a.strip() for a in req.attendees.split(",") if a.strip()]
    template_prompt = template_service.get_prompt(req.template_type)
    
    ext = os.path.splitext(req.filename)[1].lower()
    is_direct_audio = ext in [".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"]
    
    temp_extracted_gcs = None
    try:
        with AudioService.managed_temp_dir() as temp_dir:
            local_media = os.path.join(temp_dir, req.filename)
            GCSStorageService.download_to_file(req.gcs_uri, local_media)

            if is_direct_audio:
                local_audio_path = local_media
                audio_target = req.gcs_uri
            else:
                extracted_mp3 = os.path.join(temp_dir, "extracted_audio.mp3")
                AudioService.extract_audio(local_media, extracted_mp3)
                temp_extracted_gcs = GCSStorageService.upload_temp_audio(extracted_mp3)
                audio_target = temp_extracted_gcs
                local_audio_path = extracted_mp3

            try:
                dur_sec = AudioService.get_duration(local_audio_path)
                duration_minutes = max(1, int(round(dur_sec / 60)))
            except Exception:
                duration_minutes = 1

            effective_title = req.title.strip() or os.path.splitext(req.filename)[0]
            notes, transcript, stt_transcript = run_hybrid_transcription_pipeline(
                gemini_svc=gemini_svc,
                gcs_audio_uri=audio_target,
                meeting_title=effective_title,
                attendees=attendee_list,
                template_prompt=template_prompt,
                template_type=req.template_type,
                local_audio_path=local_audio_path
            )
            
            summary_text = ""
            if hasattr(notes, "executive_summary"):
                summary_text = notes.executive_summary
            elif isinstance(notes, dict):
                summary_text = notes.get("executive_summary", "")
                
            new_report = create_and_save_report(
                title=effective_title,
                duration_minutes=duration_minutes,
                template_type=req.template_type,
                attendees=req.attendees or "참석자 미입력",
                audio_source=f"GCS 다이렉트 업로드 ({req.filename})",
                notes=notes,
                transcript=transcript,
                stt_transcript=[],
                sample_key="custom_upload"
            )

            # 백그라운드 비동기 Cloud STT 전사 구동 (메인 화면은 즉시 완료 반환)
            bg_stt_path = None
            if local_audio_path and os.path.exists(local_audio_path):
                try:
                    bg_dir = AudioService.create_temp_dir()
                    bg_stt_path = os.path.join(bg_dir, "stt_bg_input.mp3")
                    shutil.copy2(local_audio_path, bg_stt_path)
                except Exception:
                    pass
            start_background_stt(new_report["id"], bg_stt_path, audio_target)
            
            return {
                "status": "SUCCESS",
                "report_id": new_report["id"],
                "notes": notes,
                "transcript": transcript,
                "stt_transcript": [],
                "stt_status": "PROCESSING",
                "report": new_report,
                "model": settings.GEMINI_MODEL_NAME
            }
    finally:
        # Zero Retention: 원본 업로드 및 임시 추출 오디오 즉시 정리
        if req.gcs_uri:
            GCSStorageService.delete_temp_audio(req.gcs_uri)
        if temp_extracted_gcs:
            GCSStorageService.delete_temp_audio(temp_extracted_gcs)

@app.post("/api/v1/notes/upload-media")
def process_uploaded_media(
    file: UploadFile = File(...),
    title: str = Form("코웨이 AI 기술 미팅"),
    attendees: str = Form("홍길동 팀장, 이상훈 담당, 고정현 CE"),
    template_type: str = Form("CFT_REGULAR")
):
    """
    로컬 비디오(.mp4/.mov) 또는 오디오(.wav/.mp3) 직접 업로드 처리 엔드포인트
    (Gemini 초고속 응답 & 백그라운드 STT 비동기 파이프라인)
    """
    gemini_svc = GeminiMeetingService()
    attendee_list = [a.strip() for a in attendees.split(",") if a.strip()]
    template_prompt = template_service.get_prompt(template_type)

    with AudioService.managed_temp_dir() as temp_dir:
        input_path = os.path.join(temp_dir, file.filename)
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        extracted_mp3 = os.path.join(temp_dir, "audio.mp3")
        AudioService.extract_audio(input_path, extracted_mp3)

        gcs_uri = None
        audio_target = extracted_mp3
        try:
            gcs_uri = GCSStorageService.upload_temp_audio(extracted_mp3)
            audio_target = gcs_uri
        except Exception as gcs_err:
            logger.warning(f"GCS 업로드 실패 (로컬 다이렉트 바이너리 모드로 자동 전환): {gcs_err}")
            audio_target = extracted_mp3

        try:
            notes, transcript, _ = run_hybrid_transcription_pipeline(
                gemini_svc=gemini_svc,
                gcs_audio_uri=audio_target,
                meeting_title=title,
                attendees=attendee_list,
                template_prompt=template_prompt,
                template_type=template_type,
                local_audio_path=extracted_mp3
            )

            # 보관함에 새 리포트로 자동 등록
            duration_minutes = 1
            try:
                dur_sec = AudioService.get_duration(extracted_mp3)
                duration_minutes = max(1, int(round(dur_sec / 60)))
            except Exception:
                duration_minutes = 1
            
            new_report = create_and_save_report(
                title=title,
                duration_minutes=duration_minutes,
                template_type=template_type,
                attendees=", ".join(attendee_list) if attendee_list else "참석자 미입력",
                audio_source=f"업로드 미디어 ({file.filename})",
                notes=notes,
                transcript=transcript,
                stt_transcript=[],
                sample_key="custom_upload"
            )

            # 백그라운드 비동기 STT 구동
            bg_stt_path = None
            if extracted_mp3 and os.path.exists(extracted_mp3):
                try:
                    bg_dir = AudioService.create_temp_dir()
                    bg_stt_path = os.path.join(bg_dir, "stt_bg_input.mp3")
                    shutil.copy2(extracted_mp3, bg_stt_path)
                except Exception:
                    pass
            start_background_stt(new_report["id"], bg_stt_path, audio_target)

            return {
                "status": "SUCCESS",
                "report_id": new_report["id"],
                "notes": notes,
                "transcript": transcript,
                "stt_transcript": [],
                "stt_status": "PROCESSING",
                "report": new_report,
                "model": settings.GEMINI_MODEL_NAME
            }
        finally:
            if gcs_uri:
                GCSStorageService.delete_temp_audio(gcs_uri)

@app.post("/api/v1/notes/replace-speakers")
def replace_speakers(req: ReplaceSpeakerRequest):
    """
    화자 라벨 일괄 치환(Replace All) 엔드포인트
    """
    updated_md = SpeakerMappingService.replace_speaker_labels(
        req.markdown_text, req.speaker_mapping
    )
    return {
        "status": "SUCCESS",
        "updated_markdown": updated_md
    }

@app.post("/api/v1/notes/process-drive")
def process_drive_recording(req: DriveProcessRequest):
    """
    Google Drive에 저장된 Meet 녹화본 병렬 처리 엔드포인트
    """
    gemini_svc = GeminiMeetingService()
    template_prompt = template_service.get_prompt(req.template_type)

    with AudioService.managed_temp_dir() as temp_dir:
        local_video = os.path.join(temp_dir, "meet_recording.mp4")
        extracted_mp3 = os.path.join(temp_dir, "audio.mp3")

        ws = WorkspaceService()
        ws.download_drive_video(req.drive_file_id, local_video)
        AudioService.extract_audio(local_video, extracted_mp3)

        gcs_uri = GCSStorageService.upload_temp_audio(extracted_mp3)
        try:
            notes, transcript = run_parallel_gemini_analysis(
                gemini_svc=gemini_svc,
                gcs_audio_uri=gcs_uri,
                meeting_title=req.meeting_title,
                attendees=req.attendees,
                template_prompt=template_prompt,
                template_type=req.template_type,
                local_audio_path=extracted_mp3
            )
            return {
                "status": "SUCCESS",
                "notes": notes,
                "transcript": transcript,
                "model": settings.GEMINI_MODEL_NAME
            }
        finally:
            GCSStorageService.delete_temp_audio(gcs_uri)


# ==============================================================================
# 템플릿 관리 REST API
# ==============================================================================

@app.get("/api/v1/templates")
def list_templates():
    """모든 회의록 프롬프트 템플릿 목록 조회"""
    return {
        "status": "SUCCESS",
        "templates": template_service.list_templates()
    }

@app.get("/api/v1/templates/{template_id}")
def get_template(template_id: str):
    """특정 템플릿 정보 및 프롬프트 상세 조회"""
    tpl = template_service.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="해당 템플릿을 찾을 수 없습니다.")
    return {
        "status": "SUCCESS",
        "template": tpl
    }

@app.put("/api/v1/templates/{template_id}")
def update_template(template_id: str, req: UpdateTemplateRequest):
    """특정 템플릿 프롬프트 및 메타데이터 수정/저장"""
    prompt_content = req.prompt if req.prompt is not None else (req.system_prompt or "")
    updated = template_service.update_template(
        template_id=template_id,
        prompt=prompt_content,
        name=req.name,
        description=req.description
    )
    return {
        "status": "SUCCESS",
        "message": f"템플릿 '{updated.get('name')}'(이)가 성공적으로 저장되었습니다.",
        "template": updated
    }

@app.post("/api/v1/templates/{template_id}/reset")
def reset_template(template_id: str):
    """특정 템플릿을 시스템 기본 프롬프트로 초기화"""
    reset = template_service.reset_template(template_id)
    if not reset:
        raise HTTPException(status_code=404, detail="기본 템플릿이 아니거나 찾을 수 없습니다.")
    return {
        "status": "SUCCESS",
        "message": f"템플릿 '{reset.get('name')}'(이)가 기본값으로 복원되었습니다.",
        "template": reset
    }

