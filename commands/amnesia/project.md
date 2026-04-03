---
name: amnesia project
description: "Project session operations — /amnesia project <name>"
---

## Project Session Operations

### Load: `/amnesia project <name>`

1. Run: `python3 $AMNESIA_PY project load <name> --project-root $PROJECT_ROOT`
2. Parse JSON response
3. If error `project_not_found`: inform user
4. If found: present sessions, git log summary

### Save: `/amnesia project <name> save`

1. Collect session data: summary, changes, commits, decisions, next steps
2. Run: `python3 $AMNESIA_PY project save <name> '<entry_json>' --project-root $PROJECT_ROOT`
3. Confirm file written

### Language

All session log content MUST be written in English. User-facing output follows detected language from settings.json.
