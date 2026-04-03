# Amnesia Claude Code Plugin

A native Claude Code plugin that transforms the Amnesia memory system into a deterministic, structured memory layer for AI-assisted development workflows. Instead of relying on LLM reasoning for merge, dedup, and validation, all core operations are handled by `amnesia.py` — a Python CLI that guarantees consistent, predictable behavior.

## Prerequisites

- Python 3.10+
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- Claude Code (with plugin support)

## Installation

1. Install the Python dependency:

```bash
pip install pydantic
```

1. Install the plugin via Claude Code:

```
/plugin install
```

Or install manually by cloning this repository and pointing Claude Code to the `.claude-plugin/plugin.json` manifest.

## Usage

### Load an entity

```
/amnesia my-project
```

Loads the entity named `my-project` from `.claude/amnesia/memory/my-project.json` in the current project root.

### List all entities

```
/amnesia list
```

Returns a structured list of all entities and projects tracked in the current workspace.

### Save an entity

```
/amnesia my-project save
```

Claude extracts facts from the current session, presents a diff for confirmation, then writes the updated entity to disk.

### Entity subcommands

```
/amnesia entity my-project     # Load a specific entity
/amnesia project my-project # Load a specific project
```

## File Structure

```
<project>/
└── .claude/
    └── amnesia/
        ├── memory/
        │   └── <entity-name>.json   # Entity records (schema: amnesia-entity)
        ├── projects/
        │   └── <project-name>.json  # Project records
        └── sessions/
            └── YYYY-MM-DD.md        # Session logs
```

## JSON Output Format

All CLI operations return structured JSON. Example:

```json
{
  "data": {
    "found": true,
    "entity": "my-project",
    "$schema": "amnesia-entity",
    "permanent_facts": {
      "metadata": { "data_source": "Sienge API" },
      "items": ["Client uses Sienge ERP for financial data"]
    },
    "decisions": [],
    "current_status": { "phase": "processing", "tracker_ids": ["OL-150"] },
    "last_session": { "date": "2026-04-01", "summary": "Processed data" },
    "technical_notes": []
  },
  "error": null
}
```

On error:

```json
{
  "data": null,
  "error": "invalid_json",
  "file": ".claude/amnesia/memory/broken.json"
}
```

## Architecture Overview

```
amnesia.py         ← Python CLI: deterministic I/O, merge, dedup, Pydantic v2 validation
commands/*.md      ← Thin Claude Code command wrappers (≤40 lines each)
Claude             ← Handles semantic work: fact extraction, translation, user presentation
```

**Key principle:** `amnesia.py` never produces plain text. All output is structured JSON so Claude can process it reliably without ambiguity.

### Save flow (two required steps)

1. `amnesia.py entity diff <name> <updates_json>` — returns JSON preview (`added`, `updated`, `skipped`)
2. Present diff to the user — wait for confirmation
3. `amnesia.py entity save <name> <updates_json>` — write changes

### Merge / dedup rules

| Field | Behavior |
|-------|----------|
| `permanent_facts.items` | Deduplicated by normalization (strip + lowercase for comparison, preserve original) |
| `technical_notes` | Deduplicated by normalization |
| `decisions` | Deduplicated by `(date, author, decision[:50])` |
| `current_status` | Replaced entirely on each save |
| `last_session` | Replaced entirely on each save |

## Schema Migration

Legacy entities using the `etl-client-memory-v1` schema are automatically migrated to `amnesia-entity` on the next write, without data loss.

## License

MIT — see [LICENSE](LICENSE).
