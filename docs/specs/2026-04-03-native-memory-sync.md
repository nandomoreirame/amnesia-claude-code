# Spec: Native Memory Sync

## Problem Statement

The Amnesia plugin operates with its own memory system in `.claude/amnesia/memory/*.json`, completely independent of Claude Code's native memory (`~/.claude/projects/<hash>/memory/`). Facts saved in Amnesia do not reinforce native memory, and native memories are invisible when loading entities. Users must maintain two systems manually.

## Goals

- Bidirectional integration: Amnesia reads native memories as context, Claude writes to native memory after Amnesia saves
- Automatic path resolution without configuration
- Selective sync: only meaningful data flows to native memory (status, decisions, metadata — not granular items)
- New `/amnesia sync` command for full synchronization

## Context

The Amnesia plugin (v0.1.0) manages entities with deterministic merge/dedup via `amnesia.py`. Claude Code's native memory stores user preferences, feedback, project context, and references in `~/.claude/projects/<slug>/memory/` with markdown files using YAML frontmatter. The two systems serve complementary purposes but have no communication channel.

## Requirements

### P1 (MVP)

1. **[REQ-019]** WHEN `amnesia.py` needs to resolve the native MEMORY.md path THEN it SHALL derive it automatically by converting the project root to a slug (replace `/` with `-`, strip leading `-`) and looking up `~/.claude/projects/<slug>/memory/MEMORY.md`.

2. **[REQ-020]** WHEN the user invokes `/amnesia <name>` and native MEMORY.md exists THEN the system SHALL read all memory files in the native memory directory, filter for entries relevant to the entity (by name, keywords, or scope), and present them as additional context alongside the entity data.

3. **[REQ-021]** WHEN `amnesia.py entity save` completes successfully THEN the command `.md` SHALL instruct Claude to write to native memory: `current_status` as a `project` type memory, recent `decisions` as `feedback` type memories, and `permanent_facts.metadata` as a `reference` type memory. Each memory file uses the native frontmatter format (`name`, `description`, `type`). Writing is done by Claude via its native memory mechanism, not by `amnesia.py` directly.

4. **[REQ-022]** WHEN the user invokes `/amnesia save` THEN before saving, the system SHALL read native MEMORY.md memories and present any relevant ones as additional context (not auto-merged into the entity).

5. **[REQ-023]** WHEN the user invokes `/amnesia sync` THEN the system SHALL iterate all entities in `.claude/amnesia/memory/*.json`, instruct Claude to synchronize each to the native MEMORY.md using the mapping defined in REQ-021, and report a summary of created/updated/skipped memory files. It SHALL also list native memories that have no corresponding Amnesia entity.

### P2 (Should Have)

1. **[REQ-024]** WHEN synchronizing to native MEMORY.md THEN `permanent_facts.items` and `technical_notes` SHALL NOT be written to native memory (too granular, would pollute the index).

2. **[REQ-025]** WHEN the native MEMORY.md index exceeds 180 lines THEN the sync SHALL warn the user and skip writing new entries to avoid truncation (native index truncates after 200 lines).

## Edge Cases

| Case | Behavior |
|------|----------|
| Native directory does not exist | `amnesia.py` (read) returns empty list. On write, the command `.md` instructs Claude to use its native memory mechanism, which creates the directory automatically. |
| Native MEMORY.md does not exist | Same — Claude creates it on first write via its native mechanism. |
| Entity has no match in native memory | Sync creates memory files for the first time via Claude. |
| Native memory has no corresponding entity | `/amnesia sync` lists as "orphan memories" in the final report. Does not delete. |
| Native MEMORY.md index exceeds 180 lines | Sync warns the user and skips new entries (REQ-025). Existing entries are still updated. |
| Corrupted native memory file (invalid YAML) | Read ignores the file and reports a warning. Does not block the operation. |
| Multiple entities generate memory with same name | Prefix `amnesia-<entity>-` on native file names avoids collision. |

## Architecture Decisions

1. **Path resolution by slug** — Native MEMORY.md path is derived automatically by converting the project root to a slug. No configuration or extra arguments needed. Discarded: `--memory-path` flag (unnecessary complexity for MVP).

2. **Read as context, not merge** — Native memories are presented as extra context alongside the entity. They are not incorporated into the entity JSON automatically. Discarded: auto-merge (risk of polluting the entity with volatile data and creating duplication between systems).

3. **Selective mapping Amnesia → native** — Only `current_status`, recent `decisions`, and `permanent_facts.metadata` are synchronized. `items` and `technical_notes` stay only in Amnesia. Discarded: full sync (would pollute native MEMORY.md with overly granular items).

4. **Separation CLI vs Claude for native memory** — `amnesia.py` only reads the native MEMORY.md (module `scripts/native_memory.py` with read and path resolution functions). Writing is done by the command `.md` which instructs Claude to use its native memory mechanism (equivalent to writing via Write tool to `~/.claude/projects/<slug>/memory/`). This ensures the directory and MEMORY.md index are managed by Claude Code itself, not by the Python script.

5. **New subcommand `sync`** — Added to the CLI as `amnesia.py sync --project-root <path>` (read-only: generates the content to sync). The command `.md` handles the actual write via Claude.

## Constraints

- `amnesia.py` has read-only access to native MEMORY.md — writing is Claude's responsibility via its memory system
- Path resolution by slug is deterministic but depends on Claude Code's naming convention (if the convention changes, the read module breaks)
- `/amnesia sync` requires Claude to execute multiple sequential writes to native MEMORY.md — may be slow for projects with many entities
- Native MEMORY.md index has a ~200 line limit — sync must respect this
- No new dependencies beyond what already exists (Python 3.10+, Pydantic v2)

## Out of Scope

| Item | Reason |
|------|--------|
| Delete orphan native memories | `/amnesia sync` lists but does not remove — risk of deleting manually created memories |
| Sync native MEMORY.md → entity (auto merge) | Decision made: read as context, no merge. Could be future P2. |
| Resolve conflicts between Amnesia and native | They are complementary systems, not competitive. Amnesia is source of truth for entities. |
| Direct filesystem write to native memory via `amnesia.py` | Delegated to Claude via its memory mechanism |
| Multi-project sync in a single command | Sync operates on the current project (`--project-root`) |

## Test Strategy

- **Unit:** `native_memory.py` module — path resolution by slug, reading native memory files, YAML frontmatter parsing, relevance filtering by entity, handling of missing directory/file
- **Unit:** `sync` subcommand — mapping Amnesia sections to native types, markdown content generation with correct frontmatter, 180-line index limit detection
- **Integration:** Full roundtrip — save entity via `entity save`, verify `amnesia.py` reads existing native memories and returns as extra context, verify sync mapping generates correct content
- **Integration:** Fixture with populated native directory — test reading with multiple `.md` files, including corrupted files and files without frontmatter

## Requirement Traceability

| ID | Description | Priority | Status |
|----|-------------|----------|--------|
| REQ-019 | Native MEMORY.md path resolution by slug | P1 | Pending |
| REQ-020 | Read native memories as context on entity load | P1 | Pending |
| REQ-021 | Write to native memory after entity save (via Claude) | P1 | Pending |
| REQ-022 | Read native memories as context before entity save | P1 | Pending |
| REQ-023 | `/amnesia sync` full synchronization command | P1 | Pending |
| REQ-024 | Exclude items and technical_notes from native sync | P2 | Pending |
| REQ-025 | Warn and skip when native index exceeds 180 lines | P2 | Pending |
