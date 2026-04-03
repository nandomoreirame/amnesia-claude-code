"""Deterministic merge and deduplication for entity memory."""
from __future__ import annotations
from datetime import datetime, timezone

def _norm(text: str) -> str:
    return text.strip().lower()

def merge_list(existing: list[str], new_items: list[str]) -> tuple[list[str], list[str], list[str]]:
    seen = {_norm(i) for i in existing}
    merged, added, skipped = list(existing), [], []
    for item in new_items:
        if _norm(item) not in seen:
            merged.append(item); added.append(item); seen.add(_norm(item))
        else:
            skipped.append(item)
    return merged, added, skipped

def merge_decisions(existing: list[dict], new_decisions: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    def key(d): return f"{d.get('date','')}|{d.get('author','')}|{d.get('decision','')[:50]}"
    seen = {key(d) for d in existing}
    merged, added, skipped = list(existing), [], []
    for d in new_decisions:
        if key(d) not in seen:
            merged.append(d); added.append(d); seen.add(key(d))
        else:
            skipped.append(d)
    return merged, added, skipped

def merge_entity(existing: dict, updates: dict) -> tuple[dict, dict]:
    result = {**existing}
    diff = {
        "permanent_facts.items": {"added": [], "skipped": []},
        "permanent_facts.metadata": {"added": [], "updated": []},
        "decisions": {"added": [], "skipped": []},
        "technical_notes": {"added": [], "skipped": []},
        "current_status": {"updated": False},
        "last_session": {"updated": False},
    }
    items, added, skipped = merge_list(
        existing.get("permanent_facts", {}).get("items", []),
        updates.get("permanent_facts", {}).get("items", []))
    result.setdefault("permanent_facts", {})["items"] = items
    diff["permanent_facts.items"].update({"added": added, "skipped": skipped})

    em = existing.get("permanent_facts", {}).get("metadata", {})
    nm = updates.get("permanent_facts", {}).get("metadata", {})
    mm = {**em}
    for k, v in nm.items():
        (diff["permanent_facts.metadata"]["added"] if k not in em else diff["permanent_facts.metadata"]["updated"]).append(k)
        mm[k] = v
    result["permanent_facts"]["metadata"] = mm

    dec, added_d, skip_d = merge_decisions(existing.get("decisions", []), updates.get("decisions", []))
    result["decisions"] = dec; diff["decisions"].update({"added": added_d, "skipped": skip_d})

    notes, added_n, skip_n = merge_list(existing.get("technical_notes", []), updates.get("technical_notes", []))
    result["technical_notes"] = notes; diff["technical_notes"].update({"added": added_n, "skipped": skip_n})

    if "current_status" in updates:
        result["current_status"] = updates["current_status"]; diff["current_status"]["updated"] = True
    if "last_session" in updates:
        result["last_session"] = updates["last_session"]; diff["last_session"]["updated"] = True

    result["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return result, diff
