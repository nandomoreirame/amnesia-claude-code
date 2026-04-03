# Plan: Amnesia Claude Code Plugin

> **Spec:** docs/specs/2026-04-03-amnesia-plugin.md

**Goal:** Implement `amnesia.py` (Python CLI + Pydantic v2) + thin `.md` commands + plugin metadata, replacing ~800 lines of LLM instructions with distributable deterministic logic via `/plugin install`.

**Architecture:** `amnesia.py` exposes subcommands (`entity load/diff/save/list`, `project load/save`, `list`) with always-structured JSON output. Pydantic v2 validates the `amnesia-entity` schema. `.md` commands are wrappers with ≤40 lines. The plugin is distributed via `.claude-plugin/plugin.json`.

**Tech Stack:** Python 3.10+, Pydantic v2, pytest, argparse

**Total Tasks:** 17

**Estimated Complexity:** large

---

## Group 1 — Foundation (Tasks 1-3)

### Task 1: Project scaffold

**Requirement:** Foundation for all REQs
**Files:**

- Create: `pyproject.toml`
- Create: `scripts/__init__.py`
- Create: `scripts/amnesia.py` (skeleton)
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Write the failing test**

```python
# tests/test_scaffold.py
import subprocess, sys

def test_amnesia_py_runs():
    result = subprocess.run(
        [sys.executable, "scripts/amnesia.py", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "amnesia" in result.stdout.lower()
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_scaffold.py -v`
Expected: FAIL — `FileNotFoundError: scripts/amnesia.py`

**Step 3: Write minimal implementation**

`pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "amnesia"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pydantic>=2.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

`scripts/amnesia.py` (skeleton):

```python
#!/usr/bin/env python3
"""Amnesia CLI — deterministic memory operations for Claude Code."""
import argparse, json, sys

def ok(data): print(json.dumps({"data": data, "error": None}, ensure_ascii=False))
def err(message, file=""): print(json.dumps({"data": None, "error": message, "file": file}, ensure_ascii=False)); sys.exit(1)

def main():
    parser = argparse.ArgumentParser(prog="amnesia", description="Amnesia — deterministic memory operations for Claude Code")
    parser.parse_args()

if __name__ == "__main__":
    main()
```

`tests/conftest.py`:

```python
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
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_scaffold.py -v`
Expected: PASS

**Step 5: Commit**
Run: `/git commit`

---

### Task 2: Pydantic schema (EntityMemory + v1 migration)

**Requirement:** REQ-007
**Files:**

- Create: `scripts/schema.py`
- Create: `tests/test_schema.py`

**Step 1: Write the failing test**

```python
# tests/test_schema.py
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
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.schema'`

**Step 3: Write minimal implementation**

`scripts/schema.py`:

```python
"""Pydantic v2 schema for amnesia-entity memory files."""
from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PermanentFacts(BaseModel):
    metadata: dict[str, str] = Field(default_factory=dict)
    items: list[str] = Field(default_factory=list)

class Decision(BaseModel):
    date: str
    author: str
    decision: str

class CurrentStatus(BaseModel):
    phase: str = ""
    tracker_ids: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

class LastSession(BaseModel):
    date: str = ""
    summary: str = ""

class EntityMemory(BaseModel):
    schema_: str = Field(alias="$schema", default="amnesia-entity")
    entity: str
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    permanent_facts: PermanentFacts = Field(default_factory=PermanentFacts)
    decisions: list[Decision] = Field(default_factory=list)
    current_status: CurrentStatus = Field(default_factory=CurrentStatus)
    last_session: LastSession = Field(default_factory=LastSession)
    technical_notes: list[str] = Field(default_factory=list)
    model_config = {"populate_by_name": True}

def is_legacy_schema(data: dict) -> bool:
    return data.get("$schema") == "etl-client-memory-v1"

def migrate_v1(data: dict) -> dict:
    pf = data.get("permanent_facts", {})
    old_status = data.get("current_status", {})
    metadata = {k: str(v) for k, v in pf.items() if k != "items" and isinstance(v, (str, int, float))}
    return {
        "$schema": "amnesia-entity",
        "entity": data.get("client", data.get("entity", "")),
        "updated_at": data.get("updated_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        "permanent_facts": {"metadata": metadata, "items": pf.get("items", [])},
        "decisions": data.get("decisions", []),
        "current_status": {
            "phase": old_status.get("phase", ""),
            "tracker_ids": old_status.get("jira_tickets", old_status.get("tracker_ids", [])),
            "blockers": old_status.get("blockers", []),
        },
        "last_session": data.get("last_session", {"date": "", "summary": ""}),
        "technical_notes": data.get("technical_notes", []),
    }
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_schema.py -v`
Expected: PASS — 5 tests

