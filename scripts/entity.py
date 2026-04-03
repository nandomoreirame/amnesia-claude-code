"""Entity memory operations."""
import json
from pathlib import Path
from scripts.paths import get_memory_dir
from scripts.schema import is_legacy_schema, migrate_v1, SCHEMA_URL
from scripts.merge import merge_entity

def load_entity(name: str, project_root: Path) -> dict | None:
    file = get_memory_dir(project_root) / f"{name}.json"
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError(f"invalid_json:{file}")
    if is_legacy_schema(data):
        data = migrate_v1(data)
    return data

def diff_entity(name: str, updates: dict, project_root: Path) -> dict:
    existing = load_entity(name, project_root)
    is_new = existing is None
    if is_new:
        existing = {"entity": name, "$schema": SCHEMA_URL,
                    "permanent_facts": {"metadata": {}, "items": []},
                    "decisions": [], "current_status": {}, "last_session": {}, "technical_notes": []}
    preview, diff = merge_entity(existing, updates)
    return {"is_new": is_new, "entity": name, "diff": diff, "preview": preview}

def save_entity(name: str, updates: dict, project_root: Path) -> dict:
    existing = load_entity(name, project_root)
    is_new = existing is None
    if is_new:
        existing = {"$schema": SCHEMA_URL, "entity": name,
                    "permanent_facts": {"metadata": {}, "items": []},
                    "decisions": [], "current_status": {}, "last_session": {}, "technical_notes": []}
    merged, diff = merge_entity(existing, updates)
    merged["$schema"] = SCHEMA_URL
    merged["entity"] = name
    file = get_memory_dir(project_root) / f"{name}.json"
    file.write_text(json.dumps(merged, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return {"entity": name, "is_new": is_new, "file": str(file), "diff": diff}

def list_entities(project_root: Path) -> list[dict]:
    results = []
    for file in sorted(get_memory_dir(project_root).glob("*.json")):
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
            if is_legacy_schema(data):
                data = migrate_v1(data)
            results.append({
                "entity": data.get("entity", file.stem),
                "updated_at": data.get("updated_at", ""),
                "phase": data.get("current_status", {}).get("phase", ""),
                "tracker_ids": data.get("current_status", {}).get("tracker_ids", []),
            })
        except Exception:
            results.append({"entity": file.stem, "error": "invalid_json"})
    return results
