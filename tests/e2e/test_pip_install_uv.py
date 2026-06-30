# SPDX-FileCopyrightText: 2020 Flying Circus
"""Integration test for pip-based uv installation.

Exercises UvBin._try_uv_from_pip end-to-end with a real subprocess: ensurepip
(or shutil.which pip fallback) installs uv into a temp directory, and the
resulting binary is verified for existence, executability, version output, and
UvBin.get_uv_version parseability.
"""

import subprocess

import pytest

import appenv
from appenv import UvBin


@pytest.mark.slow
def test_try_uv_from_pip_integration(tmp_path, monkeypatch):
    """Full integration test of UvBin._try_uv_from_pip with real subprocess.

    _try_uv_from_pip resolves the pip command (ensurepip first, then
    shutil.which fallback), installs uv into .appenv/.uv, and returns the
    binary path. This test verifies every step of that chain end-to-end.
    """
    appenv_dir = tmp_path / ".appenv"
    appenv_dir.mkdir()

    # Disable auto-mocking from conftest: we need real subprocess calls
    monkeypatch.undo()
    # Re-apply only ensure_uv mock to prevent UvBin.__init__ from running discovery
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: None)

    # Build UvBin without triggering discovery
    uv_bin = UvBin.__new__(UvBin)
    uv_bin.appenv_dir = appenv_dir
    uv_bin.uv_dir = appenv_dir / ".uv"
    uv_bin.managed_uv = uv_bin.uv_dir / "bin" / "uv"

    result = uv_bin._try_uv_from_pip()

    assert result is not None, "_try_uv_from_pip returned None — pip install failed"
    assert result.exists(), f"returned path does not exist: {result}"

    # Binary is executable
    assert result.stat().st_mode & 0o111, f"uv binary is not executable: {result}"

    # Binary runs and reports a valid version
    proc = subprocess.run(
        [str(result), "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    assert "uv" in proc.stdout.lower(), f"unexpected version output: {proc.stdout}"

    # UvBin.get_uv_version can parse it
    version = UvBin.get_uv_version(result)
    assert version.valid, f"installed uv has invalid version: {version}"
