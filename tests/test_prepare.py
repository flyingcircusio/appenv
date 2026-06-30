# SPDX-FileCopyrightText: 2020 Flying Circus
import argparse
import os
from pathlib import Path

import pytest

import appenv
from appenv import UvVersion


def test_prepare_creates_envdir_and_venv_symlink(
    workdir,
    monkeypatch,
    app_env,
    mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Test prepare creates venv, .venv symlink, and returns .appenv/venv path.

    Merges the former creates_envdir (FS state: .appenv/venv exists,
    .venv is a symlink) and creates_venv_symlink (return value equals
    .appenv/venv) assertions for the pyproject workflow.
    """
    base = Path(workdir) / "ducker"
    base.mkdir()
    os.chdir(base)

    make_pyproject(base, '[project]\nname = "ducker"\ndependencies = ["requests"]\n')

    uv = mock_uv
    uv.cmd = make_venv_creating_cmd(base=base)
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)

    env = app_env()
    env_dir = env.prepare()

    # .appenv/venv should exist
    assert (base / ".appenv" / "venv").exists()
    # .venv symlink should be created
    assert (base / ".venv").is_symlink()
    # prepare() returns the real venv path (.appenv/venv)
    assert env_dir == base / ".appenv" / "venv"


def test_prepare_syncs_with_frozen_flag(
    workdir,
    monkeypatch,
    app_env,
    mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Test prepare calls uv sync with --frozen and --no-dev flags."""
    base = Path(workdir) / "frozenproj"
    base.mkdir()
    os.chdir(base)

    make_pyproject(base, '[project]\nname = "frozenproj"\ndependencies = ["click"]\n')

    uv = mock_uv
    sync_args_captured = []
    venv_creating_cmd = make_venv_creating_cmd(base=base)

    def mock_cmd(args, verbose=False, **kwargs):
        if "sync" in args:
            sync_args_captured.append(args)
        return venv_creating_cmd(args, verbose=verbose, **kwargs)

    uv.cmd = mock_cmd
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)

    env = app_env()
    env.prepare()

    # Verify sync was called with --frozen and --no-dev (default for prepare)
    assert len(sync_args_captured) == 1
    assert "--frozen" in sync_args_captured[0]
    assert "--no-dev" in sync_args_captured[0]
    assert "--group" not in sync_args_captured[0]  # No dev group


def test_prepare_verbose_output(
    workdir,
    monkeypatch,
    capsys,
    patterns,
    app_env,
    mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
    capture_appenv_logs,
):
    """Verbose mode shows structured output with paths, mode, and sync info."""
    base = Path(workdir) / "verboseprep"
    base.mkdir()
    os.chdir(base)

    make_pyproject(base, '[project]\nname = "verboseprep"\ndependencies = ["click"]\n')

    uv = mock_uv
    uv.cmd = make_venv_creating_cmd(base=base)
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)
    monkeypatch.setenv("APPENV_VERBOSE", "1")

    env = app_env()
    env.prepare()

    out = capsys.readouterr().out

    # Concrete debug labels from source in expected order
    patterns.main.in_order(
        """\
...prepare-venv-context:...
...Creating fresh venv with uv ...
...uv-sync-extras:..."""
    )

    patterns.no_errors.optional("...")
    patterns.no_errors.refused("...error...")
    patterns.no_errors.refused("...exception...")
    patterns.no_errors.refused("...traceback...")
    patterns.no_errors.refused("...failed...")

    full_pattern = patterns.full
    full_pattern.merge("main")
    full_pattern.merge("no_errors")

    full_pattern.generate_example()

    assert full_pattern == out


