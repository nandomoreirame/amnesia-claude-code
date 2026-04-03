import subprocess, sys

def test_amnesia_py_runs():
    result = subprocess.run(
        [sys.executable, "scripts/amnesia.py", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "amnesia" in result.stdout.lower()
