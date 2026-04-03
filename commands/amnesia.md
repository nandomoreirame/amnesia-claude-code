---
name: amnesia
description: "Amnesia memory system — /amnesia <name>, /amnesia list, /amnesia save"
argument-hint: "[<name> | list | save | entity | sync]"
---

## Amnesia — Memory System

Resolve the CLI path: use `$AMNESIA_PLUGIN_PATH/scripts/amnesia.py` if set, otherwise use the path relative to this command file.

### Usage

- `/amnesia <name>` — Load entity memory
- `/amnesia list` — List all entities and projects
- `/amnesia save` — Save entity + session log for current context
- `/amnesia sync` — Synchronize all entities to Claude Code native memory

### Routing

1. If argument is `list`: run `python3 $AMNESIA_PY list --project-root $PROJECT_ROOT` via Bash, parse JSON, present as table
2. If argument is `save`: execute the **unified save flow** below
3. If argument is `sync`: delegate to `/amnesia sync`
4. If argument is `entity`: delegate to `/amnesia entity`
5. Otherwise: treat argument as entity name, run `python3 $AMNESIA_PY entity load <name> --project-root $PROJECT_ROOT`

### Unified Save Flow

Detect context from the conversation and save **both entity memory and session log**:

1. **Detect context:** identify the entity name from the conversation (client name, project name, or use the root project directory name as fallback)
2. **Extract facts** from the conversation: new permanent facts, decisions, status changes, technical notes
3. **Entity diff:** run `python3 $AMNESIA_PY entity diff <name> '<updates_json>' --project-root $PROJECT_ROOT`
4. **Present diff** to user (added, updated, skipped) — wait for confirmation
5. **Entity save:** run `python3 $AMNESIA_PY entity save <name> '<updates_json>' --project-root $PROJECT_ROOT`
6. **Session save:** collect session summary (summary, changes, commits, decisions, next steps), then run `python3 $AMNESIA_PY project save <name> '<entry_json>' --project-root $PROJECT_ROOT`
7. Confirm both files written

### Language

Detect language via `scripts/lang.py`. Present output in the detected language. All stored data (JSON values, session logs) MUST be in English regardless of display language.