**Step 5: Commit**
Run: `/git commit`

---

### Task 3: Path resolution (project root + dirs)

**Requirement:** Foundation for REQ-001 through REQ-006
**Files:**

- Create: `scripts/paths.py`
- Create: `tests/test_paths.py`

**Step 1: Write the failing test**

```python
# tests/test_paths.py
from scripts.paths import get_project_root, get_memory_dir, get_sessions_dir

def test_get_memory_dir_creates(tmp_path):
    d = get_memory_dir(tmp_path)
    assert d.exists()
    assert d == tmp_path / ".claude" / "amnesia" / "memory"

def test_get_sessions_dir_creates(tmp_path):
    d = get_sessions_dir(tmp_path)
    assert d.exists()

def test_project_root_override(tmp_path):
    root = get_project_root(override=str(tmp_path))
    assert root == tmp_path.resolve()
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_paths.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`scripts/paths.py`:

```python
"""Path resolution for amnesia plugin."""
import subprocess
from pathlib import Path

def get_project_root(override: str | None = None) -> Path:
    if override:
        return Path(override).resolve()
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(r.stdout.strip())
    except subprocess.CalledProcessError:
        return Path.cwd()

def get_memory_dir(project_root: Path) -> Path:
    d = project_root / ".claude" / "amnesia" / "memory"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_sessions_dir(project_root: Path) -> Path:
    d = project_root / ".claude" / "amnesia" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_projects_dir(project_root: Path) -> Path:
    return project_root / "projects"
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_paths.py -v`
Expected: PASS

**Step 5: Commit**
Run: `/git commit`

---

## Group 2 — Entity Operations (Tasks 4-8)

### Task 4: `entity load`

**Requirement:** REQ-001
**Files:**

- Create: `scripts/entity.py`
- Create: `tests/test_entity.py`

**Step 1: Write the failing test**

```python
# tests/test_entity.py
import json, pytest
from scripts.entity import load_entity

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
    assert result["$schema"] == "amnesia-entity"

def test_load_entity_corrupted_raises(tmp_project):
    (tmp_project / ".claude" / "amnesia" / "memory" / "broken.json").write_text("{{{invalid")
    with pytest.raises(ValueError, match="invalid_json"):
        load_entity("broken", tmp_project)
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.entity'`

**Step 3: Write minimal implementation**

`scripts/entity.py`:

```python
"""Entity memory operations."""
import json
from pathlib import Path
from scripts.paths import get_memory_dir
from scripts.schema import is_legacy_schema, migrate_v1

def load_entity(name: str, project_root: Path) -> dict | None:
    file = get_memory_dir(project_root) / f"{name}.json"
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError(f"invalid_json:{file}")
    if is_legacy_schema(data):
        data = migrate_v1(data)
    return data
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -v`
Expected: PASS — 4 tests

**Step 5: Commit**
Run: `/git commit`

---

### Task 5: `entity list`

**Requirement:** REQ-004
**Files:**

- Modify: `scripts/entity.py` — add `list_entities`
- Modify: `tests/test_entity.py` — add tests

**Step 1: Write the failing test**

