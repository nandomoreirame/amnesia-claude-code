---
name: amnesia sync
description: "Synchronize all Amnesia entities to Claude Code native memory — /amnesia sync"
---

## Sync: `/amnesia sync`

Full synchronization between Amnesia entities and Claude Code's native MEMORY.md.

### Steps

1. Run: `python3 $AMNESIA_PY sync --project-root $PROJECT_ROOT`
2. Parse JSON response containing `entities`, `orphan_native_files`, `index_warning`, `index_line_count`
3. If `index_warning` is true:
   - Warn user: "Native MEMORY.md index has {index_line_count} lines (limit: 200). New entries will be skipped."
   - Only UPDATE existing native memory files. Do NOT create new ones.
4. For each entity in `entities`:
   - For each memory in `entities.<name>.memories`:
     - Write `<memory.file_name>.md` to the native memory directory with YAML frontmatter (`name`, `description`, `type`) and content
     - Add/update entry in MEMORY.md index: `- [<name>](<file_name>.md) — <description>`
   - Report: "Entity <name>: {count} memories synced"
5. If `orphan_native_files` is not empty:
   - List orphan files: "Native memories without Amnesia entity: {files}"
   - Do NOT delete orphans
6. Present summary: entities synced, memories created/updated, orphans found

### Read context before save (REQ-022)

When `/amnesia save` is invoked, BEFORE saving:
1. Run: `python3 $AMNESIA_PY sync --project-root $PROJECT_ROOT`
2. If any relevant native memories exist for the entity being saved, present them as additional context
3. Proceed with the normal save flow

### Language

All output follows detected language from settings.json.
