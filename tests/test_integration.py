import json
from pathlib import Path
from scripts.entity import load_entity, diff_entity, save_entity

FIXTURES = Path(__file__).parent / "fixtures"

def test_roundtrip_no_data_loss(tmp_project):
    fixture = json.loads((FIXTURES / "vivamus.json").read_text())
    (tmp_project / ".claude" / "amnesia" / "memory" / "vivamus.json").write_text(json.dumps(fixture))
    loaded = load_entity("vivamus", tmp_project)
    original_count = len(loaded["permanent_facts"]["items"])
    updates = {"permanent_facts": {"items": ["integration test fact"], "metadata": {}},
               "decisions": [], "technical_notes": [],
               "current_status": loaded["current_status"],
               "last_session": {"date": "2026-04-03", "summary": "Integration test"}}
    diff = diff_entity("vivamus", updates, tmp_project)
    assert diff["diff"]["permanent_facts.items"]["added"] == ["integration test fact"]
    save_entity("vivamus", updates, tmp_project)
    reloaded = load_entity("vivamus", tmp_project)
    assert len(reloaded["permanent_facts"]["items"]) == original_count + 1
    assert reloaded["$schema"] == "amnesia-entity"

def test_dedup_on_repeated_save(tmp_project):
    fixture = json.loads((FIXTURES / "vivamus.json").read_text())
    (tmp_project / ".claude" / "amnesia" / "memory" / "vivamus.json").write_text(json.dumps(fixture))
    updates = {"permanent_facts": {"items": ["duplicate fact"], "metadata": {}},
               "decisions": [], "technical_notes": [],
               "current_status": {"phase": "test", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "2026-04-03", "summary": "Test"}}
    save_entity("vivamus", updates, tmp_project)
    save_entity("vivamus", updates, tmp_project)  # save twice
    reloaded = load_entity("vivamus", tmp_project)
    assert reloaded["permanent_facts"]["items"].count("duplicate fact") == 1
