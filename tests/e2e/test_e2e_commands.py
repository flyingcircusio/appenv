# SPDX-FileCopyrightText: 2020 Flying Circus
"""E2E tests for all appenv CLI commands using subprocess.

Tests exercise the full CLI as a real subprocess, verifying command
dispatch, exit codes, file system effects, and output.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pexpect
import pytest

from tests.e2e.conftest import _base_env


def _copy_appenv(tmp_path):
    """Copy appenv script to isolated directory, return path to the copy."""
    import appenv

    src = Path(appenv.__file__).resolve()
    dst = tmp_path / "appenv"
    shutil.copy(src, dst)
    dst.chmod(0o755)
    return dst


def _setup_project_with_lockfile(tmp_path, *, app_name="testapp"):
    """Create minimal project with pyproject.toml + uv.lock.

    Returns (base_dir, appenv_script_path).
    """
    base = tmp_path / "project"
    base.mkdir()
    appenv_script = _copy_appenv(base)

    (base / "pyproject.toml").write_text(
        "[project]\n"
        f'name = "{app_name}"\n'
        'version = "0.1.0"\n'
        "dependencies = []\n"
        'requires-python = ">=3.10"\n'
    )

    subprocess.run(
        ["uv", "lock"],
        cwd=str(base),
        capture_output=True,
        timeout=30,
        check=True,
        env=_base_env(),
    )

    return base, appenv_script


# ---------------------------------------------------------------------------
# 1. version
# ---------------------------------------------------------------------------


def test_e2e_version(tmp_path):
    """appenv version shows version string."""
    appenv_script = _copy_appenv(tmp_path)

    result = subprocess.run(
        [sys.executable, str(appenv_script), "version"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(tmp_path),
        env=_base_env(),
    )

    assert result.returncode == 0
    assert "appenv" in result.stdout
    assert any(c.isdigit() for c in result.stdout)


# ---------------------------------------------------------------------------
# 2-4. reset
# ---------------------------------------------------------------------------


def test_e2e_reset_no_venv(tmp_path):
    """appenv reset on empty project (no .appenv dir) exits 0."""
    appenv_script = _copy_appenv(tmp_path)

    result = subprocess.run(
        [sys.executable, str(appenv_script), "reset"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(tmp_path),
        env=_base_env(),
    )

    assert result.returncode == 0


@pytest.mark.slow(reason="Needs prepare which requires uv to create venv")
def test_e2e_reset_after_prepare(tmp_path):
    """Create project → prepare → reset removes both venv and .venv symlink.

    One prepare+reset cycle asserts both post-conditions (previously two tests
    each ran the full slow cycle): ``.appenv/venv`` is gone and the ``.venv``
    symlink is removed.
    """
    base, appenv_script = _setup_project_with_lockfile(tmp_path)

    # Prepare creates both .appenv/venv and the .venv symlink.
    prep = subprocess.run(
        [sys.executable, str(appenv_script), "prepare"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(base),
        env=_base_env(),
    )
    assert prep.returncode == 0, f"prepare failed: {prep.stderr}"
    assert (base / ".appenv" / "venv").exists()
    assert (base / ".venv").is_symlink()

    # Reset removes both the venv directory and the symlink.
    result = subprocess.run(
        [sys.executable, str(appenv_script), "reset"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(base),
        env=_base_env(),
    )

    assert result.returncode == 0
    assert not (base / ".appenv" / "venv").exists()
    assert not (base / ".venv").is_symlink()


# ---------------------------------------------------------------------------
# 5-6. update-lockfile
# ---------------------------------------------------------------------------


def test_e2e_update_lockfile(tmp_path):
    """Create project with pyproject.toml → update-lockfile → verify uv.lock."""
    base = tmp_path / "project"
    base.mkdir()
    appenv_script = _copy_appenv(base)

    (base / "pyproject.toml").write_text(
        '[project]\nname = "testlock"\nversion = "0.1.0"\n'
        'dependencies = []\nrequires-python = ">=3.10"\n'
    )

    result = subprocess.run(
        [sys.executable, str(appenv_script), "update-lockfile"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(base),
        env=_base_env(),
    )

    assert result.returncode == 0, f"update-lockfile failed: {result.stderr}"
    assert (base / "uv.lock").exists()


def test_e2e_update_lockfile_verbose(tmp_path):
    """APPENV_VERBOSE=1 shows user-facing operational output, not dev internals."""
    base = tmp_path / "project"
    base.mkdir()
    appenv_script = _copy_appenv(base)

    (base / "pyproject.toml").write_text(
        '[project]\nname = "testlock"\nversion = "0.1.0"\n'
        'dependencies = []\nrequires-python = ">=3.10"\n'
    )

    result = subprocess.run(
        [sys.executable, str(appenv_script), "update-lockfile"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(base),
        env=_base_env(APPENV_VERBOSE="1"),
    )

    assert result.returncode == 0, f"update-lockfile failed: {result.stderr}"
    assert (base / "uv.lock").exists()

    out = result.stdout

    # Verbose mode shows operational steps the user can act on: which uv command
    # is being run and the lockfile update.
    assert "uv-cmd-started:" in out
    assert "updating-lockfile:" in out

    # It must NOT leak developer internals onto the console (those stay in the
    # file log only).
    # - no funcName:lineno caller prefix
    assert "setup_logging:" not in out
    # - no logging-internal diagnostics
    assert "logging-configured:" not in out
    # - no raw Python object repr (argparse Namespace) with memory addresses
    assert "Namespace(" not in out
    assert not re.search(r"0x[0-9a-fA-F]+", out), out

    # The file log retains the full developer detail the console hides: internal
    # diagnostics AND the funcName:lineno prefix (file format unchanged).
    file_log = (base / ".appenv" / "logs" / "appenv.log").read_text()
    assert "logging-configured:" in file_log
    assert "parsed-args:" in file_log
    assert re.search(r"setup_logging:\d+ ", file_log)


# ---------------------------------------------------------------------------
# 7-8. self-update
# ---------------------------------------------------------------------------


def test_e2e_self_update_same_version(tmp_path):
    """self-update with same version is a no-op (exit 0, prints up-to-date)."""
    base = tmp_path / "project"
    base.mkdir()
    appenv_script = _copy_appenv(base)

    result = subprocess.run(
        [sys.executable, str(appenv_script), "self-update"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(base),
        env=_base_env(APPENV_BASEDIR=str(base)),
    )

    assert result.returncode == 0
    assert "up-to-date" in result.stdout


def test_e2e_self_update_no_script(tmp_path):
    """self-update in dir without appenv script exits with error."""
    base = tmp_path / "project"
    base.mkdir()
    appenv_script = _copy_appenv(base)

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    result = subprocess.run(
        [sys.executable, str(appenv_script), "self-update"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(empty_dir),
        env=_base_env(APPENV_BASEDIR=str(empty_dir)),
    )

    # target_script = empty_dir / "appenv" does not exist
    assert result.returncode == 67  # EXIT_CODE_NOINPUT
    assert "No appenv script found" in result.stdout


# ---------------------------------------------------------------------------
# 9-10. prepare error cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("writes_pyproject", "expected_message"),
    [
        pytest.param(
            False,
            "No pyproject.toml found",
            id="no-pyproject",
        ),
        pytest.param(
            True,
            "No uv.lock",
            id="no-lockfile",
        ),
    ],
)
def test_e2e_prepare_no_pyproject_or_lockfile(
    tmp_path, writes_pyproject, expected_message
):
    """appenv prepare exits 67 when pyproject.toml or uv.lock is missing."""
    appenv_script = _copy_appenv(tmp_path)

    if writes_pyproject:
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "testprep"\nversion = "0.1.0"\n'
            'dependencies = ["click"]\nrequires-python = ">=3.10"\n'
        )

    result = subprocess.run(
        [sys.executable, str(appenv_script), "prepare"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(tmp_path),
        env=_base_env(),
    )

    assert result.returncode == 67
    assert expected_message in result.stdout


# ---------------------------------------------------------------------------
# 11-13. python / run / uv commands (need venv)
# ---------------------------------------------------------------------------


@pytest.mark.slow(reason="Needs prepare which requires uv to create venv")
@pytest.mark.parametrize(
    ("argv_tail", "expected_substring"),
    [
        pytest.param(
            ["python", "-c", "print('hello from e2e')"],
            "hello from e2e",
            id="python",
        ),
        pytest.param(
            ["run", "python", "-c", "print('run works')"],
            "run works",
            id="run",
        ),
    ],
)
def test_e2e_python_or_run_command(tmp_path, argv_tail, expected_substring):
    """appenv python/run executes a command in the project venv."""
    base, appenv_script = _setup_project_with_lockfile(tmp_path)

    # Prepare venv first
    prep = subprocess.run(
        [sys.executable, str(appenv_script), "prepare"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(base),
        env=_base_env(),
    )
    assert prep.returncode == 0, f"prepare failed: {prep.stderr}"

    result = subprocess.run(
        [sys.executable, str(appenv_script), *argv_tail],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(base),
        env=_base_env(),
    )

    assert result.returncode == 0
    assert expected_substring in result.stdout


def test_e2e_uv_command(tmp_path):
    """appenv uv --version delegates to uv binary and shows version.

    fix-contract-treue::run-uv-pre-flight: `uv` now requires a pyproject.toml
    (exit 67 otherwise, matching prepare/python), so this runs inside a real
    project instead of an empty directory.
    """
    appenv_script = _copy_appenv(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "testapp"\nversion = "0.1.0"\n'
    )

    result = subprocess.run(
        [sys.executable, str(appenv_script), "uv", "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(tmp_path),
        env=_base_env(),
    )

    assert result.returncode == 0
    # uv --version output like "uv 0.5.x"
    assert any(c.isdigit() for c in result.stdout)


# ---------------------------------------------------------------------------
# 14. prepare creates .venv symlink
# ---------------------------------------------------------------------------


@pytest.mark.slow(reason="Needs prepare which requires uv to create venv")
def test_e2e_prepare_creates_dot_venv_symlink(tmp_path):
    """prepare creates .venv symlink pointing to .appenv/venv."""
    base, appenv_script = _setup_project_with_lockfile(tmp_path)

    result = subprocess.run(
        [sys.executable, str(appenv_script), "prepare"],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(base),
        env=_base_env(),
    )

    assert result.returncode == 0, f"prepare failed: {result.stderr}"
    assert (base / ".venv").is_symlink()
    # Symlink target resolves to .appenv/venv
    target = (base / ".venv").resolve()
    expected = (base / ".appenv" / "venv").resolve()
    assert target == expected


# ---------------------------------------------------------------------------
# 15-16. gitignore (ensure_gitignore)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(sys.platform == "win32", reason="pexpect not available on Windows")
def test_e2e_ensure_gitignore_created(tmp_path):
    """init creates .gitignore with .appenv/ and .venv/ entries."""
    base = tmp_path / "myproject"
    base.mkdir()
    appenv_script = _copy_appenv(base)

    child = pexpect.spawn(
        sys.executable,
        [str(appenv_script), "init"],
        cwd=str(base),
        timeout=30,
        env=_base_env(),
    )

    child.expect(r"Dependency:.*")
    child.sendline("click")

    child.expect(r"Dependency:.*")
    child.sendline("")  # finish dependencies

    child.expect(r"Binary to expose.*")
    child.sendline("mycli")

    child.expect(r"Project name.*")
    child.sendline("")  # accept default

    child.expect(r"Description.*")
    child.sendline("")

    child.expect(r"Minimum Python version.*")
    child.sendline("")

    child.expect(pexpect.EOF)
    child.close()

    assert child.exitstatus == 0

    gitignore = (base / ".gitignore").read_text()
    assert ".appenv" in gitignore
    assert ".venv" in gitignore


def test_e2e_ensure_gitignore_updated(tmp_path):
    """ensure_gitignore appends missing entries to existing .gitignore.

    Uses migrate (which calls ensure_gitignore) because prepare does not.
    Targets the newline-append and "Updated" print paths in ensure_gitignore.
    """
    base = tmp_path / "project"
    base.mkdir()
    appenv_script = _copy_appenv(base)

    # requirements.txt triggers migrate
    (base / "requirements.txt").write_text("click\n")

    # Pre-existing .gitignore with only .appenv
    (base / ".gitignore").write_text(".appenv\n")

    result = subprocess.run(
        [sys.executable, str(appenv_script), "migrate"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(base),
        env=_base_env(),
    )

    assert result.returncode == 0, f"migrate failed: {result.stderr}"

    gitignore = (base / ".gitignore").read_text()
    assert ".appenv" in gitignore
    assert ".venv" in gitignore
    assert "Updated" in result.stdout
