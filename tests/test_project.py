import json
from datetime import datetime
from pathlib import Path
from scripts.project import load_project, save_project

def test_load_project_not_found(tmp_project):
    result = load_project("nonexistent", tmp_project)
    assert result["error"] == "project_not_found"

def test_load_project_no_sessions(tmp_project):
    (tmp_project / "projects" / "my-project").mkdir(parents=True)
    result = load_project("my-project", tmp_project)
    assert result["project"] == "my-project"
    assert result["sessions"] == []

def test_load_project_reads_sessions(tmp_project):
    (tmp_project / "projects" / "my-project").mkdir(parents=True)
    today = datetime.now().strftime("%Y-%m-%d")
    sf = tmp_project / ".claude" / "amnesia" / "sessions" / f"{today}.md"
    sf.write_text(f"# Session Log - {today}\n\n---\n\n## project:my-project (10:00)\n### Summary\nDid stuff\n")
    result = load_project("my-project", tmp_project)
    assert len(result["sessions"]) >= 1
    assert any("my-project" in s["header"] for s in result["sessions"])

def test_save_project_creates_session_file(tmp_project):
    entry = {"summary": "Fixed the merge bug", "changes": ["scripts/merge.py — fixed dedup"],
             "commits": ["abc1234 fix: dedup"], "decisions": ["Use strip+lower"], "next": ["Add tests"]}
    result = save_project("my-project", entry, tmp_project)
    assert result["error"] is None
    today = datetime.now().strftime("%Y-%m-%d")
    content = (tmp_project / ".claude" / "amnesia" / "sessions" / f"{today}.md").read_text()
    assert "project:my-project" in content
    assert "Fixed the merge bug" in content

def test_save_project_appends_to_existing(tmp_project):
    today = datetime.now().strftime("%Y-%m-%d")
    sf = tmp_project / ".claude" / "amnesia" / "sessions" / f"{today}.md"
    sf.write_text(f"# Session Log - {today}\n\n---\n\n## project:other (09:00)\nExisting\n")
    save_project("my-project", {"summary": "New", "changes": [], "commits": [], "decisions": [], "next": []}, tmp_project)
    content = sf.read_text()
    assert "project:other" in content and "project:my-project" in content
