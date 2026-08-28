from typing import Dict

class SpeakerMappingService:
    @staticmethod
    def replace_speakers(text: str, mapping: Dict[str, str]) -> str:
        """
        미확정 화자 라벨([참석자 1], [참석자 2])을 실제 참석자 이름으로 일괄 치환
        예: mapping = {"[참석자 1]": "홍길동 팀장", "[참석자 2]": "이상훈 담당"}
        """
        if not mapping or not text:
            return text
            
        result = text
        for placeholder, real_name in mapping.items():
            if placeholder and real_name:
                result = result.replace(placeholder, real_name)
        return result

    @classmethod
    def replace_speaker_labels(cls, text: str, mapping: Dict[str, str]) -> str:
        return cls.replace_speakers(text, mapping)

