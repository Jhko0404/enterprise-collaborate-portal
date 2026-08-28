import os
import sys
import subprocess
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.audio_service import AudioService
from app.core.exceptions import AudioProcessingError

def test_audio_transcoding():
    print("=== [테스트 1: 오디오 전처리 및 ffmpeg 트랜스코딩 테스트] ===")
    
    with AudioService.managed_temp_dir() as temp_dir:
        dummy_video = os.path.join(temp_dir, "test_meeting.mp4")
        output_wav = os.path.join(temp_dir, "extracted_meeting.wav")
        
        # 1. 5초 분량의 테스트 비디오 생성 (AAC 오디오 포함)
        print("1. 테스트용 MP4 비디오 생성 중...")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=5:size=640x360:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=5",
            "-c:v", "libx264", "-c:a", "aac",
            dummy_video
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert os.path.exists(dummy_video), "테스트 비디오 생성 실패"
        print(f"   ✅ 테스트 비디오 생성 완료: {os.path.getsize(dummy_video)} bytes")

        # 2. AudioService를 통한 16kHz Mono 16-bit PCM WAV 추출
        print("2. AudioService.extract_audio() 실행...")
        result_path = AudioService.extract_audio(dummy_video, output_wav)
        assert os.path.exists(result_path), "추출된 WAV 파일이 존재하지 않음"
        
        # 3. 추출된 WAV 파일의 오디오 헤더 스펙 정밀 검증
        with wave.open(result_path, "rb") as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            duration = n_frames / float(framerate)

        print(f"3. WAV 스펙 검증:")
        print(f"   - 채널 수: {channels} (기대값: 1 Mono)")
        print(f"   - 샘플링 레이트: {framerate} Hz (기대값: 16000 Hz)")
        print(f"   - 샘플 너비: {sample_width * 8} bits (기대값: 16 bits)")
        print(f"   - 오디오 길이: {duration:.2f} 초 (기대값: ~5.0 초)")

        assert channels == 1, f"채널 수 불일치: {channels}"
        assert framerate == 16000, f"샘플링 레이트 불일치: {framerate}"
        assert sample_width == 2, f"샘플 너비 불일치 (16-bit 필요): {sample_width}"
        assert 4.9 <= duration <= 5.2, f"오디오 길이 불일치: {duration}"

    # 4. 임시 디렉토리 자동 삭제(Cleanup) 검증
    assert not os.path.exists(temp_dir), "임시 디렉토리가 정상적으로 삭제되지 않음"
    print("4. 임시 디렉토리 자동 삭제(Cleanup) 검증: 통과 (디렉토리 자동 소멸 확인)")
    print(">>> [테스트 1 성공] 오디오 트랜스코딩 및 메모리/디스크 관리 검증 완료!\n")

if __name__ == "__main__":
    test_audio_transcoding()
