import json, pytest
from pathlib import Path

@pytest.fixture
def tmp_project(tmp_path):
    (tmp_path / ".claude" / "amnesia" / "memory").mkdir(parents=True)
    (tmp_path / ".claude" / "amnesia" / "sessions").mkdir(parents=True)
    (tmp_path / "projects").mkdir(parents=True)
    return tmp_path

@pytest.fixture
def sample_entity():
    return {
        "$schema": "amnesia-entity", "entity": "test_client",
        "updated_at": "2026-04-01T10:00:00Z",
        "permanent_facts": {"metadata": {"data_source": "Sienge API"}, "items": ["existing fact one", "existing fact two"]},
        "decisions": [{"date": "2026-03-01", "author": "user", "decision": "Use V2 pipeline"}],
        "current_status": {"phase": "processing", "tracker_ids": ["OL-100"], "blockers": []},
        "last_session": {"date": "2026-04-01", "summary": "Processed January data"},
        "technical_notes": ["existing note"]
    }

@pytest.fixture
def sample_entity_v1():
    return {
        "$schema": "etl-client-memory-v1", "client": "legacy_client",
        "updated_at": "2026-03-01T10:00:00Z",
        "permanent_facts": {"data_source": "Sienge", "s3_name": "legacy-client", "items": ["legacy fact"]},
        "decisions": [],
        "current_status": {"phase": "done", "jira_tickets": ["OL-99"], "blockers": []},
        "last_session": {"date": "2026-03-01", "summary": "Done"},
        "technical_notes": []
    }
