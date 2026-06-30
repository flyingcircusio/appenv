# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for self-update command."""

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import appenv


def test_self_update_rewrites_script_on_version_mismatch(
    tmp_path, monkeypatch, capsys, test_settings, patterns
):
    """self-update rewrites ./appenv when its embedded version differs.

    Covers the APPENV_BASEDIR path too: that env var is inert here because
    branch B in ``self_update`` is already taken whenever ``self.base`` differs
    from the running package dir — which the tmp_path basedir always does — so
    the ``or`` short-circuits regardless of the variable.
    """
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create an "old" appenv script with a different version
    old_script = base / "appenv"
    old_script.write_text(
        '#!/usr/bin/env python3\n__version__ = "0.0.1"\nprint("old")\n'
    )
    old_script.chmod(0o755)

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))
    env.self_update()

    captured = capsys.readouterr()
    patterns.main.in_order(f"Updated .../appenv (0.0.1 -> {appenv.__version__})")
    patterns.no_errors.refused(
        """\
...error...
...traceback..."""
    )
    full = patterns.full
    full.merge("main", "no_errors")
    assert full == captured.out

    # The script should now contain the current version
    new_content = old_script.read_text()
    assert appenv.__version__ in new_content
    assert "0.0.1" not in new_content


def test_self_update_noop_on_same_version(tmp_path, monkeypatch, capsys, test_settings):
    """self-update does nothing when versions already match."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    current_script = base / "appenv"
    current_script.write_text(
        f"#!/usr/bin/env python3\n"
        f'__version__ = "{appenv.__version__}"\n'
        f'print("current")\n'
    )
    current_script.chmod(0o755)
    original_mtime = current_script.stat().st_mtime

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))
    env.self_update()

    captured = capsys.readouterr()
    assert "already up-to-date" in captured.out

    # File should be untouched
    assert current_script.stat().st_mtime == original_mtime


@pytest.mark.parametrize(
    ("script_content", "expected_exit_code"),
    [
        pytest.param(
            f'#!/usr/bin/env python3\n__version__ = "{appenv.__version__}"\n',
            0,
            id="no_drift",
        ),
        pytest.param(
            '#!/usr/bin/env python3\n__version__ = "0.0.1"\n',
            1,
            id="detects_drift",
        ),
    ],
)
def test_self_update_check(
    tmp_path, monkeypatch, capsys, test_settings, script_content, expected_exit_code
):
    """self-update --check exits 0 when versions match, 1 when they differ."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    script = base / "appenv"
    script.write_text(script_content)
    script.chmod(0o755)

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))

    args = argparse.Namespace(check=True)
    with pytest.raises(SystemExit) as exc_info:
        env.self_update(args)

    assert exc_info.value.code == expected_exit_code

    if expected_exit_code == 1:
        captured = capsys.readouterr()
        assert "Version drift detected" in captured.out
        assert "0.0.1" in captured.out
        assert appenv.__version__ in captured.out

        # File should NOT be modified
        assert script.read_text().startswith("#!/usr/bin/env python3")
        assert '__version__ = "0.0.1"' in script.read_text()


def test_self_update_no_script(tmp_path, monkeypatch, test_settings):
    """self-update exits with NOINPUT when no appenv script exists."""
    monkeypatch.chdir(tmp_path)

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))

    with pytest.raises(SystemExit) as exc_info:
        env.self_update()

    assert exc_info.value.code == 67  # EXIT_CODE_NOINPUT


def test_self_update_unknown_version(tmp_path, monkeypatch, capsys, test_settings):
    """self-update handles scripts without __version__."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    old_script = base / "appenv"
    old_script.write_text("#!/usr/bin/env python3\nprint('old')\n")
    old_script.chmod(0o755)

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))
    env.self_update()

    captured = capsys.readouterr()
    assert "Updated" in captured.out
    assert "unknown" in captured.out
    assert appenv.__version__ in captured.out

    # The script should now contain the current version
    new_content = old_script.read_text()
    assert appenv.__version__ in new_content


@pytest.mark.parametrize(
    "path_arg",
    [
        ".",  # relative: update script in cwd
        "subdir/target",  # creates subdirectory, absolute-style via tmp_path join
    ],
)
def test_self_update_with_explicit_path(
    tmp_path, monkeypatch, capsys, test_settings, path_arg
):
    """self-update <path> updates the appenv script in the specified directory."""
    monkeypatch.chdir(tmp_path)

    target_dir = tmp_path / path_arg
    target_dir.mkdir(parents=True, exist_ok=True)

    old_script = target_dir / "appenv"
    old_script.write_text(
        '#!/usr/bin/env python3\n__version__ = "0.0.1"\nprint("old")\n'
    )
    old_script.chmod(0o755)

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))

    args = argparse.Namespace(check=False, path=path_arg)
    env.self_update(args)

    captured = capsys.readouterr()
    assert "Updated" in captured.out
    assert "0.0.1" in captured.out
    assert appenv.__version__ in captured.out

    new_content = old_script.read_text()
    assert appenv.__version__ in new_content
    assert "0.0.1" not in new_content


def test_self_update_externally_managed_no_path_no_basedir(
    tmp_path, monkeypatch, capsys
):
    """self-update without path and without APPENV_BASEDIR exits with USAGE."""
    monkeypatch.chdir(tmp_path)
    # Ensure APPENV_BASEDIR is not set
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)

    # Create settings with basedir pointing to the package dir (simulating uvx)
    package_dir = Path(appenv.__file__).parent
    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=package_dir)
    env = appenv.AppEnv(Path.cwd(), settings)

    with pytest.raises(SystemExit) as exc_info:
        env.self_update()

    assert exc_info.value.code == 64  # EXIT_CODE_USAGE
    captured = capsys.readouterr()
    assert "externally managed" in captured.out
    assert "HINT" in captured.out
    assert "appenv self-update ." in captured.out


def test_self_update_path_overrides_externally_managed(tmp_path, monkeypatch, capsys):
    """self-update . works even when running from externally managed env."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)

    # Simulate externally managed (basedir = package dir)
    package_dir = Path(appenv.__file__).parent
    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=package_dir)
    env = appenv.AppEnv(Path.cwd(), settings)

    # Create appenv script in cwd
    old_script = tmp_path / "appenv"
    old_script.write_text(
        '#!/usr/bin/env python3\n__version__ = "0.0.1"\nprint("old")\n'
    )
    old_script.chmod(0o755)

    # Explicit path overrides the externally-managed detection
    args = argparse.Namespace(check=False, path=".")
    env.self_update(args)

    captured = capsys.readouterr()
    assert "Updated" in captured.out

    new_content = old_script.read_text()
    assert appenv.__version__ in new_content