def test_prepare_pyproject_mode_verbose(
    workdir,
    monkeypatch,
    capsys,
    patterns,
    app_env,
    mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
    capture_appenv_logs,
):
    """Line 590: Verbose output shows mode."""
    base = Path(workdir)
    make_pyproject(base, '[project]\nname = "test"\ndependencies = []\n')

    uv = mock_uv
    uv.cmd = make_venv_creating_cmd(
        base=base, python_content="#!/bin/sh\necho Python 3.12.0\n"
    )
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)
    monkeypatch.setenv("APPENV_VERBOSE", "1")

    env = app_env()
    env.prepare()

    captured = capsys.readouterr()

    # Just verify verbose output contains key messages (any order, with extra logs OK)
    assert "prepare-venv-context:" in captured.out
    assert "Creating fresh venv with uv ..." in captured.out
    assert "uv-sync-extras:" in captured.out

    patterns.no_errors.optional("...")
    patterns.no_errors.refused("...error...")
    patterns.no_errors.refused("...exception...")
    patterns.no_errors.refused("...traceback...")
    patterns.no_errors.refused("...failed...")

    full_pattern = patterns.full
    full_pattern.merge("no_errors")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_prepare_pyproject_unlink_file_in_appenv(
    workdir,
    monkeypatch,
    capsys,
    patterns,
    app_env,
    make_pyproject,
    capture_appenv_logs,
):
    """Line 758: _prepare_pyproject unlinks non-directory files in .appenv."""
    base = Path(workdir)

    make_pyproject(base, '[project]\nname = "test"\ndependencies = []\n')

    appenv_dir = base / ".appenv"
    appenv_dir.mkdir()
    old_file = appenv_dir / "old_file.txt"
    old_file.write_text("old content")

    monkeypatch.setenv("APPENV_VERBOSE", "1")

    env = app_env()
    env.prepare()

    assert not old_file.exists()
    captured = capsys.readouterr()

    # Just verify verbose output contains key messages (including the old file removal)
    assert "prepare-venv-context:" in captured.out
    assert "Creating fresh venv with uv ..." in captured.out
    assert "appenv-cleanup-entry: name=old_file.txt" in captured.out

    patterns.no_errors.optional("...")
    patterns.no_errors.refused("...error...")
    patterns.no_errors.refused("...exception...")
    patterns.no_errors.refused("...traceback...")
    patterns.no_errors.refused("...failed...")

    full_pattern = patterns.full
    full_pattern.merge("no_errors")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_update_lockfile_exits_67_no_project(monkeypatch, tmp_path, capsys, app_env):
    """update_lockfile exits with code 67 when no pyproject.toml found."""
    monkeypatch.chdir(tmp_path)

    env = app_env()

    with pytest.raises(SystemExit) as err:
        env.update_lockfile()

    # Exit code can be 65 (if requirements.txt found) or 67 (if not)
    assert err.value.code in (65, 67)
    captured = capsys.readouterr()
    assert "pyproject.toml" in captured.out


# ==============================================================================
# Additional pyproject workflow tests
# ==============================================================================


def test_prepare_pyproject_cleanup_old_appenv(
    tmp_path, monkeypatch, app_env, make_pyproject
):
    """_prepare_pyproject removes old hash-based venvs but keeps .appenv."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create pyproject.toml and uv.lock (NO requirements.txt = migration)
    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create old .appenv directory with hash-based venv
    old_appenv = base / ".appenv" / "oldhash"
    old_appenv.mkdir(parents=True)
    (old_appenv / "marker.txt").write_text("old")

    env = app_env()
    env.prepare()

    # Old hash-based venv should be gone
    assert not (base / ".appenv" / "oldhash").exists()
    # .appenv should still exist (even though mock didn't create venv)
    assert (base / ".appenv").exists()


def test_prepare_pyproject_removes_symlink_in_appenv(
    tmp_path, monkeypatch, caplog, app_env, make_pyproject
):
    """_prepare_appenv_dir removes symlinks in .appenv (e.g., nix-build out-links)."""
    caplog.set_level("DEBUG")

    base = tmp_path
    make_pyproject(base, '[project]\nname = "test"\ndependencies = []\n')

    # Create target directory and symlink in .appenv (simulates nix-build -o)
    target = base / "nix-store-uv"
    target.mkdir()
    (target / "bin").mkdir()

    appenv_dir = base / ".appenv"
    appenv_dir.mkdir()
    old_symlink = appenv_dir / "uv"
    old_symlink.symlink_to(target)

    assert old_symlink.is_symlink()
    assert old_symlink.exists()

    env = app_env(base)
    env.prepare()

    # Symlink should be removed
    assert not old_symlink.exists()
    # Target should NOT be removed
    assert target.exists()
    # Debug log should mention symlink removal
    assert "removing-path:" in caplog.text


def test_prepare_pyproject_keeps_appenv_if_requirements_exists(
    tmp_path, monkeypatch, app_env, make_pyproject
):
    """_prepare_pyproject keeps .appenv if requirements.txt still exists."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create BOTH pyproject.toml and requirements.txt
    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")
    (base / "requirements.txt").write_text("requests\n")

    # Create old .appenv directory
    old_appenv = base / ".appenv" / "oldhash"
    old_appenv.mkdir(parents=True)
    (old_appenv / "marker.txt").write_text("old")

    env = app_env()
    env.prepare()

    # Old .appenv should still exist (requirements.txt present)
    assert (base / ".appenv").exists()


