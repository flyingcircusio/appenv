# SPDX-FileCopyrightText: 2020 Flying Circus
"""Integration tests using subprocess for real appenv execution.

These tests exercise the full __main__ flow and venv creation.
"""

import subprocess
import sys

import pytest

from tests.e2e.conftest import _base_env


@pytest.mark.slow(reason="Creates real venv with uv, takes ~10 seconds")
def test_subprocess_main_flow(tmp_path, setup_project_with_lockfile):
    """Integration test: Run appenv via subprocess to cover __main__ and venv creation.

    This exercises:
    - Line 1444: if __name__ == "__main__": main()
    - Branch 1148->1154: _prepare_venv when venv doesn't exist
    - Branch 1177->1180: _prepare_venv when 'current' already exists
    """
    base = setup_project_with_lockfile(tmp_path, "mycmd")

    # First call: creates venv from scratch
    result1 = subprocess.run(
        [sys.executable, str(base / "mycmd"), "--help"],
        capture_output=True,
        text=True,
        cwd=str(base),
        timeout=60,
        env=_base_env(),
    )

    # mycmd --help should succeed
    assert result1.returncode == 0
    assert "My CLI" in result1.stdout

    # Verify venv was created
    venv_dir = base / ".appenv" / "venv"
    assert venv_dir.exists()
    current_link = base / ".appenv" / "current"
    assert current_link.exists()
    assert current_link.is_symlink()

    # Second call: reuses existing venv (covers branch when current exists)
    result2 = subprocess.run(
        [sys.executable, str(base / "mycmd"), "--version"],
        capture_output=True,
        text=True,
        cwd=str(base),
        timeout=30,
        env=_base_env(),
    )

    # Should still work
    assert result2.returncode == 0
