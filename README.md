# Amnesia Claude Code Plugin

A native Claude Code plugin that transforms the Amnesia memory system into a deterministic, structured memory layer for AI-assisted development workflows. Instead of relying on LLM reasoning for merge, dedup, and validation, all core operations are handled by `amnesia.py` — a Python CLI that guarantees consistent, predictable behavior.

## Prerequisites

- Python 3.10+
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- Claude Code (with plugin support)

## Installation

### From GitHub (recommended)

1. Add the marketplace:

```
/plugin marketplace add nandomoreirame/amnesia-claude-code
```

1. Install the plugin (choose user or project scope when prompted):

```
/plugin install amnesia@amnesia-plugin
```

1. Reload plugins:

```
/reload-plugins
```

### Manual installation

1. Clone this repository:

```bash
git clone https://github.com/nandomoreirame/amnesia-claude-code.git
```

1. Add as a local marketplace:

```
/plugin marketplace add /path/to/amnesia-claude-code
```

1. Install and reload:

```
/plugin install amnesia@amnesia-plugin
/reload-plugins
```

### Python dependency

The plugin requires Python 3.10+ and Pydantic v2:

```bash
pip install pydantic
```

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