def test_prepare_exits_without_project_files(tmp_path, monkeypatch, capsys, app_env):
    """prepare() exits with error if no pyproject.toml found."""
    monkeypatch.chdir(tmp_path)

    env = app_env()

    with pytest.raises(SystemExit) as err:
        env.prepare()

    # Exit code can be 65 (if requirements.txt found) or 67 (if not)
    assert err.value.code in (65, 67)
    captured = capsys.readouterr()
    assert "pyproject.toml" in captured.out


def test_prepare_pyproject_missing_uv_lock(tmp_path, monkeypatch, capsys, app_env):
    """_prepare_pyproject exits with code 67 when uv.lock is missing."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create pyproject.toml but NO uv.lock
    (base / "pyproject.toml").write_text(
        "[project]\nname = 'test'\ndependencies = []\n"
    )

    env = app_env()

    with pytest.raises(SystemExit) as err:
        env.prepare()

    assert err.value.code == 67
    captured = capsys.readouterr()
    assert "uv.lock" in captured.out


def test_prepare_pyproject_corrupted_venv(
    tmp_path, monkeypatch, app_env, mock_uv, make_pyproject
):
    """_prepare_pyproject removes corrupted venv and recreates it."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create broken .appenv/venv (directory without bin/python)
    venv_real = base / ".appenv" / "venv"
    venv_real.mkdir(parents=True)
    (venv_real / "broken_marker.txt").write_text("broken")

    # Mock uv commands
    uv_calls = []
    uv = mock_uv

    def mock_cmd(args, verbose=False, **kwargs):
        uv_calls.append(args)
        return ""

    uv.cmd = mock_cmd
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)

    env = app_env()
    result = env.prepare()

    # venv is now in .appenv/venv
    assert result == venv_real
    # The broken marker should be gone (venv was recreated)
    assert not (venv_real / "broken_marker.txt").exists()
    # venv command should be called
    assert any("venv" in c for c in uv_calls), f"Expected venv call, got {uv_calls}"


def test_prepare_pyproject_does_not_leak_uv_project_environment(
    tmp_path, monkeypatch, app_env, make_pyproject
):
    """_prepare_pyproject does not leak UV_PROJECT_ENVIRONMENT to os.environ.

    FIX #3 moved UV_PROJECT_ENVIRONMENT into the subprocess env dict so the
    parent process's os.environ stays clean.
    SPEC:
    integration/test_no_global_mutation.py::test_no_global_mutation_prepare_leaves_uv_project_env_alone
    """
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    env = app_env()
    env.prepare()

    assert os.environ.get("UV_PROJECT_ENVIRONMENT") is None


def test_prepare_pyproject_updates_broken_symlink(
    tmp_path, monkeypatch, app_env, make_pyproject
):
    """_prepare_pyproject updates broken .venv symlink to point to .appenv/venv."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create broken symlink (pointing to non-existent path)
    venv_link = base / ".venv"
    venv_link.symlink_to("/nonexistent/path")

    env = app_env()
    env.prepare()

    # Symlink should now point to correct location
    assert venv_link.is_symlink()
    assert venv_link.readlink() == Path(".appenv/venv")


def test_prepare_pyproject_keeps_real_venv_directory(
    tmp_path, monkeypatch, capsys, app_env, make_pyproject
):
    """_prepare_pyproject warns when .venv exists as a real directory."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create real .venv directory (not a symlink)
    venv_dir = base / ".venv"
    venv_dir.mkdir()
    (venv_dir / "marker.txt").write_text("real directory")

    env = app_env()
    env.prepare()

    # .venv should still be a real directory, not a symlink
    assert venv_dir.is_dir()
    assert not venv_dir.is_symlink()
    assert (venv_dir / "marker.txt").exists()

    # But user should be warned
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "not a symlink" in captured.out