```python
# add to tests/test_entity.py
from scripts.entity import list_entities

def test_list_entities(tmp_project, sample_entity):
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(json.dumps(sample_entity))
    result = list_entities(tmp_project)
    assert len(result) == 1
    assert result[0]["entity"] == "test_client"
    assert "updated_at" in result[0]
    assert "phase" in result[0]

def test_list_entities_empty(tmp_project):
    assert list_entities(tmp_project) == []
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -k list -v`
Expected: FAIL — `ImportError: cannot import name 'list_entities'`

**Step 3: Write minimal implementation**

```python
# add to scripts/entity.py
def list_entities(project_root: Path) -> list[dict]:
    results = []
    for file in sorted(get_memory_dir(project_root).glob("*.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if is_legacy_schema(data):
                data = migrate_v1(data)
            results.append({
                "entity": data.get("entity", file.stem),
                "updated_at": data.get("updated_at", ""),
                "phase": data.get("current_status", {}).get("phase", ""),
                "tracker_ids": data.get("current_status", {}).get("tracker_ids", []),
            })
        except Exception:
            results.append({"entity": file.stem, "error": "invalid_json"})
    return results
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -v`
Expected: PASS

**Step 5: Commit**
Run: `/git commit`

---

### Task 6: Merge/dedup core algorithm

**Requirement:** REQ-003
**Files:**

- Create: `scripts/merge.py`
- Create: `tests/test_merge.py`

**Step 1: Write the failing test**

```python
# tests/test_merge.py
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
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_merge.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.merge'`

**Step 3: Write minimal implementation**

`scripts/merge.py`:

```python
"""Deterministic merge and deduplication for entity memory."""
from __future__ import annotations
from datetime import datetime, timezone

def _norm(text: str) -> str:
    return text.strip().lower()

def merge_list(existing: list[str], new_items: list[str]) -> tuple[list[str], list[str], list[str]]:
    seen = {_norm(i): True for i in existing}
    merged, added, skipped = list(existing), [], []
    for item in new_items:
        if _norm(item) not in seen:
            merged.append(item); added.append(item); seen[_norm(item)] = True
        else:
            skipped.append(item)
    return merged, added, skipped

def merge_decisions(existing: list[dict], new_decisions: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    def key(d): return f"{d.get('date','')}|{d.get('author','')}|{d.get('decision','')[:50]}"
    seen = {key(d) for d in existing}
    merged, added, skipped = list(existing), [], []
    for d in new_decisions:
        if key(d) not in seen:
            merged.append(d); added.append(d); seen.add(key(d))
        else:
            skipped.append(d)
    return merged, added, skipped

def merge_entity(existing: dict, updates: dict) -> tuple[dict, dict]:
    result = {**existing}
    diff = {
        "permanent_facts.items": {"added": [], "skipped": []},
        "permanent_facts.metadata": {"added": [], "updated": []},
        "decisions": {"added": [], "skipped": []},
        "technical_notes": {"added": [], "skipped": []},
        "current_status": {"updated": False},
        "last_session": {"updated": False},
    }
    items, added, skipped = merge_list(
        existing.get("permanent_facts", {}).get("items", []),
        updates.get("permanent_facts", {}).get("items", []))
    result.setdefault("permanent_facts", {})["items"] = items
    diff["permanent_facts.items"].update({"added": added, "skipped": skipped})

    em = existing.get("permanent_facts", {}).get("metadata", {})
    nm = updates.get("permanent_facts", {}).get("metadata", {})
    mm = {**em}
    for k, v in nm.items():
        (diff["permanent_facts.metadata"]["added"] if k not in em else diff["permanent_facts.metadata"]["updated"]).append(k)
        mm[k] = v
    result["permanent_facts"]["metadata"] = mm

    dec, added_d, skip_d = merge_decisions(existing.get("decisions", []), updates.get("decisions", []))
    result["decisions"] = dec; diff["decisions"].update({"added": added_d, "skipped": skip_d})

    notes, added_n, skip_n = merge_list(existing.get("technical_notes", []), updates.get("technical_notes", []))
    result["technical_notes"] = notes; diff["technical_notes"].update({"added": added_n, "skipped": skip_n})

    if "current_status" in updates:
        result["current_status"] = updates["current_status"]; diff["current_status"]["updated"] = True
    if "last_session" in updates:
        result["last_session"] = updates["last_session"]; diff["last_session"]["updated"] = True

    result["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return result, diff
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_merge.py -v`
Expected: PASS — 4 tests

