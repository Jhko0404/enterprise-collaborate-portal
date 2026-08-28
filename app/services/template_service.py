import os
import json
from typing import Dict, Any, List, Optional
from app.templates.cft_regular import CFT_REGULAR_PROMPT
from app.templates.kickoff import KICKOFF_PROMPT, EXECUTIVE_PROMPT

DEFAULT_TEMPLATES = {
    "CFT_REGULAR": {
        "id": "CFT_REGULAR",
        "name": "CFT 정기 회의록",
        "description": "정기 TFT/CFT 미팅을 위한 회의록 템플릿 (부서별 의견, 핵심 결정사항, Action Items)",
        "prompt": CFT_REGULAR_PROMPT.strip(),
        "is_default": True
    },
    "KICKOFF": {
        "id": "KICKOFF",
        "name": "프로젝트 킥오프",
        "description": "신규 프로젝트 착수를 위한 템플릿 (추진 배경, 마일스톤, R&R, 리스크 대응)",
        "prompt": KICKOFF_PROMPT.strip(),
        "is_default": True
    },
    "EXECUTIVE": {
        "id": "EXECUTIVE",
        "name": "경영진/임원 보고",
        "description": "임원 및 경영진을 위한 결론 우선형 회의록 (3줄 요약 BLUF, 비즈니스 영향도, 쟁점)",
        "prompt": EXECUTIVE_PROMPT.strip(),
        "is_default": True
    }
}

class TemplateService:
    def __init__(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.storage_file = os.path.join(root_dir, "data", "templates", "templates.json")
        self._ensure_storage()

    def _ensure_storage(self):
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        if not os.path.exists(self.storage_file):
            self._save_templates(DEFAULT_TEMPLATES)

    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_TEMPLATES.copy()

    def _save_templates(self, templates: Dict[str, Dict[str, Any]]):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

    def _format_template(self, tpl: Dict[str, Any]) -> Dict[str, Any]:
        item = tpl.copy()
        p = item.get("prompt") or item.get("system_prompt") or ""
        item["prompt"] = p
        item["system_prompt"] = p
        return item

    def list_templates(self) -> List[Dict[str, Any]]:
        templates = self._load_templates()
        return [self._format_template(t) for t in templates.values()]

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        templates = self._load_templates()
        tpl = templates.get(template_id)
        if tpl:
            return self._format_template(tpl)
        return None

    def get_prompt(self, template_id: str) -> str:
        tpl = self.get_template(template_id)
        if tpl:
            return tpl.get("prompt", CFT_REGULAR_PROMPT)
        return CFT_REGULAR_PROMPT

    def update_template(self, template_id: str, prompt: str, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        templates = self._load_templates()
        if template_id not in templates:
            templates[template_id] = {
                "id": template_id,
                "name": name or template_id,
                "description": description or "",
                "prompt": prompt,
                "is_default": False
            }
        else:
            templates[template_id]["prompt"] = prompt
            if name:
                templates[template_id]["name"] = name
            if description is not None:
                templates[template_id]["description"] = description
        
        self._save_templates(templates)
        return self._format_template(templates[template_id])

    def reset_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        templates = self._load_templates()
        if template_id in DEFAULT_TEMPLATES:
            templates[template_id] = DEFAULT_TEMPLATES[template_id].copy()
            self._save_templates(templates)
            return self._format_template(templates[template_id])
        return None

template_service = TemplateService()
