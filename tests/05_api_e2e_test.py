import os
import sys
import subprocess
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

def test_api_e2e():
    print("=== [테스트 5: FastAPI REST API 엔드투엔드 통합 테스트] ===")
    client = TestClient(app)

    # 1. 헬스체크 및 UI 엔드포인트 검증
    print("1. GET /healthz 헬스체크 엔드포인트 테스트...")
    res = client.get("/healthz")
    assert res.status_code == 200, f"헬스체크 실패: {res.status_code}"
    data = res.json()
    print(f"   ✅ 서비스 상태: {data.get('status')}, 모델: {data.get('model')}")
    assert data.get("status") == "HEALTHY"

    res_ui = client.get("/")
    assert res_ui.status_code == 200, f"UI 서빙 실패: {res_ui.status_code}"
    print("   ✅ UI 메인 화면 서빙 정상 확인")

    # 2. 화자 치환 API 검증
    print("2. POST /api/v1/notes/replace-speakers 테스트...")
    replace_payload = {
        "markdown_text": "안건 논의에서 [참석자 1]이 발언했습니다.",
        "speaker_mapping": {"[참석자 1]": "김유진 팀장"}
    }
    res = client.post("/api/v1/notes/replace-speakers", json=replace_payload)
    assert res.status_code == 200
    res_data = res.json()
    assert "김유진 팀장이 발언했습니다." in res_data.get("updated_markdown")
    print("   ✅ 화자 치환 API 정상 동작 확인")

    # 3. 미디어 파일 업로드 API 검증
    print("3. POST /api/v1/notes/upload-media 멀티파트 업로드 테스트...")
    temp_wav = "/tmp/test_api_speech.wav"
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=800:duration=5",
        "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", temp_wav
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        with open(temp_wav, "rb") as f:
            files = {"file": ("test_api_speech.wav", f, "audio/wav")}
            data = {
                "title": "API E2E 검증 회의",
                "attendees": "김유진 팀장, 이상훈 담당, 고정현 CE",
                "template_type": "CFT_REGULAR"
            }
            res = client.post("/api/v1/notes/upload-media", files=files, data=data)

        assert res.status_code == 200, f"업로드 API 호출 실패: {res.text}"
        res_json = res.json()
        print(f"   ✅ API 응답 상태: {res_json.get('status')}")
        notes = res_json.get("notes")
        assert notes is not None, "회의록 응답이 비어있음"
        print(f"   ✅ 생성된 회의 제목: {notes.get('meeting_title')}")
        print(f"   ✅ 요약 본문: {notes.get('executive_summary')[:60]}...")
        print(">>> [테스트 5 성공] FastAPI REST API 엔드투엔드 통합 검증 완료!\n")
    finally:
        if os.path.exists(temp_wav):
            os.remove(temp_wav)

if __name__ == "__main__":
    test_api_e2e()
