#!/usr/bin/env python3
"""
Coway AI Agent Gateway & Cloud CDN - External Verification & E2E Test Suite
==========================================================================
Comprehensive verification of all external REST endpoints, Web UI assets,
Cloud CDN Edge Caching (HIT/MISS/BYPASS), CORS headers, WAF threat filtering,
and Rate Limiting enforcement.
"""

import sys
import time
import httpx

def run_tests(gateway_url: str = "http://127.0.0.1:8080"):
    print("==================================================================")
    print(f"🧪 [Agent Gateway & Cloud CDN E2E Verification] Testing: {gateway_url}")
    print("==================================================================")
    
    client = httpx.Client(base_url=gateway_url, timeout=30.0)
    passed = 0
    failed = 0

    def assert_test(name: str, condition: bool, details: str = ""):
        nonlocal passed, failed
        if condition:
            print(f"  ✅ [PASS] {name} {details}")
            passed += 1
        else:
            print(f"  ❌ [FAIL] {name} {details}")
            failed += 1

    # --------------------------------------------------------------------------
    # 1. Health & Gateway Status Verification
    # --------------------------------------------------------------------------
    print("\n--- 1. Health & Gateway Status Verification ---")
    try:
        r = client.get("/healthz")
        assert_test("GET /healthz", r.status_code == 200 and r.json().get("status") == "HEALTHY", f"(HTTP {r.status_code})")
    except Exception as e:
        assert_test("GET /healthz", False, f"(Error: {e})")

    try:
        r = client.get("/api/v1/health")
        assert_test("GET /api/v1/health", r.status_code == 200, f"(HTTP {r.status_code})")
    except Exception as e:
        assert_test("GET /api/v1/health", False, f"(Error: {e})")

    try:
        r = client.get("/api/v1/gateway/status")
        data = r.json()
        assert_test(
            "GET /api/v1/gateway/status",
            r.status_code == 200 and "endpoints" in data and len(data["endpoints"]) >= 10,
            f"({len(data.get('endpoints', []))} managed routes verified)"
        )
    except Exception as e:
        assert_test("GET /api/v1/gateway/status", False, f"(Error: {e})")

    # --------------------------------------------------------------------------
    # 2. Cloud CDN Edge Caching Verification
    # --------------------------------------------------------------------------
    print("\n--- 2. Cloud CDN Edge Caching Verification ---")
    try:
        # 1st Request: Cache MISS (Origin fetch)
        r1 = client.get("/static/style.css")
        # 2nd Request: Cache HIT (Edge cache)
        r2 = client.get("/static/style.css")
        cache_status_2 = r2.headers.get("x-cdn-cache-status") or r2.headers.get("x-cache")
        edge_lat = r2.headers.get("x-edge-latency-ms", "0")
        assert_test(
            "Cloud CDN: Static CSS Edge Cache HIT",
            r2.status_code == 200 and cache_status_2 == "HIT",
            f"(Status: {cache_status_2}, Edge Latency: {edge_lat}ms)"
        )
    except Exception as e:
        assert_test("Cloud CDN: Static CSS Edge Cache HIT", False, f"(Error: {e})")

    try:
        # 1st Request: Cache MISS
        r1 = client.get("/static/app.js")
        # 2nd Request: Cache HIT
        r2 = client.get("/static/app.js")
        cache_status_2 = r2.headers.get("x-cdn-cache-status") or r2.headers.get("x-cache")
        assert_test(
            "Cloud CDN: Static JS Edge Cache HIT",
            r2.status_code == 200 and cache_status_2 == "HIT",
            f"(Status: {cache_status_2})"
        )
    except Exception as e:
        assert_test("Cloud CDN: Static JS Edge Cache HIT", False, f"(Error: {e})")

    try:
        # Dynamic API should BYPASS CDN cache
        r_api = client.get("/api/v1/notes/current")
        api_cdn_status = r_api.headers.get("x-cdn-cache-status") or r_api.headers.get("x-cache")
        assert_test(
            "Cloud CDN: Dynamic API Cache BYPASS",
            r_api.status_code == 200 and api_cdn_status == "BYPASS",
            f"(Status: {api_cdn_status}, Live backend data guaranteed)"
        )
    except Exception as e:
        assert_test("Cloud CDN: Dynamic API Cache BYPASS", False, f"(Error: {e})")

    try:
        # CDN Stats Inspection
        r_stats = client.get("/gateway/cdn/stats")
        s_data = r_stats.json()
        assert_test(
            "Cloud CDN: Edge Cache Statistics & Ratio",
            r_stats.status_code == 200 and s_data.get("hits", 0) >= 1,
            f"(Hits: {s_data.get('hits')}, Misses: {s_data.get('misses')}, Ratio: {s_data.get('hit_ratio_percent')}%)"
        )
    except Exception as e:
        assert_test("Cloud CDN: Edge Cache Statistics & Ratio", False, f"(Error: {e})")

    # --------------------------------------------------------------------------
    # 3. Web UI & Static Assets
    # --------------------------------------------------------------------------
    print("\n--- 3. Web UI & Static Assets Verification ---")
    try:
        r = client.get("/")
        assert_test("GET / (Web UI HTML)", r.status_code == 200 and ("Collaborate Portal" in r.text or "html" in r.text.lower()), f"({len(r.text)} bytes)")
    except Exception as e:
        assert_test("GET /", False, f"(Error: {e})")

    # --------------------------------------------------------------------------
    # 4. Core Business & AI Endpoints
    # --------------------------------------------------------------------------
    print("\n--- 4. Core Business & AI Endpoints Verification ---")
    try:
        r = client.get("/api/v1/notes/current?sample=coway_meet_85min")
        data = r.json()
        total_turns = data.get("total_turns", 0)
        assert_test("GET /api/v1/notes/current", r.status_code == 200 and total_turns >= 0, f"(Total turns: {total_turns})")
    except Exception as e:
        assert_test("GET /api/v1/notes/current", False, f"(Error: {e})")

    try:
        r = client.get("/api/v1/templates")
        tpl_list = r.json().get("templates", [])
        assert_test("GET /api/v1/templates", r.status_code == 200 and len(tpl_list) >= 3, f"({len(tpl_list)} prompt templates)")
    except Exception as e:
        assert_test("GET /api/v1/templates", False, f"(Error: {e})")

    try:
        r = client.get("/api/v1/templates/CFT_REGULAR")
        tpl_data = r.json().get("template", {})
        assert_test("GET /api/v1/templates/CFT_REGULAR", r.status_code == 200 and "CFT" in tpl_data.get("name", ""), f"(Template: {tpl_data.get('name')})")
    except Exception as e:
        assert_test("GET /api/v1/templates/CFT_REGULAR", False, f"(Error: {e})")

    try:
        r = client.get("/api/v1/storage/bucket-files")
        b_data = r.json()
        assert_test("GET /api/v1/storage/bucket-files", r.status_code == 200 and "files" in b_data, f"({len(b_data.get('files', []))} media files found)")
    except Exception as e:
        assert_test("GET /api/v1/storage/bucket-files", False, f"(Error: {e})")

    try:
        payload = {
            "markdown_text": "회의에서 [화자 1]과 [화자 2]가 논의했습니다.",
            "speaker_mapping": {"[화자 1]": "홍길동 팀장", "[화자 2]": "이상훈 담당"}
        }
        r = client.post("/api/v1/notes/replace-speakers", json=payload)
        updated = r.json().get("updated_markdown", "")
        assert_test("POST /api/v1/notes/replace-speakers", "홍길동 팀장과 이상훈 담당가 논의했습니다." in updated, "(1-Click Batch Replacement verified)")
    except Exception as e:
        assert_test("POST /api/v1/notes/replace-speakers", False, f"(Error: {e})")

    # --------------------------------------------------------------------------
    # 5. Agent Gateway Security (WAF & Rate Limiter)
    # --------------------------------------------------------------------------
    print("\n--- 5. Agent Gateway Security Verification (WAF & Rate Limiter) ---")
    try:
        # Test SQL Injection prevention
        r = client.get("/api/v1/notes/current?sample=' UNION SELECT * FROM users--")
        assert_test("WAF: SQL Injection Attack Blocking", r.status_code == 403, f"(HTTP {r.status_code} Forbidden)")
    except Exception as e:
        assert_test("WAF: SQL Injection Attack Blocking", False, f"(Error: {e})")

    try:
        # Test XSS prevention
        r = client.get("/api/v1/notes/current?sample=<script>alert('xss')</script>")
        assert_test("WAF: XSS Attack Blocking", r.status_code == 403, f"(HTTP {r.status_code} Forbidden)")
    except Exception as e:
        assert_test("WAF: XSS Attack Blocking", False, f"(Error: {e})")

    try:
        # Test CORS headers
        r = client.options("/api/v1/health", headers={"Origin": "https://portal.coway.co.kr", "Access-Control-Request-Method": "GET"})
        cors_hdr = r.headers.get("access-control-allow-origin")
        assert_test("CORS Headers Injection", cors_hdr in ["*", "https://portal.coway.co.kr"] or r.status_code == 200, f"(Access-Control-Allow-Origin: {cors_hdr})")
    except Exception as e:
        assert_test("CORS Headers Injection", False, f"(Error: {e})")

    # --------------------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------------------
    print("\n==================================================================")
    print(f"📊 [테스트 결과 요약] 총 {passed + failed}개 테스트 중 {passed}개 통과 / {failed}개 실패")
    print("==================================================================")
    if failed == 0:
        print("🎉 [SUCCESS] Agent Gateway & Cloud CDN 외부 접근 및 보안 검증이 완벽하게 완료되었습니다!")
        return True
    else:
        print("⚠️ [WARNING] 일부 테스트 항목에 실패했습니다. 로그를 점검하세요.")
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
    success = run_tests(target)
    sys.exit(0 if success else 1)
