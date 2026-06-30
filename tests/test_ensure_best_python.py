# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for appenv.ensure_best_python."""

import subprocess
from pathlib import Path

import pytest

import appenv


@pytest.fixture
def capture_execve(monkeypatch):
    """Mock os.execve to capture calls. Returns list of (path, argv, env) tuples."""
    calls = []

    def mock_execve(path, argv, env):
        calls.append((path, argv, env))
        raise SystemExit(0)

    monkeypatch.setattr("os.execve", mock_execve)
    return calls


# Happy path


def test_ensure_best_python_skips_when_env_set(tmp_path, monkeypatch, make_pyproject):
    """Line 92: Returns early when APPENV_BEST_PYTHON is set."""
    base = tmp_path
    make_pyproject(base, '[project]\nname = "test"\n')

    monkeypatch.setenv("APPENV_BEST_PYTHON", "/usr/bin/python3")
    monkeypatch.setattr("os.chdir", lambda p: None)

    appenv.ensure_best_python(base)


def test_ensure_best_python_already_running_best(tmp_path, monkeypatch, make_pyproject):
    """Line 123: Returns early when already running the best Python."""
    base = tmp_path
    make_pyproject(base, '[project]\nname = "test"\n')

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("os.chdir", lambda p: None)

    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [("3.12", "/usr/bin/python3.12")],
    )

    def mock_resolve(self):
        return Path("/usr/bin/python3.12")

    monkeypatch.setattr("pathlib.Path.resolve", mock_resolve)
    monkeypatch.setattr("sys.executable", "/usr/bin/python3.12")

    appenv.ensure_best_python(base)


def test_ensure_best_python_execv_with_correct_args(
    monkeypatch, tmp_path, make_pyproject, capture_execve
):
    """ensure_best_python calls os.execv with correct args."""
    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("os.chdir", lambda p: None)
    # Simulate running outside a venv (standalone script mode)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")

    base = tmp_path
    make_pyproject(base, '[project]\nrequires-python = ">=3.11"\n')

    # Mock available pythons
    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [
            ("3.12", "/usr/bin/python3.12"),
            ("3.11", "/usr/bin/python3.11"),
        ],
    )
    monkeypatch.setattr("subprocess.check_call", lambda cmd, **kwargs: None)
    monkeypatch.setattr("sys.executable", "/old/python")

    with pytest.raises(SystemExit):
        appenv.ensure_best_python(base)

    assert len(capture_execve) == 1
    # Should pick 3.12 (newest that satisfies >=3.11)
    assert "python3.12" in capture_execve[0][0]
    # APPENV_BEST_PYTHON is in the env dict, not in os.environ
    assert capture_execve[0][2].get("APPENV_BEST_PYTHON") == "/usr/bin/python3.12"


def test_ensure_best_python_respects_upper_bound(
    tmp_path, monkeypatch, capsys, make_pyproject, capture_execve
):
    """ensure_best_python respects upper bound in requires-python."""
    monkeypatch.chdir(tmp_path)
    base = tmp_path

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    # Simulate running outside a venv (standalone script mode)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")

    # Create pyproject.toml with upper bound
    make_pyproject(base, '[project]\nname = "test"\nrequires-python = ">=3.11,<3.14"\n')

    # Mock find_available_pythons to return versions including ones exceeding bound
    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [
            ("3.16", "/usr/bin/python3.16"),
            ("3.13", "/usr/bin/python3.13"),
            ("3.12", "/usr/bin/python3.12"),
            ("3.11", "/usr/bin/python3.11"),
        ],
    )

    # Mock os.execve and subprocess.check_call to prevent actual re-exec
    monkeypatch.setattr(
        "subprocess.check_call", lambda cmd, **kwargs: None
    )  # Python works

    # Mock sys.executable to be different from available pythons
    monkeypatch.setattr("sys.executable", "/different/path/python")

    # Call the function - it should call execve and then SystemExit(0)
    with pytest.raises(SystemExit) as exc_info:
        appenv.ensure_best_python(base)

    # Should have exited via our mock (code 0), not the error path (code 65)
    assert exc_info.value.code == 0

    # Verify Python 3.13 was chosen (newest that satisfies >=3.11,<3.14)
    # 3.16 should be skipped (>= 3.14 upper bound)
    assert len(capture_execve) == 1
    assert "python3.13" in capture_execve[0][0]


# Error cases


