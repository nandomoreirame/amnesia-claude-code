from scripts.merge import merge_list, merge_decisions, merge_entity

def test_merge_list_appends_new():
    merged, added, skipped = merge_list(["fact one", "fact two"], ["fact three", "fact one"])
    assert "fact three" in added and "fact one" in skipped and len(merged) == 3

def test_merge_list_dedup_normalizes():
    merged, added, skipped = merge_list(["  Fact One  "], ["fact one"])
    assert len(merged) == 1 and "fact one" in skipped

def test_merge_decisions_dedup_by_key():
    existing = [{"date": "2026-03-01", "author": "user", "decision": "Use V2"}]
    new = [{"date": "2026-03-01", "author": "user", "decision": "Use V2"},
           {"date": "2026-04-01", "author": "livia", "decision": "New decision"}]
    merged, added, skipped = merge_decisions(existing, new)
    assert len(merged) == 2 and len(added) == 1 and len(skipped) == 1

def test_merge_entity_replaces_current_status(sample_entity):
    updates = {
        "current_status": {"phase": "upload complete", "tracker_ids": ["OL-200"], "blockers": []},
        "last_session": {"date": "2026-04-03", "summary": "Uploaded data"},
        "permanent_facts": {"items": ["new fact"], "metadata": {}},
        "decisions": [], "technical_notes": [],
    }
    result, diff = merge_entity(sample_entity, updates)
    assert result["current_status"]["phase"] == "upload complete"
    assert "new fact" in result["permanent_facts"]["items"]
    assert "existing fact one" in result["permanent_facts"]["items"]
