import json
import pytest
from pathlib import Path
from scripts.lang import detect_language, get_project_language


def test_detects_pt_br(tmp_path):
    s = tmp_path / "settings.json"
    s.write_text(json.dumps({"language": "pt-BR"}))
    assert detect_language(settings_path=s) == "pt-BR"


def test_detects_en(tmp_path):
    s = tmp_path / "settings.json"
    s.write_text(json.dumps({"language": "en"}))
    assert detect_language(settings_path=s) == "en"


def test_absent_field_defaults_en(tmp_path):
    s = tmp_path / "settings.json"
    s.write_text(json.dumps({}))
    assert detect_language(settings_path=s) == "en"


def test_missing_file_defaults_en():
    assert detect_language(settings_path=Path("/nonexistent/settings.json")) == "en"


def test_local_overrides_global(tmp_path):
    global_s = tmp_path / "global_settings.json"
    local_s = tmp_path / "local_settings.json"
    global_s.write_text(json.dumps({"language": "en"}))
    local_s.write_text(json.dumps({"language": "pt-BR"}))
    assert detect_language(settings_path=local_s, fallback_path=global_s) == "pt-BR"
