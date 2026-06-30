# SPDX-FileCopyrightText: 2020 Flying Circus
"""Unit tests for AppEnv._build_env() — the central env-dict builder.

_build_env starts from os.environ.copy(), drops PYTHONPATH (venv
isolation), and applies caller overlays. Every subprocess boundary
and os.execve call receives its env from this function.
"""

import os


def test_build_env_returns_dict_instance(app_env):
    """_build_env returns a plain dict, not the live os.environ mapping."""
    result = app_env()._build_env()
    assert isinstance(result, dict)
    assert result is not os.environ


def test_build_env_preserves_path_and_home(app_env, monkeypatch):
    """_build_env starts from os.environ.copy() — PATH/HOME survive."""
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setenv("HOME", "/home/test")
    result = app_env()._build_env()
    assert result["PATH"] == "/usr/bin:/bin"
    assert result["HOME"] == "/home/test"


def test_build_env_drops_pythonpath(app_env, monkeypatch):
    """PYTHONPATH is filtered out — venv isolation, no global pop in main().

    Today ``main()`` pops PYTHONPATH globally. After FIX #3 the filter
    lives inside ``_build_env`` so each child gets a clean env without
    mutating the parent's ``os.environ``.
    """
    monkeypatch.setenv("PYTHONPATH", "/some/leaked/path")
    result = app_env()._build_env()
    assert "PYTHONPATH" not in result


def test_build_env_applies_overlays(app_env):
    """_build_env(overlays) merges caller-supplied keys."""
    result = app_env()._build_env({"FOO": "bar", "BAZ": "qux"})
    assert result["FOO"] == "bar"
    assert result["BAZ"] == "qux"


def test_build_env_overlays_override_os_environ(app_env, monkeypatch):
    """Overlay values take precedence over os.environ."""
    monkeypatch.setenv("FOO", "from-os")
    result = app_env()._build_env({"FOO": "from-overlay"})
    assert result["FOO"] == "from-overlay"


def test_build_env_does_not_mutate_os_environ(app_env, monkeypatch):
    """Building the env dict has zero side effects on os.environ."""
    monkeypatch.setenv("PYTHONPATH", "/keep-me")
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)
    snapshot = dict(os.environ)
    app_env()._build_env({"UV_PROJECT_ENVIRONMENT": "/tmp/venv"})
    assert dict(os.environ) == snapshot
    assert os.environ.get("PYTHONPATH") == "/keep-me"
    assert "UV_PROJECT_ENVIRONMENT" not in os.environ
