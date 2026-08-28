import os
import subprocess
import tempfile
import shutil
from typing import Generator
from contextlib import contextmanager
from app.core.config import settings
from app.core.exceptions import AudioProcessingError

class AudioService:
    @staticmethod
    def create_temp_dir(prefix: str = "meet_notes_") -> str:
        """독립적인 임시 작업 디렉토리 생성"""
        return tempfile.mkdtemp(prefix=prefix)

    @staticmethod
    @contextmanager
    def managed_temp_dir() -> Generator[str, None, None]:
        """자동 삭제되는 안전한 임시 작업 디렉토리 컨텍스트"""
        temp_dir = tempfile.mkdtemp(prefix="meet_notes_")
        try:
            yield temp_dir
        finally:
            if settings.TEMP_DIR_CLEANUP and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def extract_audio(input_media_path: str, output_audio_path: str) -> str:
        """
        ffmpeg 서브프로세스를 호출하여 16kHz Mono 오디오 스트림 추출
        - 출력 확장자가 .mp3인 경우 고압축 __LSI 수행사P3LAME__ (64kbps)
        - 출력 확장자가 .wav인 경우 16-bit PCM WAV
        """
        ext = os.path.splitext(output_audio_path)[1].lower()
        if ext == ".mp3":
            cmd = [
                "ffmpeg", "-y",
                "-i", input_media_path,
                "-vn",
                "-acodec", "__LSI 수행사P3LAME__",
                "-b:a", "64k",
                "-ar", str(settings.AUDIO_SAMPLE_RATE),
                "-ac", str(settings.AUDIO_CHANNELS),
                output_audio_path
            ]
        elif ext in [".m4a", ".aac"]:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_media_path,
                "-vn",
                "-acodec", "aac",
                "-b:a", "64k",
                "-ar", str(settings.AUDIO_SAMPLE_RATE),
                "-ac", str(settings.AUDIO_CHANNELS),
                output_audio_path
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_media_path,
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", str(settings.AUDIO_SAMPLE_RATE),
                "-ac", str(settings.AUDIO_CHANNELS),
                output_audio_path
            ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
                raise AudioProcessingError("추출된 오디오 파일이 비어있거나 생성되지 않았습니다.")
            return output_audio_path
        except subprocess.CalledProcessError as e:
            raise AudioProcessingError(f"ffmpeg 오디오 변환 실패: {e.stderr.decode('utf-8')}")
        except FileNotFoundError:
            raise AudioProcessingError("시스템에 'ffmpeg'가 설치되어 있지 않습니다. brew install ffmpeg을 실행하십시오.")

    @staticmethod
    def get_duration(media_path: str) -> float:
        """ffprobe를 사용하여 미디어 파일의 총 재생 시간(초)을 측정"""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            media_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
            return float(res.stdout.strip())
        except Exception as e:
            raise AudioProcessingError(f"미디어 재생 시간 분석 실패: {e}")

    @staticmethod
    def split_into_chunks(audio_path: str, output_dir: str, chunk_seconds: int = 900) -> list:
        """
        장시간 오디오를 일정 시간(기본 15분/900초) 단위로 분할하여 (파일경로, 시작초, 길이) 튜플 리스트 반환
        - 15분(900초) 윈도우는 Gemini 3.7 Flash의 JAILBREAK 오탐을 방지하고 높은 타임스탬프 정밀도를 제공합니다.
        """
        total_duration = AudioService.get_duration(audio_path)
        chunks = []
        start = 0
        chunk_idx = 1

        while start < total_duration:
            duration = min(chunk_seconds, total_duration - start)
            chunk_filename = os.path.join(output_dir, f"chunk_{chunk_idx:02d}_{int(start)}s.mp3")
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(start),
                "-t", str(duration),
                "-i", audio_path,
                "-acodec", "__LSI 수행사P3LAME__",
                "-b:a", "64k",
                "-ar", str(settings.AUDIO_SAMPLE_RATE),
                "-ac", str(settings.AUDIO_CHANNELS),
                chunk_filename
            ]
            try:
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                chunks.append((chunk_filename, int(start), float(duration)))
            except subprocess.CalledProcessError as e:
                raise AudioProcessingError(f"오디오 청크 분할 실패 ({chunk_idx}): {e.stderr.decode('utf-8')}")

            start += chunk_seconds
            chunk_idx += 1

        return chunks
