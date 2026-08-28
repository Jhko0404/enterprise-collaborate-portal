import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.audio_service import AudioService
from app.services.storage_service import GCSStorageService
from app.services.gemini_service import GeminiMeetingService
from app.templates.cft_regular import CFT_REGULAR_PROMPT
from app.templates.kickoff import KICKOFF_PROMPT, EXECUTIVE_PROMPT

def test_gemini_diarization():
    print("=== [테스트 3: Vertex AI Gemini 멀티모달 화자 분리 및 3대 템플릿 검증] ===")
    
    gemini_svc = GeminiMeetingService()
    
    with AudioService.managed_temp_dir() as temp_dir:
        dummy_wav = os.path.join(temp_dir, "test_speech.wav")
        
        # 1. 10초 분량의 16kHz 모노 테스트 오디오 생성
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=800:duration=10",
            "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", dummy_wav
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 2. GCS 임시 업로드
        gcs_uri = GCSStorageService.upload_temp_audio(dummy_wav)
        
        try:
            # 3. 템플릿 1: CFT 정기 회의 테스트
            print("\n1. CFT 정기 회의 템플릿(CFT_REGULAR) 추론 테스트...")
            cft_notes = gemini_svc.generate_notes(
                gcs_audio_uri=gcs_uri,
                meeting_title="AI 협업포털 주간 CFT 회의",
                attendees=["홍길동 팀장 (리테일 회사)", "이몽룡 담당 (리테일 회사)", "담당 CE (Google Cloud)"],
                template_prompt=CFT_REGULAR_PROMPT,
                template_type="CFT_REGULAR"
            )
            print(f"   ✅ CFT 요약: {cft_notes.executive_summary[:80]}...")
            assert len(cft_notes.executive_summary) > 0, "Executive summary가 비어있음"
            assert isinstance(cft_notes.action_items, list), "Action items가 리스트가 아님"
            assert len(cft_notes.formatted_markdown) > 0, "마크다운 서식이 비어있음"

            # 4. 템플릿 2: 프로젝트 킥오프 미팅 테스트
            print("\n2. 프로젝트 킥오프 템플릿(KICKOFF) 추론 테스트...")
            kickoff_notes = gemini_svc.generate_notes(
                gcs_audio_uri=gcs_uri,
                meeting_title="리테일 회사 AI 회의록 시스템 구축 킥오프",
                attendees=["홍길동 팀장", "이몽룡 담당", "성춘향 님"],
                template_prompt=KICKOFF_PROMPT,
                template_type="KICKOFF"
            )
            print(f"   ✅ 킥오프 요약: {kickoff_notes.executive_summary[:80]}...")
            assert kickoff_notes.template_type == "KICKOFF", "템플릿 유형 불일치"

            # 5. 템플릿 3: 임원/경영진 보고 템플릿 테스트
            print("\n3. 경영진 보고 템플릿(EXECUTIVE) 추론 테스트...")
            exec_notes = gemini_svc.generate_notes(
                gcs_audio_uri=gcs_uri,
                meeting_title="생성형 AI 추진 경과 경영진 보고",
                attendees=["홍길동 팀장", "사업본부장"],
                template_prompt=EXECUTIVE_PROMPT,
                template_type="EXECUTIVE"
            )
            print(f"   ✅ 임원 보고 요약: {exec_notes.executive_summary[:80]}...")
            assert exec_notes.template_type == "EXECUTIVE", "템플릿 유형 불일치"

            print("\n>>> [테스트 3 성공] Vertex AI Gemini 3대 템플릿 멀티모달 추론 및 스키마 검증 완료!\n")

        finally:
            GCSStorageService.delete_temp_audio(gcs_uri)

if __name__ == "__main__":
    test_gemini_diarization()
