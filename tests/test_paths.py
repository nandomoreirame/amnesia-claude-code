from scripts.paths import get_project_root, get_memory_dir, get_sessions_dir

def test_get_memory_dir_creates(tmp_path):
    d = get_memory_dir(tmp_path)
    assert d.exists()
    assert d == tmp_path / ".claude" / "amnesia" / "memory"

def test_get_sessions_dir_creates(tmp_path):
    d = get_sessions_dir(tmp_path)
    assert d.exists()

def test_project_root_override(tmp_path):
    root = get_project_root(override=str(tmp_path))
    assert root == tmp_path.resolve()
