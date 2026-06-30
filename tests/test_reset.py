# SPDX-FileCopyrightText: 2020 Flying Circus
from pathlib import Path

import appenv


def test_reset_nonexisting_envdir_silent(tmp_path, test_settings):
    env = appenv.AppEnv(Path.cwd(), test_settings(tmp_path))
    assert not env.appenv_dir.exists()
    env.reset()
    assert not env.appenv_dir.exists()
    assert tmp_path.exists()


def test_reset_removes_envdir_with_subdirs(tmp_path, test_settings):
    """reset() cleans up contents in .appenv."""
    env = appenv.AppEnv(Path.cwd(), test_settings(tmp_path))
    env.appenv_dir.mkdir(parents=True)
    # Create some subdirectories
    (env.appenv_dir / "subdir1").mkdir()
    (env.appenv_dir / "subdir2").mkdir()
    assert env.appenv_dir.exists()
    env.reset()
    # .appenv should still exist but be empty (or only contain .uv)
    assert env.appenv_dir.exists()
    # No subdirectories left (except possibly .uv)
    remaining = list(env.appenv_dir.iterdir())
    assert all(p.name == ".uv" for p in remaining)


def test_reset_warns_about_unmanaged_real_venv(
    tmp_path, capsys, test_settings, patterns
):
    """reset() warns about a real .venv directory it does not manage and leaves it.

    The incidental setup shape (``.venv/bin/python`` vs an empty ``bin/``) is
    irrelevant: reset never iterates ``.venv`` contents, so both reduce to the
    same "exists but is not a symlink" note.
    """
    base = tmp_path / "myproject"
    base.mkdir()
    venv = base / ".venv"
    venv.mkdir()
    (venv / "bin").mkdir()
    (venv / "bin" / "python").write_text("#!/bin/sh\necho python")

    assert venv.exists()

    env = appenv.AppEnv(Path.cwd(), test_settings(base))
    env.reset()

    # .venv should still exist (not managed by appenv)
    assert venv.exists()
    captured = capsys.readouterr()
    patterns.main.in_order("....venv...not a symlink...")
    patterns.no_errors.refused("...error...")
    full = patterns.full
    full.merge("main", "no_errors")
    assert full == captured.out


def test_reset_removes_venv_symlink_and_managed_venv(
    tmp_path, capsys, test_settings, patterns
):
    """reset() removes the .venv symlink and the managed .appenv/venv it points at.

    Merges the fs-only check (symlink + real venv removed, .appenv survives) with
    the structural output check: both ``Removing`` lines appear in order.
    """
    base = tmp_path / "myproject"
    base.mkdir()

    # Create .venv (as symlink to .appenv/venv)
    appenv_dir = base / ".appenv"
    appenv_dir.mkdir()
    venv_real = appenv_dir / "venv"
    venv_real.mkdir()
    venv_link = base / ".venv"
    venv_link.symlink_to(".appenv/venv")

    assert venv_link.exists()
    assert appenv_dir.exists()

    env = appenv.AppEnv(Path.cwd(), test_settings(base))
    env.reset()

    # Symlink removed, real venv removed, .appenv survives.
    assert not venv_link.exists()
    assert appenv_dir.exists()
    assert not venv_real.exists()

    captured = capsys.readouterr()
    patterns.main.in_order(
        """\
Removing ....venv symlink ...
Removing ...venv ..."""
    )
    patterns.no_errors.refused("...error...")
    full = patterns.full
    full.merge("main", "no_errors")
    assert full == captured.out


def test_reset_unlinks_file_in_appenv(workdir, monkeypatch, capsys):
    """Line 1108: reset() unlinks non-directory files in .appenv."""
    base = Path(workdir)

    # Create .appenv with a file (not directory)
    appenv_dir = base / ".appenv"
    appenv_dir.mkdir()
    old_file = appenv_dir / "old_file.txt"
    old_file.write_text("old content")

    env = appenv.AppEnv(
        Path.cwd(),
        appenv.AppEnvSettings(verbose=True, extras=[], basedir=Path.cwd()),
    )
    env.reset()

    assert not old_file.exists()
    captured = capsys.readouterr()
    assert "Removing" in captured.out


def test_reset_removes_real_venv(workdir, monkeypatch, capsys, test_settings):
    """reset() removes .appenv/venv directory."""
    base = Path(workdir)

    # Create .appenv/venv
    appenv_dir = base / ".appenv"
    appenv_dir.mkdir()
    venv_real = appenv_dir / "venv"
    venv_real.mkdir()
    (venv_real / "bin").mkdir()

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))
    env.reset()

    assert not venv_real.exists()
    captured = capsys.readouterr()
    assert "Removing" in captured.out


# ==============================================================================
# Reset and project detection tests
# ==============================================================================


def test_reset_keeps_uv_binary(tmp_path, monkeypatch, capsys, test_settings):
    """Reset keeps .appenv/.uv directory (uv binary cache)."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    # Create .appenv/.uv
    uv_dir = base / ".appenv" / ".uv"
    uv_dir.mkdir(parents=True)
    (uv_dir / "bin").mkdir()
    (uv_dir / "bin" / "uv").write_text("#!/bin/bash")

    env = appenv.AppEnv(Path.cwd(), test_settings(Path.cwd()))
    env.reset()

    # .appenv/.uv should still exist
    assert uv_dir.exists()
    assert (uv_dir / "bin" / "uv").exists()
