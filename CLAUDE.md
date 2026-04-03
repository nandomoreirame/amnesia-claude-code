# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Amnesia Claude Code Plugin** — a native Claude Code plugin that makes memory operations (merge, dedup, validation) deterministic through `amnesia.py` (Python CLI), replacing the previous natural-language `.md` approach.

## Architecture

### Separation of responsibilities

- **`scripts/amnesia.py`** — Python CLI entrypoint; delegates to modules in `scripts/`
- **`scripts/`** — Core logic modules: `schema.py` (Pydantic v2 models + migration), `entity.py` (load/diff/save/list), `project.py` (session logs + git log), `merge.py` (deterministic dedup), `paths.py` (project root detection), `lang.py` (language detection)
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
```

Output is always structured JSON: `{"data": ..., "error": null}` — never plain text.

### Data structure (at target project)

```
<project>/.claude/amnesia/
├── memory/<name>.json     # Entities (schema: amnesia-entity)
├── sessions/YYYY-MM-DD.md # Session logs
<project>/projects/<name>/ # Project directories (for project load)
```

### Save flow (two required steps)

1. `entity diff` → returns JSON preview with `added`, `updated`, `skipped` per section
2. Present diff to user → wait for confirmation
3. `entity save` → write merged changes

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

## Spec

Full spec with all REQ IDs: `docs/specs/2026-04-03-amnesia-plugin.md`
Implementation plan (17 tasks): `docs/plans/2026-04-03-amnesia-plugin.md`
