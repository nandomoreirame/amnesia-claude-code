"""Pydantic v2 schema for amnesia-entity memory files."""
from __future__ import annotations
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class PermanentFacts(BaseModel):
    metadata: dict[str, str] = Field(default_factory=dict)
    items: list[str] = Field(default_factory=list)

class Decision(BaseModel):
    date: str
    author: str
    decision: str

class CurrentStatus(BaseModel):
    phase: str = ""
    tracker_ids: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)

class LastSession(BaseModel):
    date: str = ""
    summary: str = ""

class EntityMemory(BaseModel):
    schema_: str = Field(alias="$schema", default="amnesia-entity")
    entity: str
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    permanent_facts: PermanentFacts = Field(default_factory=PermanentFacts)
    decisions: list[Decision] = Field(default_factory=list)
    current_status: CurrentStatus = Field(default_factory=CurrentStatus)
    last_session: LastSession = Field(default_factory=LastSession)
    technical_notes: list[str] = Field(default_factory=list)
    model_config = {"populate_by_name": True}

def is_legacy_schema(data: dict) -> bool:
    return data.get("$schema") == "etl-client-memory-v1"

def migrate_v1(data: dict) -> dict:
    pf = data.get("permanent_facts", {})
    old_status = data.get("current_status", {})
    metadata = {k: str(v) for k, v in pf.items() if k != "items" and isinstance(v, (str, int, float))}
    return {
        "$schema": "amnesia-entity",
        "entity": data.get("client", data.get("entity", "")),
        "updated_at": data.get("updated_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        "permanent_facts": {"metadata": metadata, "items": pf.get("items", [])},
        "decisions": data.get("decisions", []),
        "current_status": {
            "phase": old_status.get("phase", ""),
            "tracker_ids": old_status.get("jira_tickets", old_status.get("tracker_ids", [])),
            "blockers": old_status.get("blockers", []),
        },
        "last_session": data.get("last_session", {"date": "", "summary": ""}),
        "technical_notes": data.get("technical_notes", []),
    }
