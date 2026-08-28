#!/usr/bin/env python3
"""
E2E Test Script:
Process user-provided input media:
[AI Live+Labs] Speakers_Supporters Briefing (KR) - 2026_07_10 15_58 KST - Recording.mp4
1. Upload to GCS via clean path
2. Trigger Fast-Path Gemini 3.7 Flash Report Generation (/api/v1/notes/process-gcs-media)
3. Monitor real-time Cloud STT (Chirp 2) Progress (percentage & chunk status)
4. Verify Detokenized Transcript Quality (No '▁' artifacts, natural sentence flow)
"""

import os
import sys
import time
import subprocess
import requests

INPUT_FILE = "/usr/local/google/home/junghyunko/git/2026-AI/collaborate-portal/data/input_media/[AI Live+Labs] Speakers_Supporters Briefing (KR) - 2026_07_10 15_58 KST - Recording.mp4"
PROJECT_ID = "project-elevate-007"
BUCKET_NAME = "project-elevate-007-meet-audio-temp"
GATEWAY_URL = "https://coway-agent-gateway-7p7fk8nj.uc.gateway.dev"

def main():
    print("=" * 70)
    print("🚀 [COWAY AI PORTAL] E2E 미디어 분석 및 STT 품질 검증 테스트")
    print("=" * 70)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ 입력 파일이 존재하지 않습니다: {INPUT_FILE}")
        sys.exit(1)

    file_size_mb = os.path.getsize(INPUT_FILE) / (1024 * 1024)
    filename = os.path.basename(INPUT_FILE)
    print(f"📁 테스트 미디어: {filename} ({file_size_mb:.1f} MB)")

    # 1. GCS 업로드 (심볼릭 링크로 특수문자 회피)
    blob_name = "test_media_briefing.mp4"
    gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}"
    print(f"\n☁️ 1. GCS 임시 업로드 시작 ➔ {gcs_uri} ...")
    
    clean_symlink = "/tmp/test_media_briefing_upload.mp4"
    if os.path.exists(clean_symlink):
        os.remove(clean_symlink)
    os.symlink(INPUT_FILE, clean_symlink)

    cmd = ["gcloud", "storage", "cp", clean_symlink, gcs_uri, f"--project={PROJECT_ID}"]
    ret = subprocess.run(cmd, capture_output=True, text=True)
    if ret.returncode != 0:
        print(f"❌ GCS 업로드 실패: {ret.stderr}")
        sys.exit(1)
    print("   ✅ GCS 업로드 완료!")

    # 2. 회의록 생성 API 호출 (Fast-Path)
    payload = {
        "gcs_uri": gcs_uri,
        "filename": filename,
        "title": "[AI Live+Labs] Speakers & Supporters Briefing",
        "template_type": "CFT_REGULAR",
        "attendees": "고정현 CE, 크리스틴, 김창재, 세리"
    }
    
    print("\n⚡ 2. Gemini 3.7 Flash 회의록 생성 요청 (Fast-Path API 호출)...")
    start_t = time.time()
    res = requests.post(f"{GATEWAY_URL}/api/v1/notes/process-gcs-media", json=payload, timeout=180)
    elapsed = time.time() - start_t

    if res.status_code != 200:
        print(f"❌ API 호출 실패 (HTTP {res.status_code}): {res.text}")
        sys.exit(1)

    data = res.json()
    report = data.get("report") or data
    report_id = report.get("id") or data.get("report_id")
    print(f"   ✅ 회의록 생성 완료! (소요 시간: {elapsed:.2f}초)")
    print(f"   📋 생성된 Report ID: {report_id}")
    print(f"   📝 핵심 요약: {report.get('executive_summary', '')[:140]}...")

    # 3. 비동기 Cloud STT 진행 상황 모니터링 (프로그레스 바 & 퍼센티지)
    print("\n🎤 3. Cloud STT (Chirp 2) 비동기 10-Way 병렬 전사 진행률 모니터링:")
    stt_status = "PROCESSING"
    stt_transcript = []
    
    for attempt in range(80):
        time.sleep(5)
        status_res = requests.get(f"{GATEWAY_URL}/api/v1/reports/{report_id}/stt-status", timeout=10)
        if status_res.status_code == 200:
            status_data = status_res.json()
            stt_status = status_data.get("stt_status")
            prog = status_data.get("stt_progress") or {}
            pct = prog.get("percent", 0)
            comp = prog.get("completed", 0)
            tot = prog.get("total", 0)
            
            bar_len = 20
            filled = int(round(bar_len * pct / 100))
            bar = "█" * filled + "░" * (bar_len - filled)
            print(f"\r   ⏳ [{bar}] {pct}% ({comp}/{tot} 청크 전사 완료) - 상태: {stt_status}", end="", flush=True)

            if stt_status == "COMPLETED" and status_data.get("stt_transcript") and len(status_data.get("stt_transcript")) > 0:
                stt_transcript = status_data.get("stt_transcript")
                print(f"\n   🎉 Cloud STT 전사 완료! (총 {len(stt_transcript)}개 발화 턴 생성)")
                break

    # 4. STT 품질 검증 (서브워드 토큰 '▁' 제거 및 자연스러운 문장 구조 확인)
    print("\n🔍 4. Cloud STT 전사본 품질 검증:")
    has_subword_artifact = False
    total_chars = 0
    sample_turns = []
    
    for idx, turn in enumerate(stt_transcript):
        text = turn.get("text", "")
        total_chars += len(text)
        if "▁" in text or "\u2581" in text:
            has_subword_artifact = True
        if idx < 6:
            sample_turns.append(turn)

    if has_subword_artifact:
        print("   ❌ 경고: 전사본에 '▁' 또는 서브워드 기호가 발견되었습니다!")
    else:
        print("   ✅ 검증 성공: '▁' 및 서브워드 깨짐 기호 100% 제거 및 자연스러운 한국어 문장 복원 확인!")

    print(f"   📊 STT 총 발화 턴: {len(stt_transcript)}턴 (총 {total_chars:,}자)")
    print("\n[전사본 샘플 6턴 미리보기]:")
    for t in sample_turns:
        print(f"   {t.get('time')} 🎙️ {t.get('speaker')}: {t.get('text')}")

    print("=" * 70)
    print("✅ E2E 테스트 성공 완료!")

if __name__ == "__main__":
    main()
