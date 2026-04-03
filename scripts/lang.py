"""Language detection from Claude Code settings.json."""
import json
from pathlib import Path


def detect_language(settings_path=None, fallback_path=None) -> str:
    def read_lang(path):
        if path and Path(path).exists():
            try:
                return json.loads(Path(path).read_text(encoding="utf-8")).get("language")
            except (json.JSONDecodeError, OSError):
                pass
        return None

    return read_lang(settings_path) or read_lang(fallback_path) or "en"


def get_project_language(project_root=None) -> str:
    global_settings = Path.home() / ".claude" / "settings.json"
    local_settings = (Path(project_root) if project_root else Path.cwd()) / ".claude" / "settings.json"
    return detect_language(settings_path=local_settings, fallback_path=global_settings)
