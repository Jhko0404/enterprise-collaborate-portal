#!/usr/bin/env python3
"""
회의록 및 비동기 Cloud STT 전사 진행 상황 실시간 진단 스크립트
사용법:
    python scripts/check_report_stt_progress.py [검색어 또는 Report ID]
예:
    python scripts/check_report_stt_progress.py 1a01e051462b19c76ae1
"""

import sys
import json
import subprocess
import requests

API_GATEWAY = "https://coway-agent-gateway-7p7fk8nj.uc.gateway.dev"

def check_progress(search_term=""):
    print("=" * 70)
    print("🔍 [COWAY AI PORTAL] 회의록 및 비동기 STT 진행 상황 실시간 진단")
    print("=" * 70)

    # 1. 보관함 전체 목록 조회
    try:
        res = requests.get(f"{API_GATEWAY}/api/v1/reports", timeout=15)
        if res.status_code != 200:
            print(f"❌ API Gateway 응답 실패: HTTP {res.status_code}")
            return
        data = res.json()
        reports = data.get("reports", [])
    except Exception as e:
        print(f"❌ API 호출 실패: {e}")
        return

    # 검색 대상 리포트 필터링
    matched_reports = []
    if search_term:
        term_clean = search_term.strip().lower()
        for r in reports:
            rid = str(r.get("id", "")).lower()
            title = str(r.get("title", "")).lower()
            if term_clean in rid or term_clean in title:
                matched_reports.append(r)
    else:
        matched_reports = reports[:3]

    if not matched_reports:
        print(f"⚠️ 검색어 '{search_term}'와 일치하는 회의록을 찾을 수 없습니다.")
        print(f"현재 보관함 총 회의록 수: {len(reports)}건")
        if reports:
            print("\n[최근 회의록 목록]")
            for idx, r in enumerate(reports[:5]):
                print(f"  {idx+1}. ID: {r.get('id')} | 제목: {r.get('title')} | STT: {r.get('stt_status', 'N/A')}")
        return

    for r in matched_reports:
        report_id = r.get("id")
        title = r.get("title")
        print(f"\n📋 [회의록 정보] ID: {report_id}")
        print(f"   - 회의 제목: {title}")
        print(f"   - 일시: {r.get('date')} {r.get('time')}")
        print(f"   - 템플릿: {r.get('template_name', r.get('template_type'))}")
        print(f"   - 오디오 소스: {r.get('audio_source', 'N/A')}")
        print(f"   - STT 상태: {r.get('stt_status', 'PROCESSING')}")

        # 2. 단건 상세 조회 (/api/v1/reports/{id})
        try:
            detail_res = requests.get(f"{API_GATEWAY}/api/v1/reports/{report_id}", timeout=15)
            if detail_res.status_code == 200:
                detail = detail_res.json()
                rep = detail.get("report") or detail.get("report_meta") or {}
                
                # Gemini 회의록 및 전사본 통계
                gemini_transcript = rep.get("transcript") or []
                if isinstance(gemini_transcript, str):
                    gemini_chars = len(gemini_transcript)
                    gemini_turns_count = len(gemini_transcript.split("\n\n"))
                else:
                    gemini_turns_count = len(gemini_transcript)
                    gemini_chars = sum(len(t.get("text", "")) for t in gemini_transcript)
                
                print(f"\n   ✨ [Vertex AI Gemini 3.7 Flash]")
                print(f"      - 회의 요약: {rep.get('executive_summary', '')[:80]}...")
                print(f"      - 핵심 결정사항: {len(rep.get('key_decisions', []))}개")
                print(f"      - 실행 과제(Action Items): {len(rep.get('action_items', []))}개")
                print(f"      - 전사 발화 턴: {gemini_turns_count}턴 (총 {gemini_chars:,}자) - [완료 ✅]")

                # Cloud STT 전사본 통계
                stt_transcript = rep.get("stt_transcript") or []
                stt_status = rep.get("stt_status", "PROCESSING")
                if isinstance(stt_transcript, str):
                    stt_chars = len(stt_transcript)
                    stt_turns_count = len(stt_transcript.split("\n\n"))
                else:
                    stt_turns_count = len(stt_transcript)
                    stt_chars = sum(len(t.get("text", "")) for t in stt_transcript)

                print(f"\n   🎤 [Cloud Speech-to-Text (Chirp 2)]")
                print(f"      - 실시간 상태: {stt_status}")
                print(f"      - 전사 발화 턴: {stt_turns_count}턴 (총 {stt_chars:,}자)")
                
                if stt_turns_count > 0:
                    print(f"      - 전사 샘플 (처음 2턴):")
                    sample_turns = stt_transcript[:2] if isinstance(stt_transcript, list) else []
                    for t in sample_turns:
                        print(f"        • {t.get('time', '')} {t.get('speaker', '')}: {t.get('text', '')[:60]}...")
                else:
                    print(f"      - 백그라운드 Worker 스레드에서 15분 단위 청크 병렬 전사 진행 중...")
        except Exception as ex:
            print(f"   ⚠️ 상세 정보 조회 중 예외: {ex}")

        # 3. /stt-status 전용 폴링 엔드포인트 테스트
        try:
            stt_res = requests.get(f"{API_GATEWAY}/api/v1/reports/{report_id}/stt-status", timeout=10)
            if stt_res.status_code == 200:
                stt_data = stt_res.json()
                print(f"\n   🔄 [STT 상태 폴링 API 응답 (/stt-status)]")
                print(f"      - stt_status: {stt_data.get('stt_status')}")
                print(f"      - stt_turns_count: {stt_data.get('stt_turns_count', len(stt_data.get('stt_transcript', [])))}")
        except Exception as ex:
            print(f"   ⚠️ /stt-status 조회 중 예외: {ex}")

    # 4. Cloud Run 실시간 로그 최근 10줄 확인
    print("\n" + "=" * 70)
    print("☁️ [Cloud Run 백엔드 최근 로그 (STT 관련)]")
    print("=" * 70)
    try:
        cmd = [
            "gcloud", "logging", "read",
            'resource.type="cloud_run_revision" AND resource.labels.service_name="coway-meet-notes-service"',
            "--limit=15",
            "--project=project-elevate-007",
            "--format=table(timestamp,textPayload)"
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        if res.returncode == 0 and res.stdout.strip():
            print(res.stdout)
        else:
            print("로그를 가져올 수 없거나 출력할 로그가 없습니다.")
    except Exception as ex:
        print(f"gcloud log 조회 생략: {ex}")

if __name__ == "__main__":
    search_arg = sys.argv[1] if len(sys.argv) > 1 else "1a01e051462b19c76ae1"
    check_progress(search_arg)
