"""Native MEMORY.md integration — read-only operations for Claude Code's native memory system."""
import re
from pathlib import Path

INDEX_LINE_LIMIT = 180


def project_root_to_slug(project_root: str) -> str:
    """Convert project root path to Claude Code slug (replace / with -, strip leading -)."""
    clean = project_root.rstrip("/")
    return clean.replace("/", "-").lstrip("-")


def resolve_native_memory_dir(project_root: str) -> Path:
    """Resolve the native memory directory path for a given project root."""
    slug = project_root_to_slug(project_root)
    return Path.home() / ".claude" / "projects" / f"-{slug}" / "memory"


def _parse_frontmatter(text: str) -> tuple[dict, str] | None:
    """Parse YAML frontmatter from markdown text. Returns (metadata, content) or None."""
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not match:
        return None
    yaml_str, content = match.group(1), match.group(2).strip()
    try:
        metadata = {}
        for line in yaml_str.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                if key and value:
                    metadata[key] = value
        if not metadata.get("name") or not metadata.get("type"):
            return None
        return metadata, content
    except Exception:
        return None


def read_native_memories(memory_dir: Path) -> list[dict]:
    """Read all native memory .md files (excluding MEMORY.md index) from the directory."""
    if not memory_dir.exists():
        return []
    results = []
    for f in sorted(memory_dir.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        try:
            parsed = _parse_frontmatter(f.read_text(encoding="utf-8"))
            if parsed is None:
                continue
            metadata, content = parsed
            results.append({
                "file": f.name,
                "name": metadata.get("name", ""),
                "description": metadata.get("description", ""),
                "type": metadata.get("type", ""),
                "content": content,
            })
        except Exception:
            continue
    return results


def read_memory_md_index(memory_dir: Path) -> list[str]:
    """Read the MEMORY.md index file and return its non-empty lines."""
    index_file = memory_dir / "MEMORY.md"
    if not index_file.exists():
        return []
    try:
        text = index_file.read_text(encoding="utf-8").strip()
        if not text:
            return []
        return [line for line in text.split("\n") if line.strip()]
    except Exception:
        return []


def filter_memories_by_entity(memories: list[dict], entity_name: str) -> list[dict]:
    """Filter native memories relevant to a given entity name."""
    name_lower = entity_name.lower()
    results = []
    for m in memories:
        searchable = f"{m.get('name', '')} {m.get('description', '')} {m.get('content', '')}".lower()
        if name_lower in searchable:
            results.append(m)
    return results


def get_native_context_for_entity(entity_name: str, memory_dir: Path) -> list[dict]:
    """Read native memories and return those relevant to the given entity."""
    memories = read_native_memories(memory_dir)
    return filter_memories_by_entity(memories, entity_name)


def check_index_limit(memory_dir: Path) -> tuple[bool, int]:
    """Check if MEMORY.md index is under the line limit. Returns (is_ok, line_count)."""
    lines = read_memory_md_index(memory_dir)
    count = len(lines)
    return count <= INDEX_LINE_LIMIT, count


def map_entity_to_native_memories(entity: dict) -> list[dict]:
    """Map entity sections to native memory file content. REQ-021 + REQ-024."""
    name = entity.get("entity", "unknown")
    prefix = f"amnesia-{name}"
    result = []

    # current_status → project type
    status = entity.get("current_status", {})
    phase = status.get("phase", "")
    trackers = status.get("tracker_ids", [])
    blockers = status.get("blockers", [])
    status_lines = [f"Phase: {phase}"]
    if trackers:
        status_lines.append(f"Tracker IDs: {', '.join(trackers)}")
    if blockers:
        status_lines.append(f"Blockers: {', '.join(blockers)}")
    result.append({
        "file_name": f"{prefix}-status",
        "name": f"{prefix}-status",
        "description": f"Current status of {name} entity from Amnesia",
        "type": "project",
        "content": "\n".join(status_lines),
    })

    # decisions → feedback type (one per decision)
    for i, dec in enumerate(entity.get("decisions", [])):
        decision_text = dec.get("decision", "")
        date = dec.get("date", "")
        author = dec.get("author", "")
        result.append({
            "file_name": f"{prefix}-decision-{i}",
            "name": f"{prefix}-decision-{i}",
            "description": f"Decision by {author} on {date} for {name}",
            "type": "feedback",
            "content": f"Decision: {decision_text}\nDate: {date}\nAuthor: {author}",
        })

    # permanent_facts.metadata → reference type (skip if empty)
    metadata = entity.get("permanent_facts", {}).get("metadata", {})
    if metadata:
        meta_lines = [f"- {k}: {v}" for k, v in metadata.items()]
        result.append({
            "file_name": f"{prefix}-metadata",
            "name": f"{prefix}-metadata",
            "description": f"Metadata reference for {name} entity from Amnesia",
            "type": "reference",
            "content": "\n".join(meta_lines),
        })

    # REQ-024: permanent_facts.items and technical_notes are NOT mapped
    return result


def generate_sync_report(project_root: Path, native_memory_dir: Path) -> dict:
    """Generate a sync report: maps all entities to native memory content and identifies orphans."""
    from scripts.entity import list_entities, load_entity

    amnesia_entities = list_entities(project_root)
    entity_names = set()
    entities_report = {}

    for ent_info in amnesia_entities:
        name = ent_info.get("entity", "")
        if not name or "error" in ent_info:
            continue
        entity_names.add(name)
        entity_data = load_entity(name, project_root)
        if entity_data is None:
            continue
        memories = map_entity_to_native_memories(entity_data)
        entities_report[name] = {"memories": memories}

    # Identify orphan native memory files
    existing_native = read_native_memories(native_memory_dir)
    amnesia_prefixes = {f"amnesia-{n}-" for n in entity_names}
    orphans = []
    for mem in existing_native:
        is_amnesia_owned = any(mem["file"].startswith(prefix) for prefix in amnesia_prefixes)
        if not is_amnesia_owned:
            orphans.append(mem["file"])

    # Check index limit
    index_ok, index_count = check_index_limit(native_memory_dir)

    return {
        "entities": entities_report,
        "orphan_native_files": orphans,
        "index_warning": not index_ok,
        "index_line_count": index_count,
    }