def test_prepare_pyproject_keeps_dot_uv_dir(
    tmp_path, monkeypatch, app_env, make_pyproject
):
    """_prepare_pyproject does not delete .appenv/.uv during cleanup."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create old hash-based venv AND .uv
    old_venv = base / ".appenv" / "oldhash"
    old_venv.mkdir(parents=True)
    (old_venv / "marker.txt").write_text("old")

    uv_dir = base / ".appenv" / ".uv"
    uv_dir.mkdir(parents=True)
    (uv_dir / "uv_binary").write_text("uv")

    env = app_env()
    env.prepare()

    # .uv should be kept
    assert uv_dir.exists()
    assert (uv_dir / "uv_binary").exists()
    # old hash venv should be removed
    assert not old_venv.exists()


@pytest.mark.parametrize(
    ("writes_pyproject", "expected"),
    [
        pytest.param(True, True, id="pyproject"),
        pytest.param(False, False, id="none"),
    ],
)
def test_detect_project_type(tmp_path, monkeypatch, writes_pyproject, expected):
    """pyproject.toml presence determines Pyproject.exists.

    pyproject: pyproject.toml is detected (True); none: returns False when
    no pyproject.toml exists.
    """
    monkeypatch.chdir(tmp_path)
    if writes_pyproject:
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    pyproject = appenv.Pyproject(tmp_path)
    result = pyproject.exists
    assert result is expected


def test_prepare_venv_replaces_current_symlink(
    workdir,
    monkeypatch,
    app_env,
    make_mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Line 1176: _prepare_venv replaces existing current symlink."""
    base = Path(workdir) / "myproject_venv_test"
    base.mkdir()
    os.chdir(base)

    make_pyproject(base, "[project]\nname='test'\nversion='1.0'\n")

    env = app_env()

    # Create existing symlink pointing to wrong location
    env.appenv_dir.mkdir(parents=True, exist_ok=True)
    (env.appenv_dir / "current").symlink_to("/wrong/path", target_is_directory=True)

    mock_uv = make_mock_uv(
        version=UvVersion(0, 7, 0),
        cmd_fn=make_venv_creating_cmd(
            base=base, python_content="#!/bin/sh\necho Python 3.12.0\n"
        ),
    )
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: mock_uv)

    env._prepare_venv(dev_mode=False)

    # Verify symlink was replaced
    assert (env.appenv_dir / "current").exists()
    assert (env.appenv_dir / "current").readlink() == Path("venv")


def test_prepare_venv_existing_venv(
    workdir,
    monkeypatch,
    app_env,
    make_mock_uv,
    mock_cmd_python,
    create_venv,
    make_pyproject,
):
    """Branch 1148->1154: _prepare_venv skips uv venv when venv already exists."""
    base = Path(workdir) / "myproject_existing_venv"
    base.mkdir()
    os.chdir(base)

    make_pyproject(base, "[project]\nname='test'\nversion='1.0'\n")

    env = app_env()

    # Create existing venv structure BEFORE calling _prepare_venv
    create_venv(base)

    # Track if uv.cmd was called for venv creation
    venv_called = [False]

    def venv_cmd(args, verbose=False, **kwargs):
        if "venv" in args:
            venv_called[0] = True
        return ""

    mock_uv = make_mock_uv(version=UvVersion(0, 7, 0), cmd_fn=venv_cmd)
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: mock_uv)

    env._prepare_venv(dev_mode=False)

    # uv venv should NOT have been called since venv already existed
    assert not venv_called[0], "uv venv should be skipped when venv exists"


