# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Amnesia Claude Code Plugin** — a native Claude Code plugin that makes memory operations (merge, dedup, validation) deterministic through `amnesia.py` (Python CLI), replacing the previous natural-language `.md` approach.

## Architecture

### Separation of responsibilities

- **`scripts/amnesia.py`** — Python CLI entrypoint; delegates to modules in `scripts/`
- **`scripts/`** — Core logic modules: `schema.py` (Pydantic v2 models + migration), `entity.py` (load/diff/save/list), `project.py` (session logs + git log), `merge.py` (deterministic dedup), `paths.py` (project root detection), `lang.py` (language detection), `native_memory.py` (read-only native MEMORY.md integration)
- **`commands/*.md`** — thin orchestrators (≤40 lines each); no embedded logic
- **Claude** — handles semantic work: fact extraction, translation, and user presentation

### CLI invocation

All CLI calls go through `scripts/amnesia.py` with `--project-root` flag:

```bash
python3 scripts/amnesia.py entity load <name> --project-root /path
python3 scripts/amnesia.py entity diff <name> '<updates_json>' --project-root /path
python3 scripts/amnesia.py entity save <name> '<updates_json>' --project-root /path
python3 scripts/amnesia.py entity list --project-root /path
python3 scripts/amnesia.py project load <name> --project-root /path
python3 scripts/amnesia.py project save <name> '<entry_json>' --project-root /path
python3 scripts/amnesia.py list --project-root /path
python3 scripts/amnesia.py sync --project-root /path
```

Output is always structured JSON: `{"data": ..., "error": null}` — never plain text.

### Data structure (at target project)

```
<project>/.claude/amnesia/
├── memory/<name>.json     # Entities (schema: amnesia-entity)
└── sessions/YYYY-MM-DD.md # Session logs
```

### Save flow (`/amnesia save` — unified)

1. Detect context (entity name) from conversation — client, project, or root project name as fallback
2. `entity diff` → returns JSON preview with `added`, `updated`, `skipped` per section
3. Present diff to user → wait for confirmation
4. `entity save` → write merged entity memory
5. `project save` → write session log to `sessions/YYYY-MM-DD.md`

## Commands

```bash
# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_merge.py

# Run a specific test
python -m pytest tests/test_merge.py::test_merge_list_dedup -v

# Run with coverage
python -m pytest --cov=scripts
```

## Merge Logic (REQ-003)

- `permanent_facts.items` and `technical_notes` — dedup by normalization (`strip + lowercase` for comparison, preserve original casing)
- `decisions` — dedup by composite key `(date, author, decision[:50])`
- `current_status` and `last_session` — replaced entirely (not merged)

## Schema Migration (REQ-007)

`etl-client-memory-v1` → `amnesia-entity`: migrated automatically on read via `schema.migrate_v1()`. Key mappings: `client` → `entity`, `jira_tickets` → `tracker_ids`, flat `permanent_facts` fields → `metadata` dict.

## Edge Cases

| Case | Behavior |
|------|----------|
| Corrupted JSON | `{"error": "invalid_json", "file": "..."}` via ValueError |
| `git rev-parse` fails | Fallback to `$PWD` |
| Missing `memory/` directory | Created automatically by `paths.get_memory_dir()` |
| Language detection | Reads `language` from local then global `settings.json`, defaults to `"en"` |

## Native Memory Sync

Bidirectional integration with Claude Code's native `MEMORY.md` system (`~/.claude/projects/<slug>/memory/`):

- **`scripts/native_memory.py`** — read-only operations: path resolution by slug, YAML frontmatter parsing, entity relevance filtering, sync content generation
- **`amnesia.py sync`** — generates sync report (entity→native mapping, orphan detection, index limit check)
- **Writing to native memory** — delegated to Claude via commands `.md`; `amnesia.py` never writes to native memory
- **Mapping:** `current_status`→project, `decisions`→feedback, `metadata`→reference. `items` and `technical_notes` are NOT synced.
- **Index limit:** warns when MEMORY.md exceeds 180 lines (native truncates at 200)

## Specs

- Plugin spec: `docs/specs/2026-04-03-amnesia-plugin.md` (REQ-001–REQ-018)
- Native Memory Sync spec: `docs/specs/2026-04-03-native-memory-sync.md` (REQ-019–REQ-025)
- Plans: `docs/plans/2026-04-03-amnesia-plugin.md`, `docs/plans/2026-04-03-native-memory-sync.md`
