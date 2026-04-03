import json, subprocess, sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_AMNESIA_PY = str(_PROJECT_ROOT / "scripts" / "amnesia.py")

def run_amnesia(args, cwd):
    r = subprocess.run([sys.executable, _AMNESIA_PY] + args, capture_output=True, text=True, cwd=cwd)
    return json.loads(r.stdout)

def test_cli_entity_list_empty(tmp_project):
    out = run_amnesia(["--project-root", str(tmp_project), "entity", "list"], str(tmp_project))
    assert out["error"] is None and out["data"] == []

def test_cli_entity_load_not_found(tmp_project):
    out = run_amnesia(["--project-root", str(tmp_project), "entity", "load", "nope"], str(tmp_project))
    assert out["data"]["found"] is False

def test_cli_error_corrupted_json(tmp_project):
    (tmp_project / ".claude" / "amnesia" / "memory" / "broken.json").write_text("{{{invalid")
    out = run_amnesia(["--project-root", str(tmp_project), "entity", "load", "broken"], str(tmp_project))
    assert out["error"] is not None and out["data"] is None

def test_project_root_flag(tmp_project, sample_entity):
    import json as _json
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(_json.dumps(sample_entity))
    out = run_amnesia(["--project-root", str(tmp_project), "entity", "load", "test_client"], str(Path.home()))
    assert out["data"]["found"] is True
    assert out["data"]["entity"] == "test_client"

def test_cli_list_unified(tmp_project, sample_entity):
    import json as _json
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(_json.dumps(sample_entity))
    (tmp_project / "projects" / "my-project").mkdir(parents=True)
    out = run_amnesia(["--project-root", str(tmp_project), "list"], str(tmp_project))
    assert out["error"] is None
    assert any(e["entity"] == "test_client" for e in out["data"]["entities"])
    assert "my-project" in out["data"]["projects"]