def test_ensure_best_python_exits_65_no_python_found(
    monkeypatch, tmp_path, capsys, make_pyproject
):
    """ensure_best_python exits with code 65 when no Python found."""
    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("os.chdir", lambda p: None)
    # Simulate running outside a venv (standalone script mode)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")

    base = tmp_path
    make_pyproject(base, '[project]\nrequires-python = ">=3.99"\n')

    # No Python available
    monkeypatch.setattr(appenv, "find_available_pythons", list)

    with pytest.raises(SystemExit) as err:
        appenv.ensure_best_python(base)

    assert err.value.code == 65
    captured = capsys.readouterr()
    assert "requires-python:" in captured.out


def test_ensure_best_python_exits_65_with_upper_bound(
    monkeypatch, tmp_path, capsys, make_pyproject
):
    """ensure_best_python shows upper bound in error message."""
    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("os.chdir", lambda p: None)
    # Simulate running outside a venv (standalone script mode)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")

    base = tmp_path
    make_pyproject(base, '[project]\nrequires-python = ">=3.99,<4.0"\n')

    # Only have old Python
    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [("3.11", "/usr/bin/python3.11")],
    )

    with pytest.raises(SystemExit) as err:
        appenv.ensure_best_python(base)

    assert err.value.code == 65
    captured = capsys.readouterr()
    # Should show upper bound in error message
    assert "3.99" in captured.out
    assert "<4.0" in captured.out


# Edge cases


def test_ensure_best_python_default_min_version(
    tmp_path, monkeypatch, make_pyproject, capture_execve
):
    """Line 99: Uses 3.10 as default when no requires-python specified."""
    base = tmp_path
    make_pyproject(base, '[project]\nname = "test"\n')

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("os.chdir", lambda p: None)
    # Simulate running outside a venv (standalone script mode)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")

    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [
            ("3.14", "/usr/bin/python3.14"),
            ("3.10", "/usr/bin/python3.10"),
            ("3.9", "/usr/bin/python3.9"),
        ],
    )

    monkeypatch.setattr("subprocess.check_call", lambda cmd, **kwargs: None)
    monkeypatch.setattr("sys.executable", "/different/python")

    with pytest.raises(SystemExit):
        appenv.ensure_best_python(base)

    assert "python3.14" in capture_execve[0][0]


def test_ensure_best_python_broken_python(
    tmp_path, monkeypatch, make_pyproject, capture_execve
):
    """Lines 132-133: Continues to next Python when subprocess fails."""
    base = tmp_path
    make_pyproject(base, '[project]\nname = "test"\n')

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("os.chdir", lambda p: None)
    # Simulate running outside a venv (standalone script mode)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")

    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [
            ("3.12", "/usr/bin/python3.12"),
            ("3.11", "/usr/bin/python3.11"),
        ],
    )

    check_call_count = []

    def mock_check_call(cmd, **kwargs):
        check_call_count.append(cmd)
        if "python3.12" in str(cmd):
            raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr("subprocess.check_call", mock_check_call)
    monkeypatch.setattr("sys.executable", "/different/python")

    with pytest.raises(SystemExit):
        appenv.ensure_best_python(base)

    assert len(check_call_count) == 2
    assert "python3.11" in capture_execve[0][0]


def test_no_compatible_python_not_leaked_to_verbose_stdout(
    monkeypatch, tmp_path, capsys, make_pyproject
):
    """F13: 'no-compatible-python' debug log is hidden from verbose stdout.

    ``ensure_best_python`` logs ``no-compatible-python:`` at ERROR when no
    available Python satisfies ``requires-python``. Under ``APPENV_VERBOSE=1``
    the verbose console handler configured by :func:`setup_logging` filters
    that internal line out via ``_ConsoleDiagnosticFilter`` — it stays in the
    file log for developers but does not pollute the user's verbose stdout.
    The user-facing ``requires-python: >=X.Y`` print() IS shown.

    SPEC: fix-init-safety-layer::no-compatible-python-hidden
    """
    import logging

    log = logging.getLogger("appenv")
    saved_handlers = list(log.handlers)
    saved_level = log.level

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("os.chdir", lambda p: None)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")
    monkeypatch.setenv("APPENV_VERBOSE", "1")

    base = tmp_path
    make_pyproject(base, '[project]\nrequires-python = ">=3.99"\nname = "x"\n')
    # No Python available — triggers the no-compatible-python path.
    monkeypatch.setattr(appenv, "find_available_pythons", list)

    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    # Mirror what AppEnv.meta() does after reading APPENV_VERBOSE=1: attach
    # the verbose console handler with _ConsoleDiagnosticFilter.
    appenv.setup_logging("bestpython", log_dir, verbose=True)

    try:
        with pytest.raises(SystemExit) as err:
            appenv.ensure_best_python(base)
        assert err.value.code == appenv.EXIT_CODE_DATAERR

        captured = capsys.readouterr()
        assert "no-compatible-python:" not in captured.out
        assert "requires-python:" in captured.out
    finally:
        for handler in log.handlers[:]:
            handler.close()
            log.removeHandler(handler)
        for handler in saved_handlers:
            log.addHandler(handler)
        log.setLevel(saved_level)


