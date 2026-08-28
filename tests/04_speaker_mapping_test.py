import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.speaker_service import SpeakerMappingService

def test_speaker_mapping():
    print("=== [테스트 4: 화자 지능형 매핑 및 일괄 치환(Replace All) 엔진 테스트] ===")
    
    sample_text = """
# 📋 [CFT_REGULAR 회의록] 기술 미팅
## 3. 안건별 상세 논의
- [참석자 1]은 AI 회의록 도입에 따른 생산성 혁신 효과를 제시했습니다.
- [참석자 2]는 16kHz 모노 변환 및 Vertex AI 연동 방식에 대해 문의했습니다.
- [참석자 1]이 이에 대해 0-Day Retention 데이터 거버넌스를 함께 설명했습니다.

## 4. 실행 과제
| No | 과제 | 담당자 | 기한 |
|:--:|:---|:---:|:---:|
| 1 | 아키텍처 문서화 | [참석자 2] | 2026-08-25 |
| 2 | 보안성 검토 | [참석자 1] | 2026-08-28 |
"""

    mapping = {
        "[참석자 1]": "홍길동 팀장 (리테일 회사)",
        "[참석자 2]": "담당 CE (Google Cloud)"
    }

    print("1. 화자 라벨 치환 실행...")
    result = SpeakerMappingService.replace_speakers(sample_text, mapping)

    print("2. 치환 결과 검증:")
    assert "[참석자 1]" not in result, "[참석자 1] 치환 누락"
    assert "[참석자 2]" not in result, "[참석자 2] 치환 누락"
    assert "홍길동 팀장 (리테일 회사)" in result, "치환된 이름(홍길동 팀장) 누락"
    assert "담당 CE (Google Cloud)" in result, "치환된 이름(담당 CE) 누락"
    assert result.count("홍길동 팀장 (리테일 회사)") == 3, "치환 횟수 불일치 (기대값: 3회)"
    assert result.count("담당 CE (Google Cloud)") == 2, "치환 횟수 불일치 (기대값: 2회)"

    # 3. 엣지 케이스 테스트 (빈 매핑, 빈 텍스트)
    assert SpeakerMappingService.replace_speakers("", mapping) == ""
    assert SpeakerMappingService.replace_speakers(sample_text, {}) == sample_text

    print("   ✅ 모든 화자 라벨이 정확하게 일괄 치환됨 (다중 발생 및 표 내부 포함)")
    print(">>> [테스트 4 성공] 화자 매핑 및 일괄 치환 엔진 검증 완료!\n")

if __name__ == "__main__":
    test_speaker_mapping()
