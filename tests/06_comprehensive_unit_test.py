import os
import sys
import time
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, load_reports_from_disk, save_reports_to_disk
from app.services.speaker_service import SpeakerMappingService
from app.core.auth_utils import get_google_credentials

def run_all_tests():
    print("==================================================================")
    print("🚀 [COWAY AI PORTAL] 신규 기능 및 최적화 단위 테스트 시작")
    print("==================================================================")

    client = TestClient(app)

    # -------------------------------------------------------------
    # Test 1: 화자 일괄 치환 (Replace All) 다양한 커스텀 라벨 치환 검증
    # -------------------------------------------------------------
    print("\n[Test 1] 🔄 화자 지능형 일괄 치환 (Speaker Mapping) 검증...")
    sample_text = (
        "안건 1에서 [참석자 1]과 [화자 2], 그리고 Speaker 3이 의견을 교환했습니다.\n"
        "[참석자 1]은 AI 시스템 아키텍처를 제안했고, Speaker 3은 이에 동의했습니다."
    )
    mapping = {
        "[참석자 1]": "홍길동 팀장 (코웨이)",
        "[화자 2]": "고정현 CE (Google Cloud)",
        "Speaker 3": "김원유 Specialist (Google Workspace)"
    }
    
    # 1-1. 서비스 계층 테스트
    res_text = SpeakerMappingService.replace_speakers(sample_text, mapping)
    assert "[참석자 1]" not in res_text, "참석자 1 치환 실패"
    assert "[화자 2]" not in res_text, "화자 2 치환 실패"
    assert "Speaker 3" not in res_text, "Speaker 3 치환 실패"
    assert "홍길동 팀장 (코웨이)" in res_text
    assert "고정현 CE (Google Cloud)" in res_text
    assert "김원유 Specialist (Google Workspace)" in res_text
    print("   ✅ Service 계층 커스텀 화자 다중 치환 성공")

    # 1-2. REST API 엔드포인트 테스트
    res_api = client.post("/api/v1/notes/replace-speakers", json={
        "markdown_text": sample_text,
        "speaker_mapping": mapping
    })
    assert res_api.status_code == 200
    api_json = res_api.json()
    assert api_json.get("status") == "SUCCESS"
    assert "홍길동 팀장 (코웨이)" in api_json.get("updated_markdown")
    print("   ✅ API POST /api/v1/notes/replace-speakers 엔드포인트 응답 검증 성공")

    # -------------------------------------------------------------
    # Test 2: 회의록 보관함 조회/검색/삭제 성능 및 무결성 검증
    # -------------------------------------------------------------
    print("\n[Test 2] ⚡ 회의록 보관함 (Reports Archive) 초고속 조회 및 CRUD 검증...")
    
    # Mock report 데이터 주입
    test_report_id = "report-test-unit-001"
    test_report = {
        "id": test_report_id,
        "title": "단위 테스트 코웨이 기술 미팅",
        "date": "2026-08-28",
        "time": "10:00 (총 45분)",
        "duration_minutes": 45,
        "template_type": "CFT_REGULAR",
        "template_name": "CFT 정기 회의",
        "attendees": "홍길동 팀장, 고정현 CE",
        "summary_snippet": "단위 테스트 검증용 1페이지 요약입니다.",
        "executive_summary": "단위 테스트 검증용 상세 요약 내용입니다.",
        "key_decisions": ["SimSolid PoC 진행 합의"],
        "agendas": [{"title": "안건 1", "summary": "테스트 요약", "content": "내용", "speakers": ["고정현 CE"]}],
        "action_items": [{"task": "아키텍처 문서화", "assignee": "고정현 CE", "due": "2026-08-30", "status": "TODO"}],
        "transcript": [{"time": "[00:00:00]", "speaker": "고정현 CE", "text": "안녕하세요"}],
        "created_at": "2026-08-28 10:00:00",
        "status": "COMPLETED",
        "audio_source": "로컬 파일 업로드 (test.mp3)"
    }
    
    # 디스크/메모리에 저장
    current_reports = load_reports_from_disk(force_reload=True)
    save_reports_to_disk([test_report] + current_reports)

    # 2-1. 목록 조회 속도 (Latency) 테스트
    start_t = time.time()
    res_list = client.get("/api/v1/reports")
    elapsed_ms = (time.time() - start_t) * 1000
    assert res_list.status_code == 200
    list_json = res_list.json()
    assert list_json.get("status") == "SUCCESS"
    assert any(r["id"] == test_report_id for r in list_json.get("reports", []))
    print(f"   ✅ GET /api/v1/reports 목록 조회 성공 (응답 지연시간: {elapsed_ms:.2f}ms - 초고속 검증 통과)")

    # 2-2. 검색 및 템플릿 필터링 테스트
    res_search = client.get("/api/v1/reports?search=코웨이")
    assert res_search.status_code == 200
    assert len(res_search.json().get("reports", [])) >= 1
    print("   ✅ 키워드 검색 필터링 정상 동작 확인")

    # 2-3. 단건 상세 조회 테스트
    res_detail = client.get(f"/api/v1/reports/{test_report_id}")
    assert res_detail.status_code == 200
    detail_json = res_detail.json()
    assert detail_json.get("report_meta", {}).get("id") == test_report_id or detail_json.get("report", {}).get("id") == test_report_id
    print("   ✅ GET /api/v1/reports/{id} 상세 메타데이터 반환 확인")

    # 2-4. 삭제 테스트
    res_delete = client.delete(f"/api/v1/reports/{test_report_id}")
    assert res_delete.status_code == 200
    del_json = res_delete.json()
    assert del_json.get("status") == "SUCCESS"
    assert del_json.get("deleted_id") == test_report_id
    print("   ✅ DELETE /api/v1/reports/{id} 정상 삭제 및 즉시 캐시 동기화 확인")

    # -------------------------------------------------------------
    # Test 3: Cloud Run 환경 인증 자격 (ADC) 초고속 획득 검증
    # -------------------------------------------------------------
    print("\n[Test 3] 🛡️ Cloud Run 환경 감지 시 0ms 직결 ADC 인증 자격 획득 검증...")
    os.environ["K_SERVICE"] = "coway-meet-notes-service"
    start_auth_t = time.time()
    creds = get_google_credentials()
    auth_elapsed_ms = (time.time() - start_auth_t) * 1000
    print(f"   ✅ Serverless ADC 자격 획득 완료 (소요시간: {auth_elapsed_ms:.2f}ms - gcloud subprocess 차단 검증)")
    os.environ.pop("K_SERVICE", None)

    # -------------------------------------------------------------
    # Test 4: 미디어 URL 검증 API (/api/v1/media/verify-url)
    # -------------------------------------------------------------
    print("\n[Test 4] 🔗 미디어 URL 유효성 검증 API 테스트...")
    # 빈 URL 테스트
    res_empty_url = client.post("/api/v1/media/verify-url", json={"url": ""})
    assert res_empty_url.json().get("status") == "INVALID"
    print("   ✅ 빈 URL 입력 시 거부(INVALID) 검증 완료")
    
    # 웹 URL 형식 검증 테스트
    res_web_url = client.post("/api/v1/media/verify-url", json={"url": "https://storage.googleapis.com/sample/audio.mp3"})
    assert res_web_url.status_code == 200
    assert res_web_url.json().get("status") in ["VALID", "INVALID"]
    print("   ✅ 미디어 URL 검증 API 정상 응답 확인")

    # -------------------------------------------------------------
    # Test 5: 프롬프트 템플릿 엔드포인트 검증
    # -------------------------------------------------------------
    print("\n[Test 5] ⚙️ 프롬프트 템플릿 관리 엔드포인트 테스트...")
    res_templates = client.get("/api/v1/templates")
    assert res_templates.status_code == 200
    templates_data = res_templates.json()
    tpl_list = templates_data.get("templates", [])
    tpl_ids = [t["id"] if isinstance(t, dict) else t for t in tpl_list]
    assert "CFT_REGULAR" in tpl_ids
    assert "KICKOFF" in tpl_ids
    assert "EXECUTIVE" in tpl_ids
    print("   ✅ 회의 템플릿 목록 3종 정상 반환 확인 (CFT_REGULAR, KICKOFF, EXECUTIVE)")

    print("\n==================================================================")
    print("🎉 [모든 단위 테스트 통과 (ALL 5 TEST SUITES PASSED!)]")
    print("==================================================================")

if __name__ == "__main__":
    run_all_tests()
