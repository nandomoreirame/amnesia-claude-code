"""Path resolution for amnesia plugin."""
import subprocess
from pathlib import Path

def get_project_root(override: str | None = None) -> Path:
    if override:
        return Path(override).resolve()
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
        return Path(r.stdout.strip())
    except subprocess.CalledProcessError:
        return Path.cwd()

def get_memory_dir(project_root: Path) -> Path:
    d = project_root / ".claude" / "amnesia" / "memory"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_sessions_dir(project_root: Path) -> Path:
    d = project_root / ".claude" / "amnesia" / "sessions"
    d.mkdir(parents=True, exist_ok=True)
    return d

def get_projects_dir(project_root: Path) -> Path:
    return project_root / "projects"
