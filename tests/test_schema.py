from scripts.schema import EntityMemory, is_legacy_schema, migrate_v1

def test_entity_memory_valid(sample_entity):
    m = EntityMemory.model_validate(sample_entity)
    assert m.entity == "test_client"
    assert len(m.permanent_facts.items) == 2

def test_entity_memory_defaults():
    m = EntityMemory(entity="new_client")
    assert m.schema_ == "amnesia-entity"
    assert m.permanent_facts.items == []

def test_is_legacy_schema(sample_entity_v1):
    assert is_legacy_schema(sample_entity_v1) is True

def test_is_not_legacy_schema(sample_entity):
    assert is_legacy_schema(sample_entity) is False

def test_migrate_v1(sample_entity_v1):
    migrated = migrate_v1(sample_entity_v1)
    m = EntityMemory.model_validate(migrated)
    assert m.entity == "legacy_client"
    assert m.permanent_facts.metadata["s3_name"] == "legacy-client"
    assert "OL-99" in m.current_status.tracker_ids
    assert m.schema_ == "amnesia-entity"