**Step 5: Commit**
Run: `/git commit`

---

### Task 7: `entity diff`

**Requirement:** REQ-002, REQ-009
**Files:**

- Modify: `scripts/entity.py` — add `diff_entity`
- Modify: `tests/test_entity.py` — add tests

**Step 1: Write the failing test**

```python
# add to tests/test_entity.py
from scripts.entity import diff_entity

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
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -k diff -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# add to scripts/entity.py
from scripts.merge import merge_entity

def diff_entity(name: str, updates: dict, project_root: Path) -> dict:
    existing = load_entity(name, project_root)
    is_new = existing is None
    if is_new:
        existing = {"entity": name, "$schema": "amnesia-entity",
                    "permanent_facts": {"metadata": {}, "items": []},
                    "decisions": [], "current_status": {}, "last_session": {}, "technical_notes": []}
    preview, diff = merge_entity(existing, updates)
    return {"is_new": is_new, "entity": name, "diff": diff, "preview": preview}
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -v`
Expected: PASS

**Step 5: Commit**
Run: `/git commit`

---

### Task 8: `entity save` + write with migration

**Requirement:** REQ-002, REQ-003, REQ-007
**Files:**

- Modify: `scripts/entity.py` — add `save_entity`
- Modify: `tests/test_entity.py` — add tests

**Step 1: Write the failing test**

```python
# add to tests/test_entity.py
from scripts.entity import save_entity

def test_save_entity_creates_file(tmp_project):
    updates = {"permanent_facts": {"items": ["first fact"], "metadata": {"source": "API"}},
               "decisions": [{"date": "2026-04-03", "author": "user", "decision": "Start"}],
               "technical_notes": [],
               "current_status": {"phase": "active", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "2026-04-03", "summary": "Initial"}}
    result = save_entity("new_client", updates, tmp_project)
    assert result["is_new"] is True
    written = json.loads((tmp_project / ".claude" / "amnesia" / "memory" / "new_client.json").read_text())
    assert written["$schema"] == "amnesia-entity"
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
    assert written["$schema"] == "amnesia-entity"
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -k save -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# add to scripts/entity.py
def save_entity(name: str, updates: dict, project_root: Path) -> dict:
    existing = load_entity(name, project_root)
    is_new = existing is None
    if is_new:
        existing = {"$schema": "amnesia-entity", "entity": name,
                    "permanent_facts": {"metadata": {}, "items": []},
                    "decisions": [], "current_status": {}, "last_session": {}, "technical_notes": []}
    merged, diff = merge_entity(existing, updates)
    merged["$schema"] = "amnesia-entity"
    merged["entity"] = name
    file = get_memory_dir(project_root) / f"{name}.json"
    file.write_text(json.dumps(merged, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return {"entity": name, "is_new": is_new, "file": str(file), "diff": diff}
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_entity.py -v`
Expected: PASS — all entity tests

**Step 5: Commit**
Run: `/git commit`

---

## Group 3 — Project Operations (Tasks 9-10)

### Task 9: `project load`

**Requirement:** REQ-005
**Files:**

- Create: `scripts/project.py`
- Create: `tests/test_project.py`

**Step 1: Write the failing test**

```python
# tests/test_project.py
import json
from datetime import datetime
from pathlib import Path
from scripts.project import load_project

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
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_project.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

`scripts/project.py`:

```python
"""Project session memory operations."""
from __future__ import annotations
import re, subprocess
from datetime import datetime, timedelta
from pathlib import Path
from scripts.paths import get_sessions_dir, get_projects_dir

