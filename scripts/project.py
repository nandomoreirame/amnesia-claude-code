"""Project session memory operations."""
from __future__ import annotations
import re, subprocess
from datetime import datetime, timedelta
from pathlib import Path
from scripts.paths import get_sessions_dir, get_projects_dir

def save_project(name: str, entry: dict, project_root: Path) -> dict:
    sessions_dir = get_sessions_dir(project_root)
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%H:%M")
    sf = sessions_dir / f"{today}.md"
    lines = [f"## project:{name} ({now})", f"### Summary\n{entry.get('summary', '')}"]
    for key, label in [("changes", "Changes"), ("commits", "Commits"), ("decisions", "Decisions"), ("next", "Next")]:
        if entry.get(key):
            lines.append(f"### {label}")
            prefix = "- [ ] " if key == "next" else "- "
            lines.extend(f"{prefix}{i}" for i in entry[key])
    text = "\n".join(lines)
    if sf.exists():
        sf.write_text(sf.read_text(encoding="utf-8") + f"\n---\n\n{text}\n", encoding="utf-8")
    else:
        sf.write_text(f"# Session Log - {today}\n\n---\n\n{text}\n", encoding="utf-8")
    return {"project": name, "file": str(sf), "time": now, "error": None}

def _git_log(project_dir: Path, days: int = 7) -> list[str]:
    try:
        r = subprocess.run(["git", "-C", str(project_dir), "log", "--oneline", f"--since={days} days ago"],
                           capture_output=True, text=True, check=True)
        return [l for l in r.stdout.strip().splitlines() if l]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return []

def _extract_sections(content: str, name: str) -> list[dict]:
    pattern = re.compile(
        rf"^## project:{re.escape(name)}\s*\((\d{{2}}:\d{{2}})\)(.*?)(?=^---|\Z)",
        re.M | re.S)
    return [{"header": f"project:{name} ({m.group(1)})", "time": m.group(1), "content": m.group(2).strip()}
            for m in pattern.finditer(content)]

def load_project(name: str, project_root: Path, days: int = 7) -> dict:
    project_dir = get_projects_dir(project_root) / name
    if not project_dir.exists():
        return {"project": name, "error": "project_not_found", "sessions": [], "git_log": []}
    sessions_dir = get_sessions_dir(project_root)
    sessions = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        f = sessions_dir / f"{date}.md"
        if f.exists():
            for s in _extract_sections(f.read_text(encoding="utf-8"), name):
                sessions.append({**s, "date": date})
    return {"project": name, "project_dir": str(project_dir),
            "sessions": sessions, "git_log": _git_log(project_dir, days), "error": None}