def test_self_update_standalone_delegates_to_uvx(tmp_path, monkeypatch):
    """Standalone self-update delegates to uv tool run appenv self-update."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)

    fake_script = tmp_path / "appenv"
    fake_script.write_text(
        f'#!/usr/bin/env python3\n__version__ = "{appenv.__version__}"\n'
    )
    fake_script.chmod(0o755)

    monkeypatch.setattr(appenv, "__file__", str(fake_script))

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(Path.cwd(), settings)

    fake_uv = argparse.Namespace(bin=Path("/fake/uv"))
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: fake_uv)

    run_calls = []
    captured_kw: dict = {}

    def mock_run(cmd, **kwargs):
        run_calls.append(cmd)
        captured_kw.update(kwargs)
        return argparse.Namespace(returncode=0)

    monkeypatch.setattr("subprocess.run", mock_run)

    with pytest.raises(SystemExit) as exc_info:
        env.self_update()

    assert exc_info.value.code == 0
    assert len(run_calls) == 1
    assert run_calls[0] == [
        Path("/fake/uv"),
        "tool",
        "run",
        "--prerelease=allow",
        "appenv",
        "self-update",
        str(tmp_path),
    ]
    # Every subprocess boundary receives an explicit env dict (not None → no
    # silent os.environ inheritance). APPENV_BASEDIR tells the spawned child
    # appenv where the project lives.
    assert captured_kw.get("env") is not None
    assert isinstance(captured_kw["env"], dict)
    assert captured_kw["env"].get("APPENV_BASEDIR") == str(env.base)


def test_self_update_standalone_delegates_to_uvx_with_check(tmp_path, monkeypatch):
    """Standalone self-update --check delegates to uvx with --check flag."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)

    fake_script = tmp_path / "appenv"
    fake_script.write_text(
        f'#!/usr/bin/env python3\n__version__ = "{appenv.__version__}"\n'
    )
    fake_script.chmod(0o755)

    monkeypatch.setattr(appenv, "__file__", str(fake_script))

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(Path.cwd(), settings)

    fake_uv = argparse.Namespace(bin=Path("/fake/uv"))
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: fake_uv)

    run_calls = []

    def mock_run(cmd, **kwargs):
        run_calls.append(cmd)
        return argparse.Namespace(returncode=0)

    monkeypatch.setattr("subprocess.run", mock_run)

    args = argparse.Namespace(check=True)
    with pytest.raises(SystemExit) as exc_info:
        env.self_update(args)

    assert exc_info.value.code == 0
    assert len(run_calls) == 1
    assert run_calls[0] == [
        Path("/fake/uv"),
        "tool",
        "run",
        "--prerelease=allow",
        "appenv",
        "self-update",
        "--check",
        str(tmp_path),
    ]


def test_self_update_standalone_uvx_failure(tmp_path, monkeypatch):
    """Standalone self-update propagates uvx failure exit code."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)

    fake_script = tmp_path / "appenv"
    fake_script.write_text(
        f'#!/usr/bin/env python3\n__version__ = "{appenv.__version__}"\n'
    )
    fake_script.chmod(0o755)

    monkeypatch.setattr(appenv, "__file__", str(fake_script))

    settings = appenv.AppEnvSettings(verbose=False, extras=[], basedir=tmp_path)
    env = appenv.AppEnv(Path.cwd(), settings)

    fake_uv = argparse.Namespace(bin=Path("/fake/uv"))
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: fake_uv)

    def mock_run(cmd, **kwargs):
        return argparse.Namespace(returncode=1)

    monkeypatch.setattr("subprocess.run", mock_run)

    with pytest.raises(SystemExit) as exc_info:
        env.self_update()

    assert exc_info.value.code == 1


def test_self_update_standalone_script(monkeypatch):
    """self_update calls _self_update_via_uvx for standalone script."""
    base_dir = Path(appenv.__file__).parent.resolve()
    env = appenv.AppEnv(
        base_dir,
        appenv.AppEnvSettings(
            verbose=False,
            extras=[],
            basedir=base_dir,
        ),
    )

    # Trick self_update into taking the standalone (uvx) branch:
    # Make appenv_script point to the actual appenv.py, and base match its parent.
    orig_file = Path(appenv.__file__).resolve()
    env.base = orig_file.parent
    env.appenv_script = orig_file

    mock_uv = MagicMock(spec=appenv.UvBin)
    mock_uv.bin = "/usr/bin/uv"
    monkeypatch.setattr(appenv, "ensure_uv", lambda d: mock_uv)

    mock_result = MagicMock(spec=subprocess.CompletedProcess)
    mock_result.returncode = 0
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: mock_result)

    monkeypatch.setattr(sys, "exit", lambda code: None)

    args = argparse.Namespace(path=None, check=False)
    env.self_update(args)