def _git_log(project_dir: Path, days: int = 7) -> list[str]:
    try:
        r = subprocess.run(["git", "-C", str(project_dir), "log", "--oneline", f"--since={days} days ago"],
                           capture_output=True, text=True, check=True)
        return [l for l in r.stdout.strip().splitlines() if l]
    except subprocess.CalledProcessError:
        return []

def _extract_sections(content: str, name: str) -> list[dict]:
    pattern = re.compile(
        rf"^## project:{re.escape(name)}\s*\((\d{{2}}:\d{{2}})\)(.*?)(?=^---|\Z)",
        re.M | re.S)
    return [{"header": f"project:{name} ({m.group(1)})", "time": m.group(1), "content": m.group(2).strip()}
            for m in pattern.finditer(content)]

def load_project(name: str, project_root: Path, days: int = 7) -> dict:
    project_dir = get_projects_dir(project_root) / name
    if not project_dir.exists():
        return {"project": name, "error": "project_not_found", "sessions": [], "git_log": []}
    sessions_dir = get_sessions_dir(project_root)
    sessions = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        f = sessions_dir / f"{date}.md"
        if f.exists():
            for s in _extract_sections(f.read_text(encoding="utf-8"), name):
                sessions.append({**s, "date": date})
    return {"project": name, "project_dir": str(project_dir),
            "sessions": sessions, "git_log": _git_log(project_dir, days), "error": None}
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_project.py -v`
Expected: PASS

**Step 5: Commit**
Run: `/git commit`

---

### Task 10: `project save`

**Requirement:** REQ-010
**Files:**

- Modify: `scripts/project.py` — add `save_project`
- Modify: `tests/test_project.py` — add tests

**Step 1: Write the failing test**

```python
# add to tests/test_project.py
from scripts.project import save_project

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
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_project.py -k save -v`
Expected: FAIL

**Step 3: Write minimal implementation**

```python
# add to scripts/project.py
def save_project(name: str, entry: dict, project_root: Path) -> dict:
    sessions_dir = get_sessions_dir(project_root)
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")
    sf = sessions_dir / f"{today}.md"
    lines = [f"## project:{name} ({now})", f"### Summary\n{entry.get('summary', '')}"]
    for key, label in [("changes", "Changes"), ("commits", "Commits"), ("decisions", "Decisions"), ("next", "Next")]:
        if entry.get(key):
            lines.append(f"### {label}")
            prefix = "- [ ] " if key == "next" else "- "
            lines.extend(f"{prefix}{i}" for i in entry[key])
    text = "\n".join(lines)
    if sf.exists():
        sf.write_text(sf.read_text(encoding="utf-8") + f"\n---\n\n{text}\n", encoding="utf-8")
    else:
        sf.write_text(f"# Session Log - {today}\n\n---\n\n{text}\n", encoding="utf-8")
    return {"project": name, "file": str(sf), "time": now, "error": None}
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_project.py -v`
Expected: PASS — all project tests

**Step 5: Commit**
Run: `/git commit`

---

## Group 4 — Plugin Metadata + Commands + CLI Wire (Tasks 11-13)

### Task 11: Wire full CLI + error handling

**Requirement:** REQ-001 through REQ-006, REQ-011
**Files:**

- Modify: `scripts/amnesia.py` — replace skeleton with full CLI
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

```python
# tests/test_cli.py
import json, subprocess, sys
from pathlib import Path

def run_amnesia(args, cwd):
    r = subprocess.run([sys.executable, "scripts/amnesia.py"] + args, capture_output=True, text=True, cwd=cwd)
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
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_cli.py -v`
Expected: FAIL — CLI skeleton has no subcommands

**Step 3: Write minimal implementation**

Replace `scripts/amnesia.py` with the full version:

```python
#!/usr/bin/env python3
"""Amnesia CLI — deterministic memory operations for Claude Code."""
import argparse, json, sys
from pathlib import Path

