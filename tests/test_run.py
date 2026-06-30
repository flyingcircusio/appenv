# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for AppEnv.run(), run_script(), python() and related."""

import argparse
import os

import pytest

import appenv

from .conftest import MockUvBin


def test_run_sets_env_and_execs(monkeypatch, tmp_path, app_env, make_pyproject):
    app_env_instance = app_env()

    # Add pyproject.toml and uv.lock so _prepare_venv doesn't exit
    make_pyproject(tmp_path, '[project]\nname = "test"\nversion = "0.1.0"\n')

    env_dir = tmp_path / ".appenv" / "abc123"
    env_dir.mkdir(parents=True)
    bin_dir = env_dir / "bin"
    bin_dir.mkdir()
    (bin_dir / "myapp").write_text("#!/bin/sh\necho hello\n")

    monkeypatch.setattr(
        app_env_instance, "_prepare_venv", lambda dev_mode=False: env_dir
    )

    execve_called = []
    monkeypatch.setattr(
        os,
        "execve",
        lambda path, argv, env_dict: execve_called.append((path, argv, env_dict)),
    )
    monkeypatch.setattr("os.chdir", lambda p: None)

    app_env_instance.run("myapp", ["--help"])

    assert len(execve_called) == 1
    path, _argv, env_dict = execve_called[0]
    assert "myapp" in path
    assert env_dict.get("APPENV_BASEDIR") == str(app_env_instance.base)


def test_run_missing_binary_shows_helpful_error(
    monkeypatch, tmp_path, capsys, app_env, patterns
):
    env = app_env()

    env_dir = tmp_path / ".appenv" / "venv"
    bin_dir = env_dir / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "python").write_text("#!/bin/sh\necho python\n")
    (bin_dir / "ruff").write_text("#!/bin/sh\necho ruff\n")

    monkeypatch.setattr(env, "_prepare_venv", lambda dev_mode=False: env_dir)

    with pytest.raises(SystemExit) as exc_info:
        env.run("myapp", ["--help"])

    assert exc_info.value.code == appenv.EXIT_CODE_NOINPUT

    captured = capsys.readouterr()

    patterns.main.in_order(
        """\
...Error: Binary '...' not found in .../bin/
...The symlink '...' determines which binary gets executed.
...Available binaries:
...python...
...ruff...
...Either:
...Install a package that provides the '...' binary
...[project.scripts]...
...Or create a symlink with the name of an installed binary"""
    )
    patterns.no_errors.optional("...")

    full_pattern = patterns.full
    full_pattern.merge("main")
    full_pattern.merge("no_errors")

    full_pattern.generate_example()

    assert full_pattern == captured.out


def test_run_missing_binary_empty_venv(monkeypatch, tmp_path, capsys, app_env):
    """Line 690: run() shows 'No binaries found' when venv/bin/ is empty."""
    env = app_env()

    # Create empty venv/bin/ directory (no binaries)
    env_dir = tmp_path / ".appenv" / "venv"
    bin_dir = env_dir / "bin"
    bin_dir.mkdir(parents=True)
    # bin_dir is intentionally empty

    monkeypatch.setattr(env, "_prepare_venv", lambda dev_mode=False: env_dir)

    with pytest.raises(SystemExit) as exc_info:
        env.run("myapp", ["--help"])

    assert exc_info.value.code == appenv.EXIT_CODE_NOINPUT
    captured = capsys.readouterr()
    assert "No binaries found in the virtual environment" in captured.out


def test_run_uv_sets_environment_and_execs(
    monkeypatch, tmp_path, app_env, no_ensure_python, mock_logdir, make_pyproject
):
    """run_uv() passes UV_PROJECT_ENVIRONMENT in the execve env dict."""
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    make_pyproject(tmp_path, '[project]\nname = "test"\n')
    env = app_env(tmp_path)
    mock_uv = MockUvBin()
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: mock_uv)

    execve_called = []
    monkeypatch.setattr(
        os,
        "execve",
        lambda path, argv, env_dict: execve_called.append((path, argv, env_dict)),
    )
    monkeypatch.setattr(os, "chdir", lambda d: None)

    env.run_uv(argparse.Namespace(), ["pip", "install", "pkg"])

    assert len(execve_called) == 1
    path, argv, env_dict = execve_called[0]
    assert path == str(mock_uv.bin)
    assert argv == [str(mock_uv.bin), "pip", "install", "pkg"]
    # UV_PROJECT_ENVIRONMENT is in the env dict, not in os.environ
    assert env_dict.get("UV_PROJECT_ENVIRONMENT") == str(env.venv_real)
    assert os.environ.get("UV_PROJECT_ENVIRONMENT") is None


@pytest.mark.parametrize(
    "remaining_args",
    [
        ["-c", "print(1)"],
        ["-m", "pdb", "script.py"],
    ],
)
def test_python_delegates_to_run(monkeypatch, tmp_path, app_env, remaining_args):
    """python() delegates to run() with command and remaining args."""
    env = app_env()

    run_called = []
    monkeypatch.setattr(env, "run", lambda cmd, argv: run_called.append((cmd, argv)))

    env.python(argparse.Namespace(), remaining_args)

    assert run_called == [("python", remaining_args)]


def test_run_script_delegates(monkeypatch, tmp_path, app_env):
    """run_script() delegates to run_uv with 'run' prepended to remaining."""
    env = app_env()

    called = []
    monkeypatch.setattr(env, "run_uv", lambda args, remaining: called.append(remaining))

    env.run_script(argparse.Namespace(), ["script_name", "--flag"])

    assert called == [["run", "script_name", "--flag"]]
