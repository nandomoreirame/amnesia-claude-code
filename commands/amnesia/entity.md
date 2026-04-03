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

### Native Memory Context (on load)

When loading an entity, the JSON response includes a `native_memory_context` array with relevant native memories. Present these as additional context alongside the entity data:

> **Native Memory Context:** {count} related memories found in Claude Code's native memory.

List each native memory with its name, type, and a brief summary.

### Save: `/amnesia entity <name> save`

Two-step flow (REQ-009):

1. Extract facts from current conversation context
2. Run: `python3 $AMNESIA_PY entity diff <name> '<updates_json>' --project-root $PROJECT_ROOT`
3. Present diff to user (added, updated, skipped items)
4. Wait for explicit confirmation
5. Run: `python3 $AMNESIA_PY entity save <name> '<updates_json>' --project-root $PROJECT_ROOT`

### Native Memory Sync (after save)

After a successful `entity save`, synchronize to Claude Code's native memory system:

1. Run: `python3 $AMNESIA_PY sync --project-root $PROJECT_ROOT`
2. Parse the `entities.<name>.memories` array from the JSON response
3. For each memory entry, write a native memory file to `~/.claude/projects/<slug>/memory/` using the Write tool:
   - File name: `<entry.file_name>.md`
   - Content: YAML frontmatter with `name`, `description`, `type` fields, followed by the content body
   - Prefix convention: `amnesia-<entity>-` to avoid collision with user memories
4. Update `MEMORY.md` index with a pointer to each written file
5. If the sync response includes `index_warning: true`, warn the user: "Native MEMORY.md index has {index_line_count} lines (limit: 200). Skipping new entries to avoid truncation."

**Type mapping (REQ-021):**
- `current_status` → `project` type
- `decisions` → `feedback` type (one file per decision)
- `permanent_facts.metadata` → `reference` type
- `permanent_facts.items` and `technical_notes` are NOT synced (REQ-024)

### Language

All stored values in JSON MUST be written in English. User-facing output follows detected language from settings.json.