def ok(data): print(json.dumps({"data": data, "error": None}, ensure_ascii=False))
def err(msg, file=""): print(json.dumps({"data": None, "error": msg, "file": file}, ensure_ascii=False)); sys.exit(1)

def root(args):
    from scripts.paths import get_project_root
    return get_project_root(getattr(args, "project_root", None))

def cmd_entity_load(args):
    from scripts.entity import load_entity
    try:
        data = load_entity(args.name, root(args))
        ok({"found": data is not None, "entity": args.name, **(data or {})})
    except ValueError as e: err(str(e), f".claude/amnesia/memory/{args.name}.json")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_entity_list(args):
    from scripts.entity import list_entities
    try: ok(list_entities(root(args)))
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_entity_diff(args):
    from scripts.entity import diff_entity
    try: ok(diff_entity(args.name, json.loads(args.updates_json), root(args)))
    except json.JSONDecodeError as e: err(f"invalid updates_json: {e}")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_entity_save(args):
    from scripts.entity import save_entity
    try: ok(save_entity(args.name, json.loads(args.updates_json), root(args)))
    except json.JSONDecodeError as e: err(f"invalid updates_json: {e}")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_project_load(args):
    from scripts.project import load_project
    try: ok(load_project(args.name, root(args)))
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_project_save(args):
    from scripts.project import save_project
    try: ok(save_project(args.name, json.loads(args.entry_json), root(args)))
    except json.JSONDecodeError as e: err(f"invalid entry_json: {e}")
    except Exception as e: err(f"unexpected_error: {e}")

def cmd_list(args):
    from scripts.entity import list_entities
    from scripts.paths import get_projects_dir
    r = root(args)
    pd = get_projects_dir(r)
    projects = [d.name for d in pd.iterdir() if d.is_dir()] if pd.exists() else []
    ok({"entities": list_entities(r), "projects": projects})

def main():
    p = argparse.ArgumentParser(prog="amnesia")
    p.add_argument("--project-root", default=None)
    sub = p.add_subparsers(dest="command", required=True)

    ep = sub.add_parser("entity"); es = ep.add_subparsers(dest="subcommand", required=True)
    for name, func, extra in [("load", cmd_entity_load, ["name"]), ("list", cmd_entity_list, []),
                               ("diff", cmd_entity_diff, ["name", "updates_json"]),
                               ("save", cmd_entity_save, ["name", "updates_json"])]:
        sp = es.add_parser(name); sp.set_defaults(func=func)
        for a in extra: sp.add_argument(a)

    pp = sub.add_parser("project"); ps = pp.add_subparsers(dest="subcommand", required=True)
    for name, func, extra in [("load", cmd_project_load, ["name"]), ("save", cmd_project_save, ["name", "entry_json"])]:
        sp = ps.add_parser(name); sp.set_defaults(func=func)
        for a in extra: sp.add_argument(a)

    lp = sub.add_parser("list"); lp.set_defaults(func=cmd_list)

    args = p.parse_args(); args.func(args)

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_cli.py -v`
Expected: PASS

**Step 5: Commit**
Run: `/git commit`

---

### Task 12: Plugin metadata (.claude-plugin/)

**Requirement:** REQ-008
**Files:**

- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`

**Step 3: Create the files**

`.claude-plugin/plugin.json`:

```json
{
  "name": "amnesia",
  "version": "0.1.0",
  "description": "Persistent memory system for Claude Code — deterministic entity and project session memory",
  "author": "nandomoreira",
  "license": "MIT",
  "main": "scripts/amnesia.py",
  "commands": ["commands/amnesia.md", "commands/amnesia/entity.md", "commands/amnesia/project.md"],
  "requires": {"python": ">=3.10", "packages": ["pydantic>=2.0"]}
}
```

`.claude-plugin/marketplace.json`:

```json
{
  "marketplace": "amnesia-plugin",
  "plugins": [{"name": "amnesia", "repo": "nandomoreira/amnesia-claude-code",
               "description": "Persistent memory system for Claude Code"}]
}
```

