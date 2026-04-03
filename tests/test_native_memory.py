"""Tests for native MEMORY.md integration (scripts/native_memory.py)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.native_memory import (
    project_root_to_slug,
    resolve_native_memory_dir,
    read_native_memories,
    read_memory_md_index,
    filter_memories_by_entity,
    get_native_context_for_entity,
    check_index_limit,
    map_entity_to_native_memories,
    generate_sync_report,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def native_memory_dir(tmp_path):
    d = tmp_path / "memory"
    d.mkdir(parents=True)
    return d


# ---------------------------------------------------------------------------
# Task 1: Path resolution by slug (REQ-019)
# ---------------------------------------------------------------------------

class TestPathResolution:
    def test_slug_simple_path(self):
        assert project_root_to_slug("/home/user/project") == "home-user-project"

    def test_slug_strips_leading_dash(self):
        # Leading / becomes leading - which is stripped
        assert project_root_to_slug("/home/user/project") == "home-user-project"

    def test_slug_nested_path(self):
        assert project_root_to_slug("/home/user/dev/projects/my-app") == "home-user-dev-projects-my-app"

    def test_slug_trailing_slash(self):
        assert project_root_to_slug("/home/user/project/") == "home-user-project"

    def test_resolve_native_memory_dir(self):
        result = resolve_native_memory_dir("/home/user/project")
        expected = Path.home() / ".claude" / "projects" / "-home-user-project" / "memory"
        assert result == expected

    def test_resolve_native_memory_dir_with_trailing_slash(self):
        result = resolve_native_memory_dir("/home/user/project/")
        expected = Path.home() / ".claude" / "projects" / "-home-user-project" / "memory"
        assert result == expected


# ---------------------------------------------------------------------------
# Task 2: Read native memory files (REQ-019, REQ-020)
# ---------------------------------------------------------------------------

class TestReadNativeMemories:
    def test_empty_dir(self, native_memory_dir):
        result = read_native_memories(native_memory_dir)
        assert result == []

    def test_with_valid_files(self, native_memory_dir):
        (native_memory_dir / "project_status.md").write_text(
            "---\nname: project status\ndescription: Current project phase\ntype: project\n---\n\nPhase: development\n"
        )
        (native_memory_dir / "user_pref.md").write_text(
            "---\nname: user preference\ndescription: User likes TDD\ntype: feedback\n---\n\nUser prefers TDD workflow.\n"
        )
        result = read_native_memories(native_memory_dir)
        assert len(result) == 2
        assert result[0]["name"] == "project status"
        assert result[0]["type"] == "project"
        assert "Phase: development" in result[0]["content"]

    def test_dir_not_exists(self, tmp_path):
        result = read_native_memories(tmp_path / "nonexistent")
        assert result == []

    def test_corrupted_yaml_skipped(self, native_memory_dir):
        (native_memory_dir / "bad.md").write_text("---\n: invalid: yaml: {{{\n---\nContent\n")
        (native_memory_dir / "good.md").write_text(
            "---\nname: good\ndescription: A good memory\ntype: reference\n---\n\nGood content\n"
        )
        result = read_native_memories(native_memory_dir)
        assert len(result) == 1
        assert result[0]["name"] == "good"

    def test_no_frontmatter_skipped(self, native_memory_dir):
        (native_memory_dir / "plain.md").write_text("Just plain text without frontmatter\n")
        result = read_native_memories(native_memory_dir)
        assert len(result) == 0

    def test_memory_md_index_excluded(self, native_memory_dir):
        (native_memory_dir / "MEMORY.md").write_text("- [a](a.md) — desc\n")
        (native_memory_dir / "real.md").write_text(
            "---\nname: real\ndescription: real memory\ntype: user\n---\n\nContent\n"
        )
        result = read_native_memories(native_memory_dir)
        assert len(result) == 1
        assert result[0]["name"] == "real"


class TestReadMemoryMdIndex:
    def test_read_index(self, native_memory_dir):
        (native_memory_dir / "MEMORY.md").write_text(
            "- [Status](status.md) — current phase\n- [Pref](pref.md) — user pref\n"
        )
        lines = read_memory_md_index(native_memory_dir)
        assert len(lines) == 2
        assert "Status" in lines[0]

    def test_index_not_exists(self, tmp_path):
        lines = read_memory_md_index(tmp_path / "nonexistent")
        assert lines == []

    def test_empty_index(self, native_memory_dir):
        (native_memory_dir / "MEMORY.md").write_text("")
        lines = read_memory_md_index(native_memory_dir)
        assert lines == []


# ---------------------------------------------------------------------------
# Task 3: Filter memories by entity (REQ-020)
# ---------------------------------------------------------------------------

class TestFilterByEntity:
    def test_matches_by_name_prefix(self, native_memory_dir):
        (native_memory_dir / "amnesia-myapp-status.md").write_text(
            "---\nname: amnesia-myapp-status\ndescription: myapp phase\ntype: project\n---\n\nPhase: dev\n"
        )
        (native_memory_dir / "amnesia-other-status.md").write_text(
            "---\nname: amnesia-other-status\ndescription: other phase\ntype: project\n---\n\nPhase: done\n"
        )
        memories = read_native_memories(native_memory_dir)
        filtered = filter_memories_by_entity(memories, "myapp")
        assert len(filtered) == 1
        assert filtered[0]["name"] == "amnesia-myapp-status"

    def test_matches_by_content(self, native_memory_dir):
        (native_memory_dir / "project_ref.md").write_text(
            "---\nname: project reference\ndescription: deployment info\ntype: reference\n---\n\nmyapp uses Docker\n"
        )
        memories = read_native_memories(native_memory_dir)
        filtered = filter_memories_by_entity(memories, "myapp")
        assert len(filtered) == 1

    def test_matches_by_description(self, native_memory_dir):
        (native_memory_dir / "desc.md").write_text(
            "---\nname: some-memory\ndescription: about myapp deployment\ntype: reference\n---\n\nGeneric content\n"
        )
        memories = read_native_memories(native_memory_dir)
        filtered = filter_memories_by_entity(memories, "myapp")
        assert len(filtered) == 1

    def test_no_match(self, native_memory_dir):
        (native_memory_dir / "unrelated.md").write_text(
            "---\nname: unrelated\ndescription: nothing here\ntype: user\n---\n\nCompletely unrelated\n"
        )
        memories = read_native_memories(native_memory_dir)
        filtered = filter_memories_by_entity(memories, "myapp")
        assert len(filtered) == 0


# ---------------------------------------------------------------------------
# Task 4: get_native_context_for_entity facade (REQ-020)
# ---------------------------------------------------------------------------

class TestGetNativeContext:
    def test_returns_relevant(self, native_memory_dir):
        (native_memory_dir / "amnesia-myapp-status.md").write_text(
            "---\nname: amnesia-myapp-status\ndescription: myapp current phase\ntype: project\n---\n\nPhase: dev\n"
        )
        (native_memory_dir / "unrelated.md").write_text(
            "---\nname: unrelated\ndescription: something else\ntype: user\n---\n\nNot related\n"
        )
        result = get_native_context_for_entity("myapp", native_memory_dir)
        assert len(result) == 1
        assert result[0]["name"] == "amnesia-myapp-status"

    def test_dir_missing(self, tmp_path):
        result = get_native_context_for_entity("myapp", tmp_path / "nonexistent")
        assert result == []


# ---------------------------------------------------------------------------
# Task 5: Entity-to-native mapping (REQ-021, REQ-024)
# ---------------------------------------------------------------------------

class TestMapEntityToNative:
    def test_full_mapping(self):
        entity = {
            "$schema": "amnesia-entity", "entity": "myapp",
            "current_status": {"phase": "development", "tracker_ids": ["OL-150"], "blockers": []},
            "decisions": [
                {"date": "2026-04-01", "author": "user", "decision": "Use PostgreSQL for persistence"},
                {"date": "2026-04-02", "author": "user", "decision": "Deploy via Docker Compose"},
            ],
            "permanent_facts": {
                "metadata": {"data_source": "REST API", "deploy_target": "AWS"},
                "items": ["Uses Python 3.12", "Has CI/CD pipeline"],
            },
            "technical_notes": ["Runs on port 8080"],
        }
        result = map_entity_to_native_memories(entity)
        types = [m["type"] for m in result]
        assert types.count("project") == 1
        assert types.count("feedback") == 2
        assert types.count("reference") == 1
        # Status
        status_mem = [m for m in result if m["type"] == "project"][0]
        assert status_mem["file_name"] == "amnesia-myapp-status"
        assert "development" in status_mem["content"]
        assert "OL-150" in status_mem["content"]
        # Decisions
        decision_mems = [m for m in result if m["type"] == "feedback"]
        assert "PostgreSQL" in decision_mems[0]["content"]
        # Metadata
        ref_mem = [m for m in result if m["type"] == "reference"][0]
        assert "data_source" in ref_mem["content"]
        assert "deploy_target" in ref_mem["content"]

    def test_excludes_items_and_notes(self):
        """REQ-024: items and technical_notes must NOT appear in native memories."""
        entity = {
            "$schema": "amnesia-entity", "entity": "myapp",
            "current_status": {"phase": "dev", "tracker_ids": [], "blockers": []},
            "decisions": [],
            "permanent_facts": {"metadata": {}, "items": ["Secret item that should not sync"]},
            "technical_notes": ["Note that should not sync"],
        }
        result = map_entity_to_native_memories(entity)
        all_content = " ".join(m["content"] for m in result)
        assert "Secret item" not in all_content
        assert "Note that should not sync" not in all_content

    def test_empty_sections(self):
        entity = {
            "$schema": "amnesia-entity", "entity": "empty",
            "current_status": {"phase": "", "tracker_ids": [], "blockers": []},
            "decisions": [],
            "permanent_facts": {"metadata": {}, "items": []},
            "technical_notes": [],
        }
        result = map_entity_to_native_memories(entity)
        # Only status is always generated
        assert len(result) == 1
        assert result[0]["type"] == "project"


# ---------------------------------------------------------------------------
# Task 6: Index line count check (REQ-025)
# ---------------------------------------------------------------------------

class TestCheckIndexLimit:
    def test_under_limit(self, native_memory_dir):
        (native_memory_dir / "MEMORY.md").write_text("- [A](a.md) — something\n" * 10)
        ok, count = check_index_limit(native_memory_dir)
        assert ok is True
        assert count == 10

    def test_at_threshold(self, native_memory_dir):
        (native_memory_dir / "MEMORY.md").write_text("- [A](a.md) — something\n" * 180)
        ok, count = check_index_limit(native_memory_dir)
        assert ok is True
        assert count == 180

    def test_over_limit(self, native_memory_dir):
        (native_memory_dir / "MEMORY.md").write_text("- [A](a.md) — something\n" * 181)
        ok, count = check_index_limit(native_memory_dir)
        assert ok is False
        assert count == 181

    def test_no_file(self, tmp_path):
        ok, count = check_index_limit(tmp_path / "nonexistent")
        assert ok is True
        assert count == 0


# ---------------------------------------------------------------------------
# Task 7: generate_sync_report (REQ-023)
# ---------------------------------------------------------------------------

class TestGenerateSyncReport:
    def test_full_report(self, tmp_path):
        mem_dir = tmp_path / ".claude" / "amnesia" / "memory"
        mem_dir.mkdir(parents=True)
        entity = {
            "$schema": "amnesia-entity", "entity": "myapp",
            "current_status": {"phase": "dev", "tracker_ids": [], "blockers": []},
            "decisions": [{"date": "2026-04-01", "author": "user", "decision": "Use Redis"}],
            "permanent_facts": {"metadata": {"source": "API"}, "items": ["fact"]},
            "technical_notes": ["note"],
        }
        (mem_dir / "myapp.json").write_text(json.dumps(entity))
        # Native dir with one existing + one orphan
        native_dir = tmp_path / "native_memory"
        native_dir.mkdir(parents=True)
        (native_dir / "amnesia-myapp-status.md").write_text(
            "---\nname: amnesia-myapp-status\ndescription: old\ntype: project\n---\n\nPhase: old\n"
        )
        (native_dir / "orphan-memory.md").write_text(
            "---\nname: orphan-memory\ndescription: no entity\ntype: user\n---\n\nOrphan content\n"
        )
        report = generate_sync_report(tmp_path, native_dir)
        assert "myapp" in report["entities"]
        assert len(report["entities"]["myapp"]["memories"]) > 0
        assert "orphan-memory.md" in report["orphan_native_files"]

    def test_index_over_limit(self, tmp_path):
        mem_dir = tmp_path / ".claude" / "amnesia" / "memory"
        mem_dir.mkdir(parents=True)
        entity = {
            "$schema": "amnesia-entity", "entity": "app",
            "current_status": {"phase": "dev", "tracker_ids": [], "blockers": []},
            "decisions": [], "permanent_facts": {"metadata": {}, "items": []},
            "technical_notes": [],
        }
        (mem_dir / "app.json").write_text(json.dumps(entity))
        native_dir = tmp_path / "native"
        native_dir.mkdir(parents=True)
        (native_dir / "MEMORY.md").write_text("- [A](a.md) — x\n" * 185)
        report = generate_sync_report(tmp_path, native_dir)
        assert report["index_warning"] is True
        assert report["index_line_count"] == 185


# ---------------------------------------------------------------------------
# Task 8: CLI sync subcommand (REQ-023)
# ---------------------------------------------------------------------------

class TestCliSync:
    def test_sync_subcommand(self, tmp_path):
        mem_dir = tmp_path / ".claude" / "amnesia" / "memory"
        mem_dir.mkdir(parents=True)
        entity = {
            "$schema": "amnesia-entity", "entity": "testapp",
            "current_status": {"phase": "active", "tracker_ids": [], "blockers": []},
            "decisions": [], "permanent_facts": {"metadata": {}, "items": []},
            "technical_notes": [],
        }
        (mem_dir / "testapp.json").write_text(json.dumps(entity))
        result = subprocess.run(
            [sys.executable, "scripts/amnesia.py", "sync", "--project-root", str(tmp_path)],
            capture_output=True, text=True,
            cwd=str(Path(__file__).parent.parent),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["error"] is None
        assert "testapp" in data["data"]["entities"]


# ---------------------------------------------------------------------------
# Task 9: entity.md has native write instructions (REQ-021)
# ---------------------------------------------------------------------------

class TestCommandFiles:
    def test_entity_command_has_native_instructions(self):
        cmd_file = Path(__file__).parent.parent / "commands" / "amnesia" / "entity.md"
        content = cmd_file.read_text()
        assert "native memory" in content.lower()
        assert "amnesia-" in content
        assert "project" in content
        assert "feedback" in content
        assert "reference" in content

    # Task 10: sync.md exists + amnesia.md routes sync
    def test_sync_command_exists(self):
        cmd_file = Path(__file__).parent.parent / "commands" / "amnesia" / "sync.md"
        assert cmd_file.exists()
        content = cmd_file.read_text()
        assert "sync" in content.lower()
        assert "orphan" in content.lower()

    def test_amnesia_routes_sync(self):
        cmd_file = Path(__file__).parent.parent / "commands" / "amnesia.md"
        content = cmd_file.read_text()
        assert "sync" in content.lower()
