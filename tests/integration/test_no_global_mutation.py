# SPDX-FileCopyrightText: 2020 Flying Circus
"""Integration tests: os.environ must not be mutated by any workflow.

These tests run full AppEnv workflows (run, run_uv, prepare, main) and
verify that os.environ stays untouched after the call. They are
integration-level because they exercise the complete code path end-to-end,
not just a single function.
"""

import argparse
import os

import pytest

import appenv
from tests.conftest import MockUvBin


def test_no_global_mutation_run_uv_leaves_uv_project_env_alone(
    monkeypatch, tmp_path, app_env, make_pyproject
):
    make_pyproject(tmp_path, '[project]\nname = "test"\n')
    env = app_env(tmp_path)
    mock_uv = MockUvBin()
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: mock_uv)
    monkeypatch.setattr("os.chdir", lambda d: None)

    # Mock both execv (current behaviour) and execve (target behaviour)
    # so the test stays robust across the refactor.
    def fake_execv(path, argv):
        raise SystemExit(0)

    def fake_execve(path, argv, env_dict):
        raise SystemExit(0)

    monkeypatch.setattr("os.execv", fake_execv)
    monkeypatch.setattr("os.execve", fake_execve)
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)

    with pytest.raises(SystemExit):
        env.run_uv(argparse.Namespace(), ["pip", "list"])

    assert "UV_PROJECT_ENVIRONMENT" not in os.environ


def test_no_global_mutation_prepare_leaves_uv_project_env_alone(
    tmp_path,
    monkeypatch,
    app_env,
    mock_uv,
    mock_cmd_python,
    make_pyproject,
    make_venv_creating_cmd,
):
    """After prepare(), os.environ has no UV_PROJECT_ENVIRONMENT set."""
    monkeypatch.chdir(tmp_path)
    make_pyproject(tmp_path, '[project]\nname = "test"\ndependencies = []\n')
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: mock_uv)

    mock_uv.cmd = make_venv_creating_cmd(base=tmp_path)

    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    app_env().prepare()
    assert "UV_PROJECT_ENVIRONMENT" not in os.environ


def test_no_global_mutation_main_does_not_pop_pythonpath(
    monkeypatch, no_ensure_python, mock_logdir
):
    """main() must not pop PYTHONPATH from os.environ.

    Today main() does ``os.environ.pop("PYTHONPATH", None)`` for venv
    isolation. After FIX #3 the filter lives inside ``_build_env`` so
    every child process gets a clean env without mutating the parent.
    """
    monkeypatch.setattr("sys.argv", ["appenv"])
    monkeypatch.setattr(appenv, "__file__", "/some/path/appenv")
    monkeypatch.setenv("PYTHONPATH", "/keep/this")
    with pytest.raises(SystemExit):
        appenv.main()
    assert os.environ.get("PYTHONPATH") == "/keep/this"


def test_no_global_mutation_run_leaves_appenv_basedir_alone(
    monkeypatch, tmp_path, app_env, make_pyproject
):
    """After AppEnv.run, APPENV_BASEDIR is not set in os.environ."""
    env = app_env(tmp_path)
    make_pyproject(tmp_path, '[project]\nname = "test"\n')

    env_dir = tmp_path / ".appenv" / "venv"
    env_dir.mkdir(parents=True)
    (env_dir / "bin").mkdir()
    myapp = env_dir / "bin" / "myapp"
    myapp.write_text("#!/bin/sh\n")
    myapp.chmod(0o755)

    monkeypatch.setattr(env, "_prepare_venv", lambda dev_mode=False: env_dir)
    monkeypatch.setattr("os.chdir", lambda p: None)

    def fake_execv(path, argv):
        raise SystemExit(0)

    def fake_execve(path, argv, env_dict):
        raise SystemExit(0)

    monkeypatch.setattr("os.execv", fake_execv)
    monkeypatch.setattr("os.execve", fake_execve)
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)

    with pytest.raises(SystemExit):
        env.run("myapp", ["--help"])

    assert "APPENV_BASEDIR" not in os.environ