**Step 4: Validate JSON**
Run: `cat .claude-plugin/plugin.json | python3 -m json.tool`
Expected: valid JSON with no errors

**Step 5: Commit**
Run: `/git commit`

---

### Task 12b: Language detection helper (scripts/lang.py)

**Requirement:** REQ-017
**Files:**

- Create: `scripts/lang.py`
- Create: `tests/test_lang.py`

**Step 1: Write failing tests**

`tests/test_lang.py`:

```python
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
```

Run: `python -m pytest tests/test_lang.py -v`
Expected: 5 tests fail (module not found)

**Step 3: Implement**

`scripts/lang.py`:

```python
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
```

**Step 4: Run tests**
Run: `python -m pytest tests/test_lang.py -v`
Expected: 5 tests pass

**Step 5: Commit**
Run: `/git commit`

> **Note on REQ-018:** English-only rule for stored documents (README, CONTRIBUTING, session logs, entity JSON values) is enforced via instruction in `commands/amnesia/entity.md` and `commands/amnesia/project.md` wrappers — no additional code required.

---

### Task 13: `.md` commands (thin wrappers ≤40 lines)

**Requirement:** REQ-008, REQ-017
**Files:**

- Create: `commands/amnesia.md`
- Create: `commands/amnesia/entity.md`
- Create: `commands/amnesia/project.md`

**Step 3: Create the files**

`commands/amnesia.md` — router that resolves `entity` vs `project`, then dispatches.
`commands/amnesia/entity.md` — load flow + diff/save flow (extract facts → diff → confirm → save).
`commands/amnesia/project.md` — load flow + save flow.

Each file uses `python3 $AMNESIA_PY <subcommand>` via the Bash tool, parses JSON, and presents output in pt-BR.

`AMNESIA_PY` is resolved via a fixed plugin install path or the `AMNESIA_PLUGIN_PATH` environment variable.

**Step 4: Verificar tamanho**
Run: `wc -l commands/amnesia.md commands/amnesia/entity.md commands/amnesia/project.md`
Expected: each file ≤ 40 lines

**Step 5: Commit**
Run: `/git commit`

---

## Group 5 — P2: Integration Tests + Docs (Tasks 14-15)

### Task 14: Integration tests with real fixture

**Requirement:** REQ-003 (roundtrip validation with real data)
**Files:**

- Create: `tests/fixtures/my-project.json`
- Create: `tests/test_integration.py`

**Step 1: Write the failing test**

```python
# tests/test_integration.py
import json
from pathlib import Path
from scripts.entity import load_entity, diff_entity, save_entity

FIXTURES = Path(__file__).parent / "fixtures"

def test_roundtrip_no_data_loss(tmp_project):
    fixture = json.loads((FIXTURES / "my-project.json").read_text())
    (tmp_project / ".claude" / "amnesia" / "memory" / "my-project.json").write_text(json.dumps(fixture))
    loaded = load_entity("my-project", tmp_project)
    original_count = len(loaded["permanent_facts"]["items"])
    updates = {"permanent_facts": {"items": ["integration test fact"], "metadata": {}},
               "decisions": [], "technical_notes": [],
               "current_status": loaded["current_status"],
               "last_session": {"date": "2026-04-03", "summary": "Integration test"}}
    diff = diff_entity("my-project", updates, tmp_project)
    assert diff["diff"]["permanent_facts.items"]["added"] == ["integration test fact"]
    save_entity("my-project", updates, tmp_project)
    reloaded = load_entity("my-project", tmp_project)
    assert len(reloaded["permanent_facts"]["items"]) == original_count + 1
    assert reloaded["$schema"] == "amnesia-entity"

def test_dedup_on_repeated_save(tmp_project):
    fixture = json.loads((FIXTURES / "my-project.json").read_text())
    (tmp_project / ".claude" / "amnesia" / "memory" / "my-project.json").write_text(json.dumps(fixture))
    updates = {"permanent_facts": {"items": ["duplicate fact"], "metadata": {}},
               "decisions": [], "technical_notes": [],
               "current_status": {"phase": "test", "tracker_ids": [], "blockers": []},
               "last_session": {"date": "2026-04-03", "summary": "Test"}}
    save_entity("my-project", updates, tmp_project)
    save_entity("my-project", updates, tmp_project)  # save twice
    reloaded = load_entity("my-project", tmp_project)
    assert reloaded["permanent_facts"]["items"].count("duplicate fact") == 1
```

