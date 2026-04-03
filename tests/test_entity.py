import json, pytest
from scripts.entity import load_entity, list_entities, diff_entity, save_entity, validate_entity_name
from scripts.schema import SCHEMA_URL

def test_validate_entity_name_valid():
    assert validate_entity_name("my-project") == "my-project"
    assert validate_entity_name("test_client") == "test_client"
    assert validate_entity_name("Client123") == "Client123"

def test_validate_entity_name_rejects_path_traversal():
    with pytest.raises(ValueError, match="invalid_entity_name"):
        validate_entity_name("../../etc/passwd")

def test_validate_entity_name_rejects_slashes():
    with pytest.raises(ValueError, match="invalid_entity_name"):
        validate_entity_name("some/path")

def test_validate_entity_name_rejects_dots():
    with pytest.raises(ValueError, match="invalid_entity_name"):
        validate_entity_name("..sneaky")

def test_validate_entity_name_rejects_empty():
    with pytest.raises(ValueError, match="invalid_entity_name"):
        validate_entity_name("")

def test_load_entity_rejects_path_traversal(tmp_project):
    with pytest.raises(ValueError, match="invalid_entity_name"):
        load_entity("../../etc/passwd", tmp_project)

def test_save_entity_rejects_path_traversal(tmp_project):
    with pytest.raises(ValueError, match="invalid_entity_name"):
        save_entity("../evil", {}, tmp_project)

def test_diff_entity_rejects_path_traversal(tmp_project):
    with pytest.raises(ValueError, match="invalid_entity_name"):
        diff_entity("../evil", {}, tmp_project)

def test_save_entity_writes_pretty_json(tmp_project):
    updates = {"permanent_facts": {"items": ["fact"], "metadata": {}},
               "decisions": [], "technical_notes": [],
               "current_status": {"phase": "active", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "2026-04-03", "summary": "Test"}}
    save_entity("pretty_test", updates, tmp_project)
    raw = (tmp_project / ".claude" / "amnesia" / "memory" / "pretty_test.json").read_text()
    assert "\n" in raw
    assert "  " in raw

def test_load_entity_found(tmp_project, sample_entity):
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(json.dumps(sample_entity))
    result = load_entity("test_client", tmp_project)
    assert result["entity"] == "test_client"
    assert len(result["permanent_facts"]["items"]) == 2

def test_load_entity_not_found(tmp_project):
    assert load_entity("nonexistent", tmp_project) is None

def test_load_entity_migrates_v1(tmp_project, sample_entity_v1):
    (tmp_project / ".claude" / "amnesia" / "memory" / "legacy_client.json").write_text(json.dumps(sample_entity_v1))
    result = load_entity("legacy_client", tmp_project)
    assert result["$schema"] == SCHEMA_URL

def test_load_entity_corrupted_raises(tmp_project):
    (tmp_project / ".claude" / "amnesia" / "memory" / "broken.json").write_text("{{{invalid")
    with pytest.raises(ValueError, match="invalid_json"):
        load_entity("broken", tmp_project)

def test_list_entities(tmp_project, sample_entity):
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(json.dumps(sample_entity))
    result = list_entities(tmp_project)
    assert len(result) == 1
    assert result[0]["entity"] == "test_client"
    assert "updated_at" in result[0]
    assert "phase" in result[0]

def test_list_entities_empty(tmp_project):
    assert list_entities(tmp_project) == []

def test_diff_entity_shows_changes(tmp_project, sample_entity):
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(json.dumps(sample_entity))
    updates = {
        "permanent_facts": {"items": ["new fact", "existing fact one"], "metadata": {}},
        "decisions": [{"date": "2026-04-03", "author": "user", "decision": "New decision"}],
        "technical_notes": [],
        "current_status": {"phase": "done", "tracker_ids": [], "blockers": []},
        "last_session": {"date": "2026-04-03", "summary": "Test"},
    }
    result = diff_entity("test_client", updates, tmp_project)
    assert result["diff"]["permanent_facts.items"]["added"] == ["new fact"]
    assert "existing fact one" in result["diff"]["permanent_facts.items"]["skipped"]

def test_diff_entity_is_new(tmp_project):
    updates = {"permanent_facts": {"items": [], "metadata": {}}, "decisions": [],
               "technical_notes": [], "current_status": {"phase": "", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "", "summary": ""}}
    result = diff_entity("brand_new", updates, tmp_project)
    assert result["is_new"] is True

def test_save_entity_creates_file(tmp_project):
    updates = {"permanent_facts": {"items": ["first fact"], "metadata": {"source": "API"}},
               "decisions": [{"date": "2026-04-03", "author": "user", "decision": "Start"}],
               "technical_notes": [],
               "current_status": {"phase": "active", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "2026-04-03", "summary": "Initial"}}
    result = save_entity("new_client", updates, tmp_project)
    assert result["is_new"] is True
    written = json.loads((tmp_project / ".claude" / "amnesia" / "memory" / "new_client.json").read_text())
    assert written["$schema"] == SCHEMA_URL
    assert "first fact" in written["permanent_facts"]["items"]

def test_save_entity_merges_existing(tmp_project, sample_entity):
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(json.dumps(sample_entity))
    updates = {"permanent_facts": {"items": ["brand new fact"], "metadata": {}},
               "decisions": [], "technical_notes": [],
               "current_status": {"phase": "complete", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "2026-04-03", "summary": "Done"}}
    save_entity("test_client", updates, tmp_project)
    written = json.loads((tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").read_text())
    assert "existing fact one" in written["permanent_facts"]["items"]
    assert "brand new fact" in written["permanent_facts"]["items"]
    assert written["current_status"]["phase"] == "complete"

def test_save_entity_migrates_v1(tmp_project, sample_entity_v1):
    (tmp_project / ".claude" / "amnesia" / "memory" / "legacy_client.json").write_text(json.dumps(sample_entity_v1))
    updates = {"permanent_facts": {"items": [], "metadata": {}}, "decisions": [], "technical_notes": [],
               "current_status": {"phase": "migrated", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "2026-04-03", "summary": "Migration"}}
    save_entity("legacy_client", updates, tmp_project)
    written = json.loads((tmp_project / ".claude" / "amnesia" / "memory" / "legacy_client.json").read_text())
    assert written["$schema"] == SCHEMA_URL
