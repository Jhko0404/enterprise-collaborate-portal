import os
import re
import concurrent.futures
from typing import List, Dict, Any, Optional, Callable
from app.core.config import settings
from app.core.auth_utils import get_google_credentials
from app.core.logging_config import logger

try:
    from google.cloud import speech_v1p1beta1 as speech
except ImportError:
    try:
        from google.cloud import speech
    except ImportError:
        speech = None

class CloudSTTService:
    """
    Google Cloud Speech-to-Text API 서비스
    - 화자 분리(Speaker Diarization) 및 100% 음향 기반 축어(Verbatim) 전사 제공
    - 15분 단위 자동 청크 분할 및 고속 병렬 전사 지원 (대용량 128분 음원 타임아웃 해소)
    """

    def __init__(self):
        self.client = None
        if speech:
            try:
                creds = get_google_credentials()
                if creds:
                    self.client = speech.SpeechClient(credentials=creds)
                else:
                    self.client = speech.SpeechClient()
            except Exception as e:
                logger.warning(f"Cloud STT 클라이언트 초기화 실패 (Fallback 지원): {e}")

    def _adjust_timestamps(self, turns: List[Dict[str, str]], offset_seconds: int) -> List[Dict[str, str]]:
        """청크 로컬 타임스탬프를 절대 타임스탬프[HH:MM:SS]로 변환"""
        if offset_seconds == 0:
            return turns

        time_pat = re.compile(r"\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]")
        adjusted_turns = []
        for t in turns:
            raw_time = t.get("time", "[00:00:00]")
            m = time_pat.search(raw_time)
            if m:
                if m.group(3) is not None:
                    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    total_s = h * 3600 + mi * 60 + s
                else:
                    mi, s = int(m.group(1)), int(m.group(2))
                    total_s = mi * 60 + s
                
                abs_s = total_s + offset_seconds
                nh = abs_s // 3600
                nmi = (abs_s % 3600) // 60
                ns = abs_s % 60
                new_time = f"[{nh:02d}:{nmi:02d}:{ns:02d}]"
            else:
                new_time = raw_time

            adjusted_turns.append({
                "time": new_time,
                "speaker": t.get("speaker", "Speaker"),
                "text": t.get("text", "")
            })
        return adjusted_turns

    def transcribe_single_chunk(self, audio_path: str, offset_seconds: int = 0) -> List[Dict[str, str]]:
        """15분 이내의 단일 오디오 파일 전사 (GCS 임시 업로드 후 LongRunningRecognize 호출)"""
        from app.services.storage_service import GCSStorageService
        if not speech or not self.client:
            return []

        uploaded_gcs_uri = None
        try:
            if audio_path.startswith("gs://"):
                audio_uri = audio_path
            else:
                uploaded_gcs_uri = GCSStorageService.upload_temp_audio(audio_path)
                audio_uri = uploaded_gcs_uri

            audio = speech.RecognitionAudio(uri=audio_uri)
            diarization_config = speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=2,
                max_speaker_count=8,
            )

            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                sample_rate_hertz=16000,
                language_code="ko-KR",
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                diarization_config=diarization_config,
                model="latest_long"
            )

            operation = self.client.long_running_recognize(config=config, audio=audio)
            response = operation.result(timeout=180)
            turns = self._parse_diarization_response(response)
            return self._adjust_timestamps(turns, offset_seconds)
        except Exception as ex:
            logger.warning(f"⚠️ [Cloud STT] 청크(offset {offset_seconds}s) 전사 예외: {ex}")
            return []
        finally:
            if uploaded_gcs_uri:
                GCSStorageService.delete_temp_audio(uploaded_gcs_uri)

    def transcribe_audio(
        self,
        local_audio_path: Optional[str] = None,
        gcs_audio_uri: Optional[str] = None,
        language_code: str = "ko-KR",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, str]]:
        """
        15분 단위 청크 분할 및 고속 병렬 Cloud STT 전사 파이프라인
        """
        from app.services.audio_service import AudioService
        from app.services.storage_service import GCSStorageService

        target_local_path = local_audio_path

        # 로컬 경로가 없고 GCS URI만 있는 경우 로컬 임시 다운로드
        temp_download_dir = None
        if not target_local_path and gcs_audio_uri and gcs_audio_uri.startswith("gs://"):
            try:
                temp_download_dir = AudioService.create_temp_dir()
                target_local_path = os.path.join(temp_download_dir, "temp_stt_input.mp3")
                GCSStorageService.download_to_file(gcs_audio_uri, target_local_path)
            except Exception as dl_err:
                logger.warning(f"Cloud STT용 GCS 다운로드 실패: {dl_err}")

        if not target_local_path or not os.path.exists(target_local_path):
            if progress_callback:
                progress_callback(1, 1)
            return self.transcribe_audio_gcs_fallback(gcs_audio_uri)

        try:
            duration = AudioService.get_duration(target_local_path)
            logger.info(f"🎤 [Cloud STT] 오디오 길이: {duration:.1f}초 ({duration/60:.1f}분)")

            # 15분(900초) 이하인 경우 단일 청크 처리
            if duration <= 900:
                if progress_callback:
                    progress_callback(0, 1)
                turns = self.transcribe_single_chunk(target_local_path, offset_seconds=0)
                if progress_callback:
                    progress_callback(1, 1)
                if turns:
                    return turns

            # 15분 초과 대용량 파일: 15분 단위로 자동 분할 후 병렬 전사
            with AudioService.managed_temp_dir() as chunk_dir:
                chunks = AudioService.split_into_chunks(target_local_path, chunk_dir, chunk_seconds=900)
                total_chunks = len(chunks)
                logger.info(f"🎤 [Cloud STT] 총 {total_chunks}개 청크 병렬 전사 시작 (동시 스레드: {total_chunks})...")
                
                if progress_callback:
                    progress_callback(0, total_chunks)

                results = [None] * total_chunks
                completed_count = 0
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(total_chunks, 10)) as executor:
                    future_to_idx = {
                        executor.submit(
                            self.transcribe_single_chunk,
                            chunk_file,
                            offset_sec
                        ): idx
                            for idx, (chunk_file, offset_sec, dur) in enumerate(chunks)
                    }

                    for future in concurrent.futures.as_completed(future_to_idx):
                        idx = future_to_idx[future]
                        try:
                            chunk_turns = future.result()
                            results[idx] = chunk_turns
                        except Exception as e:
                            logger.warning(f"Cloud STT 청크 {idx+1} 처리 실패: {e}")
                            results[idx] = []
                        finally:
                            completed_count += 1
                            if progress_callback:
                                progress_callback(completed_count, total_chunks)

                # 모든 청크 발화 턴 병합
                combined_turns = []
                for chunk_turns in results:
                    if chunk_turns:
                        combined_turns.extend(chunk_turns)

                if combined_turns:
                    logger.info(f"✅ [Cloud STT] 하이브리드 청크 병렬 전사 완료 (총 {len(combined_turns)}개 발화 턴)")
                    return combined_turns

        except Exception as ex:
            logger.warning(f"Cloud STT 청크 파이프라인 예외: {ex}")
        finally:
            if temp_download_dir and os.path.exists(temp_download_dir):
                import shutil
                shutil.rmtree(temp_download_dir, ignore_errors=True)

        return self.transcribe_audio_gcs_fallback(gcs_audio_uri)

    def transcribe_audio_gcs_fallback(self, gcs_audio_uri: Optional[str]) -> List[Dict[str, str]]:
        """단일 GCS URI 직접 호출 Fallback"""
        if not gcs_audio_uri or not speech or not self.client:
            return [
                {
                    "time": "[00:00:00]",
                    "speaker": "Cloud STT",
                    "text": "(Cloud Speech-to-Text 음향 전사 준비 완료)"
                }
            ]

        try:
            audio = speech.RecognitionAudio(uri=gcs_audio_uri)
            diarization_config = speech.SpeakerDiarizationConfig(
                enable_speaker_diarization=True,
                min_speaker_count=2,
                max_speaker_count=8,
            )
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                sample_rate_hertz=16000,
                language_code="ko-KR",
                enable_automatic_punctuation=True,
                enable_word_time_offsets=True,
                diarization_config=diarization_config,
                model="latest_long"
            )
            operation = self.client.long_running_recognize(config=config, audio=audio)
            response = operation.result(timeout=180)
            return self._parse_diarization_response(response)
        except Exception as ex:
            return [
                {
                    "time": "[00:00:00]",
                    "speaker": "Cloud STT",
                    "text": f"(Cloud Speech-to-Text 처리 안내: {str(ex)[:100]})"
                }
            ]

    @staticmethod
    def _clean_stt_tokens(tokens: List[str]) -> str:
        """
        Google Cloud Speech-to-Text (Chirp/SentencePiece) 서브워드 토큰(U+2581, ▁) 디토크나이징 및 자연스러운 한국어 문장 복원
        """
        if not tokens:
            return ""
        reconstructed = ""
        for w in tokens:
            if not w:
                continue
            # U+2581 ( ) 또는 ▁ 문자는 단어 시작(어절 경계)을 의미
            if w.startswith(" ") or w.startswith("\u2581") or w.startswith("▁"):
                clean_w = w.lstrip(" \u2581▁")
                reconstructed += (" " if reconstructed else "") + clean_w
            else:
                # 서브워드 결합 (예: '일단' + '은' -> '일단은')
                reconstructed += w
        
        # 텍스트 내 잔여 토큰 기호 정리 및 중복 공백 정제
        cleaned = re.sub(r"[ \u2581▁]+", " ", reconstructed)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _parse_diarization_response(self, response) -> List[Dict[str, str]]:
        """STT 응답에서 화자별 및 자연스러운 발화 단위 타임스탬프 발화 턴 추출"""
        turns = []
        if not response or not hasattr(response, "results") or not response.results:
            return turns

        result = response.results[-1]
        words_info = getattr(result.alternatives[0], "words", []) if result.alternatives else []

        if not words_info:
            for res in response.results:
                if res.alternatives:
                    alt = res.alternatives[0]
                    clean_text = self._clean_stt_tokens(alt.transcript.split()) if alt.transcript else ""
                    if clean_text:
                        turns.append({
                            "time": "[00:00:00]",
                            "speaker": "Speaker 1",
                            "text": clean_text
                        })
            return turns

        current_speaker = None
        current_tokens = []
        turn_start_time = 0.0
        last_end_time = 0.0

        for word_info in words_info:
            speaker_tag = getattr(word_info, "speaker_tag", 1)
            start_sec = word_info.start_time.total_seconds() if hasattr(word_info.start_time, "total_seconds") else 0.0
            end_sec = word_info.end_time.total_seconds() if hasattr(word_info.end_time, "total_seconds") else start_sec

            # 발화 턴 분할 조건:
            # 1. 화자 변경
            # 2. 2.5초 이상의 침묵/휴지(Pause)
            # 3. 120자 이상 누적되고 종결어미(. ? 요 다 죠 까) 도달 시
            speaker_changed = (current_speaker is not None and speaker_tag != current_speaker)
            pause_detected = (last_end_time > 0 and (start_sec - last_end_time) > 2.5)
            
            curr_text_preview = self._clean_stt_tokens(current_tokens)
            length_exceeded = len(curr_text_preview) > 100 and any(curr_text_preview.endswith(end) for end in [".", "?", "요", "다", "죠", "까", "습니다", "네요"])

            if speaker_changed or pause_detected or length_exceeded:
                if current_tokens and curr_text_preview:
                    hh = int(turn_start_time // 3600)
                    mm = int((turn_start_time % 3600) // 60)
                    ss = int(turn_start_time % 60)
                    turns.append({
                        "time": f"[{hh:02d}:{mm:02d}:{ss:02d}]",
                        "speaker": f"Speaker {current_speaker if current_speaker is not None else speaker_tag}",
                        "text": curr_text_preview
                    })
                current_speaker = speaker_tag
                turn_start_time = start_sec
                current_tokens = [word_info.word]
            else:
                if current_speaker is None:
                    current_speaker = speaker_tag
                    turn_start_time = start_sec
                current_tokens.append(word_info.word)

            last_end_time = end_sec

        if current_tokens:
            final_text = self._clean_stt_tokens(current_tokens)
            if final_text:
                hh = int(turn_start_time // 3600)
                mm = int((turn_start_time % 3600) // 60)
                ss = int(turn_start_time % 60)
                turns.append({
                    "time": f"[{hh:02d}:{mm:02d}:{ss:02d}]",
                    "speaker": f"Speaker {current_speaker if current_speaker is not None else 1}",
                    "text": final_text
                })

        return turns

stt_service = CloudSTTService()