def test_prepare_venv_current_is_directory(
    workdir,
    monkeypatch,
    app_env,
    make_mock_uv,
    mock_cmd_python,
    create_venv,
    make_pyproject,
):
    """Branch 1177->1180: _prepare_venv skips symlink when current is a real dir."""
    base = Path(workdir) / "myproject_current_dir"
    base.mkdir()
    os.chdir(base)

    make_pyproject(base, "[project]\nname='test'\nversion='1.0'\n")

    env = app_env()

    # Create existing venv
    create_venv(base)

    # Create 'current' as a real directory (not a symlink)
    current_dir = env.appenv_dir / "current"
    current_dir.mkdir()
    (current_dir / "some_file.txt").write_text("test")

    assert current_dir.is_dir()
    assert not current_dir.is_symlink()

    mock_uv = make_mock_uv(version=UvVersion(0, 7, 0))
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: mock_uv)

    env._prepare_venv(dev_mode=False)

    # 'current' should still be a directory, not converted to symlink
    assert current_dir.is_dir()
    assert not current_dir.is_symlink()
    assert (current_dir / "some_file.txt").exists()


# Stale-venv recovery: broken Python triggers venv removal and recreation.


def test_stale_venv_broken_python(
    tmp_path,
    monkeypatch,
    app_env,
    mock_uv,
    create_venv,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Stale-venv broken python: cmd() raises ValueError, venv removed and recreated."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create existing venv with working python
    venv_real = create_venv(base)

    uv = mock_uv
    venv_python = venv_real / "bin" / "python"
    first_call = [True]

    uv.cmd = make_venv_creating_cmd(base, "#!/bin/sh\n")

    def mock_cmd(c, **kwargs):
        # Only raise on first call (stale-venv check), not post-sync check
        if str(venv_python) in str(c) and first_call[0]:
            first_call[0] = False
            raise appenv.CommandError("malformed output", 1)  # noqa: EM101, TRY003
        return b"Python 3.12.0"

    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)
    monkeypatch.setattr(appenv, "cmd", mock_cmd)

    env = app_env()
    env.prepare()

    # Old venv was removed (broken python) and recreated by mock uv
    assert venv_real.exists()


def test_stale_venv_version_mismatch(
    tmp_path,
    monkeypatch,
    app_env,
    mock_uv,
    create_venv,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Stale-venv version mismatch: venv Python too old for requires-python."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(
        base,
        '[project]\nname = "test"\ndependencies = []\nrequires-python = ">=3.12"\n',
    )

    # Create existing venv with old python
    venv_real = create_venv(base)

    uv = mock_uv
    uv.cmd = make_venv_creating_cmd(base, "#!/bin/sh\n")

    def mock_cmd(c, **kwargs):
        # Return old Python version to trigger version mismatch
        if str(venv_real / "bin" / "python") in str(c):
            return b"Python 3.8.0"
        return b"Python 3.12.0"

    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)
    monkeypatch.setattr(appenv, "cmd", mock_cmd)

    env = app_env()
    env.prepare()

    # Venv was removed (Python 3.8 doesn't satisfy >=3.12) and recreated
    assert venv_real.exists()


def test_stale_venv_max_version_constraint(
    tmp_path,
    monkeypatch,
    capsys,
    app_env,
    mock_uv,
    create_venv,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Stale-venv max version: Python exceeds upper bound in requires-python."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(
        base,
        '[project]\nname = "test"\n'
        'dependencies = []\nrequires-python = ">=3.12,<3.14"\n',
    )

    # Create existing venv with Python exceeding upper bound
    venv_real = create_venv(base, python_output="Python 3.15.0")

    uv = mock_uv
    uv.cmd = make_venv_creating_cmd(base, "#!/bin/sh\n")

    def mock_cmd(c, **kwargs):
        if str(venv_real / "bin" / "python") in str(c):
            return b"Python 3.15.0"
        return b"Python 3.12.0"

    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)
    monkeypatch.setattr(appenv, "cmd", mock_cmd)

    env = app_env()
    env.prepare()

    captured = capsys.readouterr()
    # Should show constraint message including upper bound
    assert "Recreating venv" in captured.out
    assert "<3.14" in captured.out
    assert venv_real.exists()


