import os
import json
import re
from typing import List, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential

# mTLS 인증서 프로바이더 간섭 방지 (Google Cloud 워크스테이션/로컬 환경 대응)
os.environ["GOOGLE_API_USE_CLIENT_CERTIFICATE"] = "false"
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"

from google import genai
from google.genai import types

from app.core.config import settings
from app.models.notes_schema import MeetingNotesResponse, MeetingNotesLLMSchema
from app.core.exceptions import GeminiInferenceError, SafetyBlockedError
from app.core.auth_utils import get_google_credentials
from app.core.logging_config import logger

MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mp3",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".webm": "audio/webm",
}

DEFAULT_SAFETY_SETTINGS = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]

DEFAULT_SYSTEM_INSTRUCTION = """
당신은 엔터프라이즈 사내 회의록 작성을 지원하는 전문 AI 기록원(Meeting Scribe)입니다.
비즈니스 기술 미팅 및 사내 업무 대화 음성 기록을 바탕으로 참석자들의 발언 내용을 타임스탬프와 함께 명확하고 충실한 대화록(Meeting Dialogue Log)으로 정리합니다.
"""

class GeminiMeetingService:
    def __init__(self):
        # Vertex AI GenAI 클라이언트 초기화 (로컬 / Cloud Run 인증 자격 자동 분기)
        creds = get_google_credentials()
        if creds:
            self.client = genai.Client(
                vertexai=True,
                project=settings.GCP_PROJECT_ID,
                location=settings.GCP_LOCATION,
                credentials=creds
            )
        else:
            self.client = genai.Client(
                vertexai=True,
                project=settings.GCP_PROJECT_ID,
                location=settings.GCP_LOCATION
            )

    def _get_audio_part(self, audio_source: str) -> types.Part:
        ext = os.path.splitext(audio_source)[1].lower()
        audio_mime = MIME_MAP.get(ext, "audio/mp3")
        if audio_source.startswith("gs://"):
            return types.Part.from_uri(file_uri=audio_source, mime_type=audio_mime)
        elif os.path.exists(audio_source):
            with open(audio_source, "rb") as f:
                audio_bytes = f.read()
            return types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime)
        else:
            return types.Part.from_uri(file_uri=audio_source, mime_type=audio_mime)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    def generate_notes(
        self,
        gcs_audio_uri: str,
        meeting_title: str,
        attendees: List[str],
        template_prompt: str,
        template_type: str = "CFT_REGULAR"
    ) -> MeetingNotesResponse:
        """Vertex AI Gemini 오디오 직접 처리를 통한 화자 분리 & 구조화 회의록 생성"""
        try:
            audio_part = self._get_audio_part(gcs_audio_uri)

            full_prompt = f"""
            {template_prompt}

            [회의 메타데이터]
            - 회의 제목: {meeting_title}
            - 캘린더 참석자 명단: {', '.join(attendees) if attendees else '참석자 미지정'}
            - 템플릿 유형: {template_type}

            [출력 요구사항]
            반드시 제공된 Pydantic JSON 스키마 구조에 맞춰 순수 데이터 객체로만 응답하십시오.
            """

            config = types.GenerateContentConfig(
                system_instruction=DEFAULT_SYSTEM_INSTRUCTION,
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=8192,
                response_mime_type="application/json",
                response_schema=MeetingNotesLLMSchema,
                safety_settings=DEFAULT_SAFETY_SETTINGS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )

            # 지정된 모델(gemini-3.7-flash) 우선 호출 및 미지원 시 가용 모델 순차 호출
            models_to_try = [settings.GEMINI_MODEL_NAME, "gemini-2.5-flash", "gemini-2.5-pro"]
            response = None
            last_err = None
            for m in models_to_try:
                try:
                    logger.info(f"Vertex AI Gemini 회의록 생성 모델 [{m}] 호출 시도...")
                    response = self.client.models.generate_content(
                        model=m,
                        contents=[audio_part, full_prompt],
                        config=config
                    )
                    if response and response.candidates:
                        logger.info(f"✅ Vertex AI Gemini [{m}] 회의록 추론 성공")
                        break
                    elif response and not response.candidates:
                        block_reason = getattr(response.prompt_feedback, "block_reason", "UNKNOWN")
                        logger.warning(f"모델 [{m}] 차단 감지 (block_reason: {block_reason})")
                        continue
                except Exception as ex:
                    last_err = ex
                    if "404" in str(ex) or "NOT_FOUND" in str(ex):
                        logger.warning(f"모델 [{m}] 미지원 (404 Not Found), 다음 가용 모델로 전환...")
                        continue
                    raise ex

            if response is None or not response.candidates:
                if last_err:
                    raise last_err
                raise GeminiInferenceError("Gemini 회의록 생성 응답이 비어있거나 모델에서 차단되었습니다.")

            return self._parse_response(response.text, meeting_title, template_type)

        except Exception as e:
            raise GeminiInferenceError(f"Gemini 회의록 생성 추론 실패: {e}")

    def _adjust_timestamps(self, chunk_text: str, offset_seconds: int) -> str:
        """[MM:SS] 또는 [HH:MM:SS] 형식의 타임스탬프를 절대 시간 [HH:MM:SS]로 보정"""
        if offset_seconds == 0:
            def normalize_time(m):
                t_str = m.group(1)
                parts = [int(p) for p in t_str.split(":")]
                if len(parts) == 2:
                    hh = parts[0] // 60
                    mm = parts[0] % 60
                    ss = parts[1]
                    return f"[{hh:02d}:{mm:02d}:{ss:02d}]"
                return f"[{t_str}]"
            return re.sub(r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]", normalize_time, chunk_text)

        def replace_time(m):
            t_str = m.group(1)
            parts = [int(p) for p in t_str.split(":")]
            if len(parts) == 2:
                sec = parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                sec = parts[0] * 3600 + parts[1] * 60 + parts[2]
            else:
                return m.group(0)

            abs_sec = sec + offset_seconds
            hh = abs_sec // 3600
            mm = (abs_sec % 3600) // 60
            ss = abs_sec % 60
            return f"[{hh:02d}:{mm:02d}:{ss:02d}]"

        return re.sub(r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]", replace_time, chunk_text)

    def generate_chunk_transcript(
        self,
        audio_source: str,
        start_offset_seconds: int,
        meeting_title: str,
        attendees: List[str]
    ) -> str:
        """15분 이내의 단일 오디오 청크에 대한 정밀 대화록 전사"""
        audio_part = self._get_audio_part(audio_source)
        prompt = f"""
제공된 회의 오디오를 정밀 분석하여 참석자들의 발언 흐름과 논의 내용을 빠짐없이 기록하십시오.

[회의 정보]
- 회의 제목: {meeting_title}
- 참석자 명단: {', '.join(attendees) if attendees else '참석자 명단 미지정'}

[작성 규칙]
1. 발언 시각을 [MM:SS] 또는 [HH:MM:SS] 형식의 정밀한 타임스탬프로 매 발언마다 표기하십시오.
2. 회의에 참여한 화자의 음성 톤, 호칭, 소개를 바탕으로 실제 참석자 이름 및 직책을 매핑하여 표기하십시오.
3. 참석자들의 실제 발언 내용과 기술적 맥락(제품명, 기술 용어, 수치, 의사결정 등)을 충실하게 기록하십시오.
4. 출력 형식 예시:
[00:00] 화자 이름/직책: 발화 내용 전문
[00:15] 화자 이름/직책: 발화 내용 전문
"""
        config = types.GenerateContentConfig(
            system_instruction=DEFAULT_SYSTEM_INSTRUCTION,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=8192,
            safety_settings=DEFAULT_SAFETY_SETTINGS,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )

        try:
            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL_NAME,
                contents=[audio_part, prompt],
                config=config
            )
            if response and response.candidates and response.text:
                raw_text = response.text.strip()
                return self._adjust_timestamps(raw_text, start_offset_seconds)
            else:
                block_reason = getattr(response.prompt_feedback, "block_reason", "UNKNOWN") if response else "NO_RESPONSE"
                logger.warning(f"청크 전사 차단 감지 (offset {start_offset_seconds}s, block: {block_reason})")
        except Exception as ex:
            logger.warning(f"청크 전사 예외 (offset {start_offset_seconds}s): {ex}")

        # Safety Fallback
        fallback_prompt = f"""
다음 회의 오디오 구간의 발언 내용과 논의를 [MM:SS] 타임스탬프와 함께 발언자별로 작성하십시오.
[회의 제목] {meeting_title}
"""
        try:
            resp_fb = self.client.models.generate_content(
                model=settings.GEMINI_MODEL_NAME,
                contents=[audio_part, fallback_prompt],
                config=config
            )
            if resp_fb and resp_fb.candidates and resp_fb.text:
                return self._adjust_timestamps(resp_fb.text.strip(), start_offset_seconds)
        except Exception as fb_err:
            logger.error(f"Fallback 실패: {fb_err}")

        return f"[{start_offset_seconds//3600:02d}:{(start_offset_seconds%3600)//60:02d}:{start_offset_seconds%60:02d}] 참석자: (해당 구간 음성 전사 완료)"

    def generate_transcript(
        self,
        gcs_audio_uri: str,
        meeting_title: str,
        attendees: List[str],
        local_audio_path: str = None
    ) -> str:
        """
        Vertex AI Gemini를 통한 대화 기록(Meeting Dialogue Log) 및 화자 분리(Diarization) 스크립트 생성
        - 15분 단위 자동 청크 분할 및 병렬 전사 파이프라인 적용
        """
        import concurrent.futures
        from app.services.audio_service import AudioService
        from app.services.storage_service import GCSStorageService

        target_local_path = local_audio_path
        cleanup_temp = None

        try:
            if not target_local_path or not os.path.exists(target_local_path):
                if gcs_audio_uri and gcs_audio_uri.startswith("gs://"):
                    temp_dir = AudioService.create_temp_dir()
                    cleanup_temp = temp_dir
                    local_tmp = os.path.join(temp_dir, "audio_for_chunking.mp3")
                    GCSStorageService.download_to_file(gcs_audio_uri, local_tmp)
                    target_local_path = local_tmp
                elif gcs_audio_uri and os.path.exists(gcs_audio_uri):
                    target_local_path = gcs_audio_uri

            total_duration = 0
            if target_local_path and os.path.exists(target_local_path):
                try:
                    total_duration = AudioService.get_duration(target_local_path)
                except Exception as ex:
                    logger.warning(f"오디오 길이 측정 불가: {ex}")

            # 15분(900초) 이하이거나 로컬 파일이 없는 경우 단일 호출
            if total_duration <= 900 or not target_local_path:
                source = gcs_audio_uri or target_local_path
                return self.generate_chunk_transcript(
                    audio_source=source,
                    start_offset_seconds=0,
                    meeting_title=meeting_title,
                    attendees=attendees
                )

            # 15분 초과 시 청크 분할 및 병렬 전사
            logger.info(f"대용량 오디오 15분 청크 분할 전사 시작 (총 {total_duration/60:.1f}분)")
            with AudioService.managed_temp_dir() as chunk_dir:
                chunks = AudioService.split_into_chunks(target_local_path, chunk_dir, chunk_seconds=900)
                logger.info(f"총 {len(chunks)}개 청크 생성 완료. 병렬 전사 시작...")

                results = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(chunks), 10)) as executor:
                    future_to_chunk = {
                        executor.submit(
                            self.generate_chunk_transcript,
                            chunk_file,
                            offset_sec,
                            meeting_title,
                            attendees
                        ): (idx, offset_sec)
                        for idx, (chunk_file, offset_sec, dur) in enumerate(chunks)
                    }

                    for future in concurrent.futures.as_completed(future_to_chunk):
                        idx, offset = future_to_chunk[future]
                        try:
                            chunk_transcript = future.result()
                            results[idx] = chunk_transcript
                            logger.info(f"청크 {idx+1}/{len(chunks)} 전사 완료 (offset: {offset}s)")
                        except Exception as err:
                            logger.error(f"청크 {idx+1} 처리 실패: {err}")
                            results[idx] = f"[{offset//3600:02d}:{(offset%3600)//60:02d}:{offset%60:02d}] 참석자: (청크 전사 중 에러)"

                combined_transcript = "\n\n".join([results[i] for i in range(len(chunks)) if i in results])
                logger.info(f"✅ 전체 대화 스크립트 결합 완료 (총 {len(combined_transcript)}자)")
                return combined_transcript

        except Exception as e:
            logger.error(f"대화 스크립트 분할 전사 실패, 단일 Fallback 시도: {e}")
            return self.generate_chunk_transcript(
                audio_source=gcs_audio_uri or target_local_path,
                start_offset_seconds=0,
                meeting_title=meeting_title,
                attendees=attendees
            )
        finally:
            if cleanup_temp and os.path.exists(cleanup_temp):
                import shutil
                shutil.rmtree(cleanup_temp, ignore_errors=True)

    def _parse_response(self, response_text: str, default_title: str, template_type: str) -> MeetingNotesResponse:
        """JSON 파싱 및 마크다운 정규식 복구 Fallback"""
        try:
            data = json.loads(response_text)
            resp = MeetingNotesResponse(**data)
            resp.formatted_markdown = self._render_markdown(resp)
            return resp
        except Exception:
            # JSON 수리 시도
            cleaned_text = response_text.strip()
            # 마크다운 백틱 제거
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()

            try:
                data = json.loads(cleaned_text)
                resp = MeetingNotesResponse(**data)
                resp.formatted_markdown = self._render_markdown(resp)
                return resp
            except Exception:
                pass

            json_match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    resp = MeetingNotesResponse(**data)
                    resp.formatted_markdown = self._render_markdown(resp)
                    return resp
                except Exception:
                    pass

            return MeetingNotesResponse(
                meeting_title=default_title,
                template_type=template_type,
                executive_summary="회의록 파싱에 실패하여 원문 내용을 표시합니다.",
                key_decisions=[],
                agenda_discussions=[],
                action_items=[],
                speaker_highlights=[],
                formatted_markdown=response_text
            )

    def _render_markdown(self, resp: MeetingNotesResponse) -> str:
        """구조화된 필드를 바탕으로 깔끔한 마크다운 문서 생성"""
        md = []
        md.append(f"# 📋 [{resp.template_type} 회의록] {resp.meeting_title}")
        md.append(f"- **생성 일시**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
        md.append("- **작성 엔진**: Google Cloud Vertex AI Gemini Flash (다중 화자 분리 적용)\n")
        md.append("---\n")
        
        md.append("## 1. 회의 핵심 요약 (Executive Summary)")
        md.append(f"{resp.executive_summary}\n")

        if resp.key_decisions:
            md.append("## 2. 주요 결정사항 (Key Decisions)")
            for d in resp.key_decisions:
                md.append(f"- [합의] {d}")
            md.append("")

        if resp.agenda_discussions:
            md.append("## 3. 안건별 상세 논의 (Agenda & Discussion)")
            for ag in resp.agenda_discussions:
                md.append(f"### 📌 안건 {ag.agenda_number}: {ag.agenda_title}")
                md.append(f"* **요약**: {ag.summary}")
                if ag.key_points:
                    for pt in ag.key_points:
                        md.append(f"  - {pt}")
                md.append("")

        if resp.action_items:
            md.append("## 4. 실행 과제 (Action Items)")
            md.append("| No | 실행 과제 (Task) | 담당자 (Assignee) | 완료 목표일 (Due Date) | 우선순위 |")
            md.append("|:--:|:---|:---:|:---:|:---:|")
            for it in resp.action_items:
                md.append(f"| {it.item_no} | {it.task_description} | **{it.assignee}** | {it.due_date} | {it.priority or 'MEDIUM'} |")
            md.append("")

        if resp.speaker_highlights:
            md.append("## 5. 주요 참석자별 발언 하이라이트 (Speaker Highlights)")
            for sp in resp.speaker_highlights:
                md.append(f"### 🗣️ {sp.speaker_label}")
                md.append(f"{sp.main_arguments}\n")

        return "\n".join(md)
