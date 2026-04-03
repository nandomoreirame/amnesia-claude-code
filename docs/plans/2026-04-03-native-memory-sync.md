# Plan: Native Memory Sync

> **Spec:** docs/specs/2026-04-03-native-memory-sync.md

**Goal:** Bidirectional integration between Amnesia plugin and Claude Code's native MEMORY.md — amnesia.py reads native memories, commands instruct Claude to write.

**Architecture:** New module `scripts/native_memory.py` handles all read-only operations (path resolution, YAML parsing, relevance filtering, sync content generation). CLI gains `sync` subcommand. Commands `.md` are updated to instruct Claude to write to native memory after save.

**Tech Stack:** Python 3.10+, Pydantic v2, PyYAML (frontmatter parsing), existing test infrastructure (pytest)

**Total Tasks:** 10
**Estimated Complexity:** medium (7 REQs, 10 tasks)

---

## P1 Tasks (REQ-019 → REQ-023)

### Task 1: Path resolution by slug (REQ-019)

**Requirement:** REQ-019
**Files:**
- Create: `scripts/native_memory.py`
- Test: `tests/test_native_memory.py`

### Task 2: Read native memory files with YAML frontmatter (REQ-019, REQ-020)

**Requirement:** REQ-019, REQ-020
**Files:**
- Modify: `scripts/native_memory.py`
- Test: `tests/test_native_memory.py`

### Task 3: Filter native memories by entity relevance (REQ-020)

**Requirement:** REQ-020
**Files:**
- Modify: `scripts/native_memory.py`
- Test: `tests/test_native_memory.py`

### Task 4: Integrate native memory context into entity load (REQ-020)

**Requirement:** REQ-020
**Files:**
- Modify: `scripts/native_memory.py`
- Test: `tests/test_native_memory.py`

### Task 5: Selective mapping — Amnesia entity to native memory content (REQ-021, REQ-024)

**Requirement:** REQ-021, REQ-024
**Files:**
- Modify: `scripts/native_memory.py`
- Test: `tests/test_native_memory.py`

### Task 6: Index line count check (REQ-025)

**Requirement:** REQ-025
**Files:**
- Modify: `scripts/native_memory.py`
- Test: `tests/test_native_memory.py`

### Task 7: Sync subcommand — generate sync content (REQ-023)

**Requirement:** REQ-023
**Files:**
- Modify: `scripts/native_memory.py`
- Test: `tests/test_native_memory.py`

### Task 8: Register `sync` subcommand in CLI (REQ-023)

**Requirement:** REQ-023
**Files:**
- Modify: `scripts/amnesia.py`
- Test: `tests/test_native_memory.py`

### Task 9: Update `entity.md` command for native memory write instructions (REQ-021)

**Requirement:** REQ-021
**Files:**
- Modify: `commands/amnesia/entity.md`

### Task 10: Create `sync.md` command and update `amnesia.md` routing (REQ-022, REQ-023)

**Requirement:** REQ-022, REQ-023
**Files:**
- Create: `commands/amnesia/sync.md`
- Modify: `commands/amnesia.md`

---

## Dependency Graph

```
Task 1 (path resolution)
  └── Task 2 (read native files)
       └── Task 3 (filter by entity)
            └── Task 4 (get_native_context facade)
  └── Task 6 (index limit check)

Task 5 (entity→native mapping)
  └── Task 7 (sync report generation)
       └── Task 8 (CLI sync subcommand)

Task 9 (entity.md update) — depends on Tasks 5, 8
Task 10 (sync.md + routing) — depends on Task 8
```

## Requirement Traceability

| Task | REQs | Priority |
|------|------|----------|
| Task 1 | REQ-019 | P1 |
| Task 2 | REQ-019, REQ-020 | P1 |
| Task 3 | REQ-020 | P1 |
| Task 4 | REQ-020 | P1 |
| Task 5 | REQ-021, REQ-024 | P1, P2 |
| Task 6 | REQ-025 | P2 |
| Task 7 | REQ-023 | P1 |
| Task 8 | REQ-023 | P1 |
| Task 9 | REQ-021 | P1 |
| Task 10 | REQ-022, REQ-023 | P1 |
