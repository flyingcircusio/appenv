# SPDX-FileCopyrightText: 2020 Flying Circus
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

import appenv

"""Tests for appenv_settings_from_env()."""


# ==============================================================================
# appenv_settings_from_env tests
#
# Pure function reading APPENV_VERBOSE / APPENV_EXTRAS / APPENV_BASEDIR from the
# environment. Sole caller is main() (run on every appenv invocation, before
# ensure_best_python). No autouse fixture clears APPENV_*, so each test must
# manage the vars it cares about to avoid cross-test / shell-env interference.
# monkeypatch.{setenv,delenv} restore automatically.
# ==============================================================================


def _clear_appenv_settings_env(monkeypatch):
    """Remove all APPENV_* settings vars so tests start from a known baseline."""
    for var in ("APPENV_VERBOSE", "APPENV_EXTRAS", "APPENV_BASEDIR"):
        monkeypatch.delenv(var, raising=False)


def test_settings_from_env_defaults_when_unset(monkeypatch):
    _clear_appenv_settings_env(monkeypatch)
    settings = appenv.appenv_settings_from_env()
    assert settings.verbose is False
    assert settings.extras == []
    assert settings.basedir == Path(appenv.__file__).parent


@pytest.mark.parametrize(
    "value", ["1", "true", "yes", "0", "false", "verbose", "anything-non-empty"]
)
def test_settings_from_env_verbose_truthy_when_nonempty_stripped(monkeypatch, value):
    """verbose is truthy: any non-empty stripped value activates it.

    Includes "0"/"false" — Python string truthiness applies; convention is
    APPENV_VERBOSE=1 or =true (SPEC: fix-smell-appenv-verbose-truthy::smell-2).
    """
    _clear_appenv_settings_env(monkeypatch)
    monkeypatch.setenv("APPENV_VERBOSE", value)
    settings = appenv.appenv_settings_from_env()
    assert settings.verbose is True


@pytest.mark.parametrize("value", ["", "   ", "\t", " \n "])
def test_settings_from_env_verbose_false_when_empty_or_whitespace(monkeypatch, value):
    """verbose is False for empty/whitespace-only APPENV_VERBOSE.

    Breaking change (SPEC: fix-smell-appenv-verbose-truthy::smell-2): previously
    `is not None` made ANY set value — even "" or "   " — truthy. Now stripped.
    """
    _clear_appenv_settings_env(monkeypatch)
    monkeypatch.setenv("APPENV_VERBOSE", value)
    settings = appenv.appenv_settings_from_env()
    assert settings.verbose is False


def test_settings_from_env_verbose_false_when_unset(monkeypatch):
    _clear_appenv_settings_env(monkeypatch)
    settings = appenv.appenv_settings_from_env()
    assert settings.verbose is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("dev", ["dev"]),
        ("dev,test", ["dev", "test"]),
        (" dev , test , docs ", ["dev", "test", "docs"]),
        ("dev,,test,", ["dev", "test"]),
        ("", []),
    ],
)
def test_settings_from_env_extras_parsing(monkeypatch, raw, expected):
    _clear_appenv_settings_env(monkeypatch)
    monkeypatch.setenv("APPENV_EXTRAS", raw)
    settings = appenv.appenv_settings_from_env()
    assert settings.extras == expected


def test_settings_from_env_extras_unset_yields_empty(monkeypatch):
    _clear_appenv_settings_env(monkeypatch)
    settings = appenv.appenv_settings_from_env()
    assert settings.extras == []


def test_settings_from_env_extras_deduplicated(monkeypatch):
    """APPENV_EXTRAS is deduplicated, preserving first-occurrence order.

    Mirrors the ``--dep`` dedup path (``_dedup_preserve_order``), so
    ``dev,dev,test`` -> ``["dev", "test"]`` rather than reaching uv as
    ``--extra dev,dev,test``.
    """
    _clear_appenv_settings_env(monkeypatch)
    monkeypatch.setenv("APPENV_EXTRAS", "dev,dev,test")
    settings = appenv.appenv_settings_from_env()
    assert settings.extras == ["dev", "test"]


def test_settings_from_env_basedir_from_env(monkeypatch):
    _clear_appenv_settings_env(monkeypatch)
    monkeypatch.setenv("APPENV_BASEDIR", "/custom/proj")
    settings = appenv.appenv_settings_from_env()
    assert settings.basedir == Path("/custom/proj")


def test_settings_from_env_basedir_default_module_dir(monkeypatch):
    _clear_appenv_settings_env(monkeypatch)
    settings = appenv.appenv_settings_from_env()
    assert settings.basedir == Path(appenv.__file__).parent


def test_settings_from_env_returns_frozen_dataclass(monkeypatch):
    _clear_appenv_settings_env(monkeypatch)
    settings = appenv.appenv_settings_from_env()
    assert isinstance(settings, appenv.AppEnvSettings)
    # setattr (not direct assignment) avoids a false-positive type error on the
    # frozen field while still triggering FrozenInstanceError at runtime.
    with pytest.raises(FrozenInstanceError):
        setattr(settings, "verbose", True)  # noqa: B010