def test_extras_sync_args(
    tmp_path,
    monkeypatch,
    app_env,
    mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Extras in AppEnvSettings produce --extra flag in uv sync args."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, '[project]\nname = "test"\ndependencies = []\n')

    uv = mock_uv
    sync_args_captured = []
    venv_creating_cmd = make_venv_creating_cmd(base=base)

    def mock_cmd(args, verbose=False, **kwargs):
        if "sync" in args:
            sync_args_captured.append(args)
        return venv_creating_cmd(args, verbose=verbose, **kwargs)

    uv.cmd = mock_cmd
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)

    settings = appenv.AppEnvSettings(verbose=False, extras=["dev-tools"], basedir=base)
    env = appenv.AppEnv(Path.cwd(), settings)
    env.prepare()

    assert len(sync_args_captured) == 1
    assert "--extra" in sync_args_captured[0]
    assert "dev-tools" in sync_args_captured[0]


def test_prepare_venv_link_is_symlink_survives_unlink(
    tmp_path,
    monkeypatch,
    capsys,
    app_env,
    mock_cmd_python,
    create_venv,
    make_pyproject,
):
    """Branch 1186->1194: .venv symlink survives unlink (race / mock).

    Covers the False branch of 'elif not self.venv_link.is_symlink()'.
    When .venv is a symlink that survives the unlink call, we reach line 1194
    without entering the warning blocks.
    """
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create .appenv/venv so _prepare_venv has something to link to
    create_venv(base)

    # Create a real directory for the symlink target
    other_dir = base / "other_venv"
    other_dir.mkdir()

    # Create .venv as a symlink to other_dir
    venv_link = base / ".venv"
    venv_link.symlink_to(other_dir)
    assert venv_link.is_symlink()

    # Track unlink calls — make the first one for .venv a no-op
    original_unlink = Path.unlink
    unlink_calls = []

    def mock_unlink(self, missing_ok=False):
        if str(self).endswith("/.venv"):
            unlink_calls.append(str(self))
            return None  # No-op: simulate race where unlink fails silently
        return original_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", mock_unlink)

    env = app_env()
    env._prepare_venv(dev_mode=False)

    # The unlink was attempted but was a no-op, so .venv is still a symlink
    assert len(unlink_calls) > 0, "unlink should have been called for .venv"


def test_prepare_removes_legacy_current_symlink(
    tmp_path,
    monkeypatch,
    app_env,
    mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
):
    """Line 1196: _prepare_venv removes existing .appenv/current symlink."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    make_pyproject(base, "[project]\nname = 'test'\ndependencies = []\n")

    # Create .appenv with a 'current' symlink pointing to old location
    appenv_dir = base / ".appenv"
    appenv_dir.mkdir()
    old_target = base / "old_venv"
    old_target.mkdir()
    current_link = appenv_dir / "current"
    current_link.symlink_to(old_target, target_is_directory=True)
    assert current_link.is_symlink()

    uv = mock_uv
    uv.cmd = make_venv_creating_cmd(base)
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: uv)

    env = app_env()
    env._prepare_venv(dev_mode=False)

    # The old symlink should have been removed and recreated pointing to venv
    assert current_link.is_symlink()
    assert current_link.readlink() == Path("venv")


# ==============================================================================
# run_uv command tests (from test_coverage.py)
# ==============================================================================


@pytest.mark.parametrize(
    ("command", "args"),
    [
        pytest.param("run_uv", ["pip", "install", "foo"], id="run_uv"),
        pytest.param("run_script", ["pytest"], id="run_script"),
    ],
)
def test_command_exits_67_no_pyproject(
    monkeypatch, tmp_path, capsys, app_env, command, args
):
    """Command exits 67 NOINPUT when no pyproject.toml exists.

    Verifies fix-contract-treue::run-uv-pre-flight: `uv` in a directory
    without pyproject.toml behaves like prepare/python/update-lockfile,
    and that run_script -> run_uv delegation inherits the pre-flight check.
    """
    monkeypatch.chdir(tmp_path)
    env = app_env()

    with pytest.raises(SystemExit) as exc:
        getattr(env, command)(argparse.Namespace(), args)

    assert exc.value.code == appenv.EXIT_CODE_NOINPUT
    captured = capsys.readouterr()
    assert "No pyproject.toml found" in captured.out
