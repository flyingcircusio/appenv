# SPDX-FileCopyrightText: 2020 Flying Circus
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

import appenv
from appenv import UvVersion


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


@pytest.fixture(autouse=True)
def _fake_tty(monkeypatch):
    """Pretend stdin is a TTY so interactive init works in tests."""
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)


class MockUvBin:
    """Mock UvBin that doesn't execute subprocesses."""

    def __init__(self):
        self.base = Path("/tmp")
        self.bin = Path("/usr/bin/uv")
        self._version = UvVersion(0, 5, 0)

    @property
    def version(self):
        return self._version

    def cmd(self, args, verbose=False, **kwargs):
        return ""


@pytest.fixture(autouse=True)
def disable_argparse_colors(monkeypatch):
    """Disable argparse colors (Python 3.14+) for stable output assertions."""
    monkeypatch.setenv("NO_COLOR", "1")


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory for regression tests."""
    return Path(__file__).parent.parent


# SPEC: test-cwd-isolation — stable cwd baseline for the autouse restore fixture.
_INVOCATION_CWD = Path.cwd()


@pytest.fixture(autouse=True)
def _isolate_cwd():
    """Restore the process cwd after every test to stop order-pollution."""
    try:
        saved = Path.cwd()
    except OSError:
        saved = _INVOCATION_CWD
    yield
    try:
        os.chdir(saved)
    except OSError:
        os.chdir(_INVOCATION_CWD)


@pytest.fixture
def workdir(tmp_path):
    """Change to tmp_path for test duration, restore afterwards."""
    # Handle case where previous test removed current directory
    try:
        old = Path.cwd()
    except OSError:
        old = str(tmp_path)
    os.chdir(tmp_path)
    yield tmp_path
    try:
        os.chdir(old)
    except OSError:
        # If old directory no longer exists, use tmp_path
        os.chdir(tmp_path)


@pytest.fixture
def test_settings(tmp_path):
    """Fixture providing AppEnvSettings with sensible test defaults.

    Yields a factory function that accepts optional basedir.
    """

    def _test_settings(basedir=None):
        return appenv.AppEnvSettings(
            verbose=False,
            extras=[],
            basedir=basedir or tmp_path,
        )

    return _test_settings


@pytest.fixture
def mock_uv():
    """Fixture providing a mock UvBin that doesn't execute subprocesses."""
    return MockUvBin()


@pytest.fixture(autouse=True)
def mock_uv_version(monkeypatch, request):
    """Auto-mock UvBin.get_uv_version to avoid subprocess calls in tests.

    Tests that mock ensure_uv to return a fake UvBin instance need get_uv_version
    to also be mocked, otherwise it tries to run the fake binary.

    Tests that directly test get_uv_version behavior can disable this
    by using the @pytest.mark.no_mock_uv_version decorator.
    """
    # Skip for tests that directly test get_uv_version
    if request.node.get_closest_marker("no_mock_uv_version"):
        return

    # Mock UvVersion to return a valid version
    mock_version = UvVersion(0, 5, 0)

    # Mock the get_uv_version method on UvBin class (static method)
    def mockget_uv_version(uv_path):
        return mock_version

    monkeypatch.setattr(appenv.UvBin, "get_uv_version", mockget_uv_version)

    # Also mock ensure_uv to prevent UvBin discovery in tests
    monkeypatch.setattr(appenv, "ensure_uv", lambda base: MockUvBin())


@pytest.fixture
def subprocess_run_fail(monkeypatch):
    def fail(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1, cmd="test_cmd", stderr="test_stderr"
        )

    monkeypatch.setattr(subprocess, "run", fail)


@pytest.fixture
def app_env(test_settings):
    """Factory fixture for AppEnv with test defaults."""

    def _app_env(basedir=None):
        basedir = basedir or Path.cwd()
        return appenv.AppEnv(basedir, test_settings(basedir))

    return _app_env


