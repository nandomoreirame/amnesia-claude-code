---
name: amnesia
description: "Amnesia memory system — /amnesia <name>, /amnesia list, /amnesia save"
---

## Amnesia — Memory System

Resolve the CLI path: use `$AMNESIA_PLUGIN_PATH/scripts/amnesia.py` if set, otherwise use the path relative to this command file.

### Usage

- `/amnesia <name>` — Load entity memory (equivalent to `/amnesia entity <name>`)
- `/amnesia list` — List all entities and projects
- `/amnesia save` — Auto-detect and save current entity context

### Routing

1. If argument is `list`: run `python3 $AMNESIA_PY list --project-root $PROJECT_ROOT` via Bash, parse JSON, present as table
2. If argument is `save`: extract facts from conversation, run `entity diff`, present diff, wait for confirmation, then `entity save`
3. If argument is `entity` or `project`: delegate to `/amnesia entity` or `/amnesia project`
4. Otherwise: treat argument as entity name, run `python3 $AMNESIA_PY entity load <name> --project-root $PROJECT_ROOT`

### Language

Detect language via `scripts/lang.py`. Present output in the detected language. All stored data (JSON values, session logs) MUST be in English regardless of display language.
