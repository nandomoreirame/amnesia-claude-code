---
name: amnesia entity
description: "Entity memory operations — /amnesia entity <name>"
---

## Entity Memory Operations

### Load: `/amnesia entity <name>`

1. Run: `python3 $AMNESIA_PY entity load <name> --project-root $PROJECT_ROOT`
2. Parse JSON response
3. If `found` is false: inform user, offer to create
4. If found: present entity summary (facts, status, decisions, notes)

### Save: `/amnesia entity <name> save`

Two-step flow (REQ-009):

1. Extract facts from current conversation context
2. Run: `python3 $AMNESIA_PY entity diff <name> '<updates_json>' --project-root $PROJECT_ROOT`
3. Present diff to user (added, updated, skipped items)
4. Wait for explicit confirmation
5. Run: `python3 $AMNESIA_PY entity save <name> '<updates_json>' --project-root $PROJECT_ROOT`

### Language

All stored values in JSON MUST be written in English. User-facing output follows detected language from settings.json.