@pytest.fixture
def make_mock_uv():
    """Factory fixture for creating MockUvBin with custom version/cmd."""

    def _make(version=None, cmd_fn=None):
        if version is None:
            version = UvVersion(0, 5, 0)
        uv = MockUvBin()
        uv._version = version
        if cmd_fn:
            uv.cmd = cmd_fn
        return uv

    return _make


@pytest.fixture
def no_ensure_python(monkeypatch):
    """Mock ensure_best_python to prevent re-exec."""
    monkeypatch.setattr(appenv, "ensure_best_python", lambda base: None)


@pytest.fixture
def mock_cmd_python(monkeypatch):
    """Mock appenv.cmd to return Python 3.12.0."""
    monkeypatch.setattr(appenv, "cmd", lambda c, **kwargs: b"Python 3.12.0")


@pytest.fixture
def create_venv(tmp_path):
    """Factory fixture for creating venv directory structures."""

    def _create(base=None, python_output="Python 3.12.0"):
        base = base or tmp_path
        venv = base / ".appenv" / "venv"
        venv.mkdir(parents=True, exist_ok=True)
        (venv / "bin").mkdir(exist_ok=True)
        python = venv / "bin" / "python"
        python.write_text(f"#!/bin/sh\necho {python_output}\n")
        python.chmod(0o755)
        return venv

    return _create


@pytest.fixture
def mock_uv_lock(monkeypatch):
    """Mock AppEnv._uv_lock to prevent actual uv execution."""
    monkeypatch.setattr(appenv.AppEnv, "_uv_lock", lambda self, uv, diff=False: None)


@pytest.fixture
def mock_logdir(tmp_path, monkeypatch):
    """Mock AppEnv._set_up_logdir to use tmp_path/logs."""
    mock_log_dir = tmp_path / "logs"
    mock_log_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(appenv.AppEnv, "_set_up_logdir", lambda self: mock_log_dir)


@pytest.fixture
def make_pyproject():
    """Factory to create pyproject.toml + uv.lock in a base directory."""

    def _make(base, pyproject_content, lock_content="version = 1\n"):
        (base / "pyproject.toml").write_text(pyproject_content)
        (base / "uv.lock").write_text(lock_content)

    return _make


@pytest.fixture
def make_venv_creating_cmd():
    """Factory: build a mock uv.cmd that materializes the venv FS on ``venv`` calls.

    Mirrors ``make_mock_uv`` / ``make_pyproject``: request the fixture, then call
    the returned factory with ``base`` (defaults to the current cwd) and optional
    ``python_content`` to obtain a ``cmd(args, verbose=False, **kwargs)`` callable
    that creates ``<base>/.appenv/venv`` when ``"venv"`` is in ``args``.
    """

    def _make(base=None, python_content="#!/bin/sh\n"):
        if base is None:
            base = Path.cwd()

        def cmd(args, verbose=False, **kwargs):
            if "venv" in args:
                venv = base / ".appenv" / "venv"
                venv.mkdir(parents=True, exist_ok=True)
                (venv / "bin").mkdir(exist_ok=True)
                (venv / "bin" / "python").write_text(python_content)
            return ""

        return cmd

    return _make


class _LateBindStreamHandler(logging.StreamHandler):
    """StreamHandler that resolves sys.stdout at emit time, not construction time.

    Fixes incompatibility between fixtures that add a StreamHandler to ``sys.stdout``
    and pytest's ``capsys`` fixture: when the handler is created in fixture setup,
    ``sys.stdout`` is a ``CaptureIO`` that may be closed before the test function
    uses the handler. This handler always reads ``sys.stdout`` at emit time,
    avoiding stale references to a closed stream.
    """

    def __init__(self):
        logging.Handler.__init__(self)

    @property
    def stream(self):
        return sys.stdout

    @stream.setter
    def stream(self, value):
        pass  # We don't store a stream reference

    def _open(self):
        return sys.stdout


@pytest.fixture
def capture_appenv_logs():
    """Capture appenv debug logs to stdout for pattern assertions."""
    log = logging.getLogger("appenv")
    handler = _LateBindStreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    yield log
    log.removeHandler(handler)