**Step 2: Run test to verify it fails**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_integration.py -v`
Expected: FAIL — fixture does not exist

**Step 3: Create `tests/fixtures/my-project.json`** with a subset of the real JSON (3 permanent items, 2 decisions, 1 technical note).

**Step 4: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/ -v`
Expected: PASS — all tests

**Step 5: Commit**
Run: `/git commit`

---

### Task 15: Documentation (README + LICENSE + CONTRIBUTING)

**Requirement:** REQ-014, REQ-015, REQ-016
**Files:**

- Create: `README.md`
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`

**Step 3: Create the files in English**

`README.md`: overview, prerequisites (Python 3.10+, Pydantic v2), install via `/plugin install amnesia`, usage examples (`/amnesia my-project`, `/amnesia my-project save`, `/amnesia list`), file structure, JSON output examples, architecture diagram.

`LICENSE`: MIT License 2026, author nandomoreira.

`CONTRIBUTING.md`: dev setup (`pip install pydantic pytest`), run tests (`python -m pytest tests/ -v`), code conventions (always JSON output, never plain text), PR process, `amnesia.py` subcommand architecture.

**Step 4: Verificar**
Run: `wc -l README.md CONTRIBUTING.md`
Expected: README > 50 linhas, CONTRIBUTING > 30 linhas

**Step 5: Commit**
Run: `/git commit`

---

## Group 6 — P3 (Tasks 16-17)

### Task 16: `--project-root` flag validation

**Requirement:** REQ-013
**Files:**

- Modify: `tests/test_cli.py` — add test

**Step 1: Write the failing test**

```python
# add to tests/test_cli.py
def test_project_root_flag(tmp_project, sample_entity):
    import json as _json
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(_json.dumps(sample_entity))
    out = run_amnesia(["--project-root", str(tmp_project), "entity", "load", "test_client"], str(Path.home()))
    assert out["data"]["found"] is True
    assert out["data"]["entity"] == "test_client"
```

**Step 2: Run test to verify it fails/passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_cli.py::test_project_root_flag -v`
Expected: PASS if `get_project_root(override)` already works correctly. FAIL indicates a bug in `paths.py`.

**Step 4: Run full suite**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/ -v`
Expected: PASS — all tests

**Step 5: Commit**
Run: `/git commit`

---

### Task 17: Unified list (entity + projects)

**Requirement:** REQ-012
**Files:**

- Verify: `scripts/amnesia.py` already has `cmd_list` (Task 11)
- Modify: `tests/test_cli.py` — add test

**Step 1: Write the failing test**

```python
# add to tests/test_cli.py
def test_cli_list_unified(tmp_project, sample_entity):
    import json as _json
    (tmp_project / ".claude" / "amnesia" / "memory" / "test_client.json").write_text(_json.dumps(sample_entity))
    (tmp_project / "projects" / "my-project").mkdir(parents=True)
    out = run_amnesia(["--project-root", str(tmp_project), "list"], str(tmp_project))
    assert out["error"] is None
    assert any(e["entity"] == "test_client" for e in out["data"]["entities"])
    assert "my-project" in out["data"]["projects"]
```

**Step 2: Run test to verify it passes**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/test_cli.py::test_cli_list_unified -v`
Expected: PASS (`cmd_list` implemented in Task 11)

**Step 4: Run final full suite**
Run: `cd ~/dev/projects/amnesia-claude-code && python -m pytest tests/ -v --tb=short`
Expected: PASS — all tests pass

**Step 5: Commit final**
Run: `/git commit`