def test_ensure_best_python_skips_in_venv_with_compatible_python(
    tmp_path, monkeypatch, make_pyproject, capture_execve
):
    """ensure_best_python skips re-exec when in venv with compatible Python."""
    base = tmp_path
    make_pyproject(base, '[project]\nrequires-python = ">=3.11"\n')

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    # Simulate running inside a venv with Python 3.12 (satisfies >=3.11)
    monkeypatch.setattr("sys.prefix", "/path/to/venv")
    monkeypatch.setattr("sys.base_prefix", "/usr")
    monkeypatch.setattr("sys.version_info", (3, 12, 0))

    # Even if better pythons are available, should NOT re-exec
    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [("3.14", "/usr/bin/python3.14")],
    )

    appenv.ensure_best_python(base)
    assert capture_execve == []


def test_ensure_best_python_searches_in_venv_with_incompatible_python(
    tmp_path, monkeypatch, make_pyproject, capture_execve
):
    """ensure_best_python searches when in env with incompatible Python.

    This covers the NixOS case where sys.prefix != sys.base_prefix (NixOS Python
    environments look like venvs) but the Python version doesn't satisfy the
    project's requires-python constraint.
    """
    base = tmp_path
    make_pyproject(base, '[project]\nrequires-python = ">=3.13,<3.15"\n')

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    # Simulate NixOS env: prefix != base_prefix, but Python 3.12 (too old)
    monkeypatch.setattr("sys.prefix", "/nix/store/abc-python3-3.12.12-env")
    monkeypatch.setattr("sys.base_prefix", "/nix/store/xyz-python3-3.12.12")
    monkeypatch.setattr("sys.version_info", (3, 12, 0))
    monkeypatch.setattr(
        "sys.executable", "/nix/store/abc-python3-3.12.12-env/bin/python3.12"
    )

    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [("3.13", "/usr/bin/python3.13")],
    )
    monkeypatch.setattr("subprocess.check_call", lambda cmd, **kwargs: None)

    with pytest.raises(SystemExit):
        appenv.ensure_best_python(base)

    assert len(capture_execve) == 1
    assert "python3.13" in capture_execve[0][0]


def test_ensure_best_python_exits_in_venv_when_no_compatible_python(
    tmp_path, monkeypatch, capsys, make_pyproject
):
    """ensure_best_python exits 65 in env with incompatible Python, no alternative."""
    base = tmp_path
    make_pyproject(base, '[project]\nrequires-python = ">=3.13,<3.15"\n')

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    # NixOS env with Python 3.12, no 3.13 available anywhere
    monkeypatch.setattr("sys.prefix", "/nix/store/abc-python3-3.12.12-env")
    monkeypatch.setattr("sys.base_prefix", "/nix/store/xyz-python3-3.12.12")
    monkeypatch.setattr("sys.version_info", (3, 12, 0))

    monkeypatch.setattr(appenv, "find_available_pythons", lambda: [])

    with pytest.raises(SystemExit) as err:
        appenv.ensure_best_python(base)

    assert err.value.code == 65
    captured = capsys.readouterr()
    assert "requires-python:" in captured.out


def test_ensure_best_python_already_running_best_logs(
    tmp_path, monkeypatch, caplog, make_pyproject
):
    """Debug log when already running the best available Python."""
    import logging

    monkeypatch.delenv("APPENV_BEST_PYTHON", raising=False)
    monkeypatch.setattr("sys.prefix", "/usr")
    monkeypatch.setattr("sys.base_prefix", "/usr")

    make_pyproject(tmp_path, '[project]\nrequires-python = ">=3.11"\n')

    monkeypatch.setattr(
        appenv,
        "find_available_pythons",
        lambda: [("3.14", "/usr/bin/python3.14")],
    )
    monkeypatch.setattr("sys.executable", "/usr/bin/python3.14")

    def mock_resolve(self):
        return Path("/usr/bin/python3.14")

    monkeypatch.setattr("pathlib.Path.resolve", mock_resolve)

    with caplog.at_level(logging.DEBUG):
        appenv.ensure_best_python(tmp_path)

    assert "python-already-best:" in caplog.text
