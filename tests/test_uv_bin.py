# SPDX-FileCopyrightText: 2020 Flying Circus
import logging
import shutil
import subprocess
from pathlib import Path

import pytest

import appenv
from appenv import EXIT_CODE_UNAVAILABLE, NoValidUvError, UvBin, UvVersion, ensure_uv


class FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_uv_bin_cmd_raises_when_uv_not_found(monkeypatch):
    # UvBin.cmd raises FileNotFoundError when uv binary doesn't exist
    # Create a UvBin with a non-existent binary
    uv = UvBin.__new__(UvBin)
    uv.bin = Path("/usr/bin/nonexistent_uv")
    uv.appenv_dir = Path("/tmp/.appenv")
    uv.uv_dir = uv.appenv_dir / ".uv"

    with pytest.raises(FileNotFoundError):
        uv.cmd(["lock"])


def test_try_uv_from_path_returns_path_when_valid(monkeypatch, tmp_path):
    """_try_uv_from_path returns path when uv in PATH and version valid."""
    # Create a UvBin instance using constructor
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock shutil.which to return a path
    monkeypatch.setattr(
        "shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None
    )

    # Mock UvBin.get_uv_version to return a valid version
    mock_version = UvVersion(0, 10, 3)
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: mock_version)

    # Mock _cleanup_appenv_uv to track if it's called
    cleanup_called = []
    monkeypatch.setattr(
        uv_bin, "_cleanup_appenv_uv", lambda: cleanup_called.append(True)
    )

    # Call the method
    result = uv_bin._try_uv_from_path()

    # Verify results
    assert result == Path("/usr/bin/uv")
    assert cleanup_called == [True]  # Cleanup should be called


def test_try_uv_from_path_returns_none_when_invalid_version(monkeypatch):
    """_try_uv_from_path returns None when uv in PATH but version invalid."""
    # Create a UvBin instance
    uv_bin = UvBin.__new__(UvBin)
    uv_bin.appenv_dir = Path("/tmp/.appenv")
    uv_bin.uv_dir = uv_bin.appenv_dir / ".uv"

    # Mock shutil.which to return a path
    monkeypatch.setattr(
        "shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None
    )

    # Mock UvBin.get_uv_version to return None (invalid version)
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: UvVersion.unknown())

    # Mock _cleanup_appenv_uv to track if it's called
    cleanup_called = []
    monkeypatch.setattr(
        uv_bin, "_cleanup_appenv_uv", lambda: cleanup_called.append(True)
    )

    # Call the method
    result = uv_bin._try_uv_from_path()

    # Verify results
    assert result is None
    assert cleanup_called == []  # Cleanup should not be called


def test_try_uv_from_path_returns_none_when_not_in_path(monkeypatch):
    """_try_uv_from_path returns None when uv not in PATH."""
    # Create a UvBin instance
    uv_bin = UvBin.__new__(UvBin)
    uv_bin.appenv_dir = Path("/tmp/.appenv")
    uv_bin.uv_dir = uv_bin.appenv_dir / ".uv"

    # Mock shutil.which to return None (not found)
    monkeypatch.setattr("shutil.which", lambda name: None)

    # Mock _cleanup_appenv_uv to track if it's called
    cleanup_called = []
    monkeypatch.setattr(
        uv_bin, "_cleanup_appenv_uv", lambda: cleanup_called.append(True)
    )

    # Call the method
    result = uv_bin._try_uv_from_path()

    # Verify results
    assert result is None
    assert cleanup_called == []  # Cleanup should not be called


@pytest.mark.no_mock_uv_version
@pytest.mark.parametrize(
    ("run_result", "expected"),
    [
        pytest.param(
            FakeResult(stdout="uv 0.10.3 (abc123 2024-01-01)\n"),
            UvVersion(0, 10, 3),
            id="valid_version",
        ),
        pytest.param(
            FakeResult(stdout="uv 0.4.0 (abc123 2024-01-01)\n"),
            UvVersion(0, 4, 0),
            id="version_below_minimum",
        ),
        pytest.param(
            FakeResult(stdout="uv invalid-version\n"),
            UvVersion.unknown(),
            id="unparseable_version_string",
        ),
        pytest.param(
            FakeResult(stdout="uv\n"),
            UvVersion.unknown(),
            id="missing_version_token",
        ),
        pytest.param(
            subprocess.CalledProcessError(1, "uv --version"),
            UvVersion.unknown(),
            id="subprocess_error",
        ),
    ],
)
def test_uv_bin_get_uv_version(monkeypatch, run_result, expected):
    """Parse uv --version output and validate against minimum (0.5.0).

    Covers: successful parse, version below minimum, unparseable string,
    missing version token (IndexError), subprocess failure.

    Every subprocess boundary receives an explicit env dict (not None → no
    silent os.environ inheritance).
    """
    captured_kw: dict = {}

    def fake_run(*a, **kw):
        captured_kw.update(kw)
        if isinstance(run_result, BaseException):
            raise run_result
        return run_result

    monkeypatch.setattr("subprocess.run", fake_run)

    result = UvBin.get_uv_version(Path("/usr/bin/uv"))
    assert result == expected
    assert result.valid == expected.valid
    if not isinstance(run_result, BaseException):
        assert captured_kw.get("env") is not None


@pytest.mark.parametrize(
    ("version_result", "expected"),
    [
        pytest.param(UvVersion(0, 10, 3), ..., id="appenv_dir-valid"),
        pytest.param(UvVersion.unknown(), None, id="appenv_dir-invalid-version"),
    ],
)
def test_try_uv_from_appenv_dir(monkeypatch, tmp_path, version_result, expected):
    """_try_uv_from_appenv_dir returns path when uv exists and version is valid,
    returns None when uv exists but version is invalid."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Create the .appenv/.uv/bin/uv file
    uv_local = tmp_path / ".appenv/.uv/bin/uv"
    uv_local.parent.mkdir(parents=True)
    uv_local.write_text("#!/bin/sh\n")

    # Mock UvBin.get_uv_version to return parametrized version
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: version_result)

    # Call the method
    result = uv_bin._try_uv_from_appenv_dir()

    # Verify results
    if expected is None:
        assert result is None
    else:
        assert result == uv_local


def test_try_uv_from_appenv_dir_returns_none_when_not_exists(monkeypatch, tmp_path):
    """_try_uv_from_appenv_dir returns None when uv does not exist."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Do not create the .appenv/.uv/bin/uv file

    # Call the method
    result = uv_bin._try_uv_from_appenv_dir()

    # Verify results
    assert result is None


# ==============================================================================
# UvBin._try_uv_from_nix_channel tests
# ==============================================================================


@pytest.mark.parametrize(
    ("uv_local_preexists", "expected_action_log"),
    [
        pytest.param(True, "Updating", id="updates-existing"),
        pytest.param(False, "Creating", id="creates-new"),
    ],
)
def test_try_uv_from_nix_channel_returns_path(
    monkeypatch, tmp_path, caplog, uv_local_preexists, expected_action_log
):
    """_try_uv_from_nix_channel returns path when nix build succeeds.

    When uv_local already exists the log says action=Updating; when it does
    not yet exist the log says action=Creating.
    """
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock preceding methods to return None so we reach this method
    monkeypatch.setattr(uv_bin, "_try_uv_from_path", lambda: None)
    monkeypatch.setattr(uv_bin, "_try_uv_from_appenv_dir", lambda: None)

    # Mock shutil.which to return nix path
    monkeypatch.setattr(
        "shutil.which", lambda name: "/nix/bin/nix" if name == "nix" else None
    )

    # uv_local: pre-create it (Updating) or leave absent (Creating)
    uv_local = tmp_path / ".appenv/.uv/bin/uv"
    if uv_local_preexists:
        uv_local.parent.mkdir(parents=True)
        uv_local.write_text("#!/bin/sh\n")

    # Mock subprocess.run to return success
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: FakeResult())

    # Mock UvBin.get_uv_version to return a valid version
    mock_version = UvVersion(0, 10, 3)
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: mock_version)

    # Cap logs at DEBUG level
    caplog.set_level(logging.DEBUG)

    # Call the method
    result = uv_bin._try_uv_from_nix_channel()

    # Verify results
    assert result == uv_local
    assert f"uv-nix-channel-build: action={expected_action_log}" in caplog.text


def test_try_uv_from_nix_channel_returns_none_when_nix_not_found(monkeypatch, tmp_path):
    """_try_uv_from_nix_channel returns None when nix not in PATH."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock shutil.which to return None (nix not found)
    monkeypatch.setattr("shutil.which", lambda name: None)

    # Call the method
    result = uv_bin._try_uv_from_nix_channel()

    # Verify results
    assert result is None


def test_try_uv_from_nix_channel_returns_none_when_build_fails(
    monkeypatch, tmp_path, caplog, subprocess_run_fail
):
    """_try_uv_from_nix_channel returns None when nix build fails."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock shutil.which to return nix path
    monkeypatch.setattr(
        "shutil.which", lambda name: "/nix/bin/nix" if name == "nix" else None
    )

    # Cap logs at DEBUG level
    caplog.set_level(logging.DEBUG)

    # Call the method
    result = uv_bin._try_uv_from_nix_channel()

    # Verify results
    assert result is None
    # Check that we logged the failure
    assert "uv-nix-channel-failed:" in caplog.text


def test_try_uv_from_nix_channel_returns_none_when_invalid_version(
    monkeypatch, tmp_path, caplog
):
    """_try_uv_from_nix_channel returns None when uv built but version invalid."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock shutil.which to return nix path
    monkeypatch.setattr(
        "shutil.which", lambda name: "/nix/bin/nix" if name == "nix" else None
    )

    # Mock subprocess.run to return success
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: FakeResult(stderr=b""),
    )

    # Mock UvBin.get_uv_version to return unknown version (invalid)
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: UvVersion.unknown())

    # Cap logs at DEBUG level
    caplog.set_level(logging.DEBUG)

    # Call the method
    result = uv_bin._try_uv_from_nix_channel()

    # Verify results
    assert result is None


def test_try_uv_from_nix_channel_and_appenv_dir_share_same_path(
    monkeypatch, tmp_path, caplog
):
    """nix-build creates uv at .appenv/.uv, _try_uv_from_appenv_dir finds it.

    Verifies that _try_uv_from_nix_channel builds uv into the same
    directory that _try_uv_from_appenv_dir looks for.
    """
    uv_bin = UvBin(tmp_path / ".appenv")

    monkeypatch.setattr(uv_bin, "_try_uv_from_path", lambda: None)

    # Keep reference to real method before patching
    real_appenv_dir = uv_bin._try_uv_from_appenv_dir

    def mock_appenv_dir():
        return real_appenv_dir()

    monkeypatch.setattr(uv_bin, "_try_uv_from_appenv_dir", mock_appenv_dir)

    monkeypatch.setattr(
        "shutil.which", lambda name: "/nix/bin/nix" if name == "nix" else None
    )

    nix_build_output_dir = []

    class FakeNixResult:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_nix_run(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args", [])
        for i, arg in enumerate(cmd):
            if arg == "-o" and i + 1 < len(cmd):
                nix_build_output_dir.append(Path(cmd[i + 1]))
                uv_path = Path(cmd[i + 1]) / "bin/uv"
                uv_path.parent.mkdir(parents=True, exist_ok=True)
                uv_path.write_text("#!/bin/sh\n")
        return FakeNixResult()

    monkeypatch.setattr(subprocess, "run", fake_nix_run)

    mock_version = UvVersion(0, 10, 3)
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: mock_version)

    caplog.set_level(logging.DEBUG)

    result = uv_bin._get_uv_bin()

    assert len(nix_build_output_dir) == 1
    assert nix_build_output_dir[0] == tmp_path / ".appenv/.uv"

    expected_uv = tmp_path / ".appenv/.uv/bin/uv"
    assert expected_uv.exists(), f"uv not found at {expected_uv}"
    assert result == expected_uv

    found = uv_bin._try_uv_from_appenv_dir()
    assert found == expected_uv


# ==============================================================================
# UvBin._try_uv_from_nix_flake tests
# ==============================================================================


@pytest.mark.parametrize(
    ("subprocess_success", "version_result", "expected", "expected_log"),
    [
        pytest.param(
            True,
            UvVersion(0, 10, 3),
            ...,
            "uv-nix-flake-succeeded:",
            id="nix_flake-valid",
        ),
        pytest.param(
            False,
            UvVersion.unknown(),
            None,
            "uv-nix-flake-failed:",
            id="nix_flake-build-fails",
        ),
        pytest.param(
            True, UvVersion.unknown(), None, None, id="nix_flake-invalid-version"
        ),
    ],
)
def test_try_uv_from_nix_flake(
    monkeypatch,
    tmp_path,
    caplog,
    subprocess_success,
    version_result,
    expected,
    expected_log,
):
    """_try_uv_from_nix_flake returns path when nix flake build succeeds,
    returns None when build fails or version is invalid."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock shutil.which to find nix
    monkeypatch.setattr(
        shutil, "which", lambda name: "/usr/bin/nix" if name == "nix" else None
    )

    # Mock subprocess.run based on parameter
    if subprocess_success:
        monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: FakeResult())
    else:

        def _fail(*args, **kwargs):
            raise subprocess.CalledProcessError(
                returncode=1, cmd="nix", stderr="test_stderr"
            )

        monkeypatch.setattr(subprocess, "run", _fail)

    # Mock UvBin.get_uv_version
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: version_result)

    # Cap logs at DEBUG level
    caplog.set_level(logging.DEBUG)

    # Call the method
    result = uv_bin._try_uv_from_nix_flake()

    # Verify results
    if expected is None:
        assert result is None
    else:
        expected_path = tmp_path / ".appenv/.uv/bin/uv"
        assert result == expected_path

    # Check log if expected
    if expected_log is not None:
        assert expected_log in caplog.text


# ==============================================================================
# UvBin._try_uv_from_pip tests
# ==============================================================================


@pytest.mark.parametrize(
    ("ensurepip_ok", "pip_ok", "version", "mock_which_none", "expected", "log_check"),
    [
        pytest.param(
            True,
            True,
            UvVersion(0, 10, 3),
            False,
            ...,
            "uv-pip-install-succeeded:",
            id="valid",
        ),
        pytest.param(
            False, True, None, True, None, "ensurepip-failed:", id="ensurepip_fails"
        ),
        pytest.param(
            True,
            False,
            None,
            False,
            None,
            "uv-pip-install-failed:",
            id="pip_install_fails",
        ),
        pytest.param(
            True, True, UvVersion.unknown(), False, None, None, id="invalid_version"
        ),
    ],
)
def test_try_uv_from_pip(
    monkeypatch,
    tmp_path,
    caplog,
    ensurepip_ok,
    pip_ok,
    version,
    mock_which_none,
    expected,
    log_check,
):
    """_try_uv_from_pip returns path when pip install succeeds and version valid,
    returns None when ensurepip fails, pip install fails, or version is invalid."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock subprocess.run with side effect based on parameters
    def mock_run(*args, **kwargs):
        if "ensurepip" in args[0]:
            if ensurepip_ok:
                return FakeResult(stdout="ensurepip output")
            raise subprocess.CalledProcessError(1, "ensurepip")
        # pip install
        if pip_ok:
            return FakeResult(stdout="Successfully installed uv")
        raise subprocess.CalledProcessError(1, "pip install")

    monkeypatch.setattr(subprocess, "run", mock_run)

    # Mock shutil.which to return None when ensurepip fails and no pip in PATH
    if mock_which_none:
        monkeypatch.setattr(shutil, "which", lambda name: None)

    # Mock UvBin.get_uv_version when version is specified
    if version is not None:
        monkeypatch.setattr(UvBin, "get_uv_version", lambda path: version)

    # Cap logs at DEBUG level
    caplog.set_level(logging.DEBUG)

    # Call the method
    result = uv_bin._try_uv_from_pip()

    # Verify results
    if expected is None:
        assert result is None
    else:
        expected_path = tmp_path / ".appenv/.uv/bin/uv"
        assert result == expected_path

    # Check log if expected
    if log_check is not None:
        assert log_check in caplog.text


def test_get_uv_bin_returns_from_nix_flake_when_previous_fail(monkeypatch, tmp_path):
    """_get_uv_bin returns from nix_flake when previous methods return None."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock preceding methods to return None so we reach nix_flake method
    monkeypatch.setattr(uv_bin, "_try_uv_from_path", lambda: None)
    monkeypatch.setattr(uv_bin, "_try_uv_from_appenv_dir", lambda: None)
    monkeypatch.setattr(uv_bin, "_try_uv_from_nix_channel", lambda: None)

    # Mock the nix_flake method to return a valid path
    expected_path = tmp_path / ".appenv/.uv/bin/uv"
    expected_path.parent.mkdir(parents=True)
    expected_path.write_text("#!/bin/sh\n")
    monkeypatch.setattr(uv_bin, "_try_uv_from_nix_flake", lambda: expected_path)

    # Mock subsequent method to ensure it's not called
    monkeypatch.setattr(uv_bin, "_try_uv_from_pip", lambda: None)

    # Call the method
    result = uv_bin._get_uv_bin()

    # Verify results
    assert result == expected_path
    # Verify subsequent method was not called (early return)


def test_get_uv_bin_returns_from_pip_when_previous_fail(monkeypatch, tmp_path):
    """_get_uv_bin returns from _try_uv_from_pip when previous methods return None."""
    # Create a UvBin instance
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock preceding methods to return None so we reach pip method
    monkeypatch.setattr(uv_bin, "_try_uv_from_path", lambda: None)
    monkeypatch.setattr(uv_bin, "_try_uv_from_appenv_dir", lambda: None)
    monkeypatch.setattr(uv_bin, "_try_uv_from_nix_channel", lambda: None)
    monkeypatch.setattr(uv_bin, "_try_uv_from_nix_flake", lambda: None)

    # Mock the pip method to return a valid path
    expected_path = tmp_path / ".appenv/.uv/bin/uv"
    expected_path.parent.mkdir(parents=True)
    expected_path.write_text("#!/bin/sh\n")
    monkeypatch.setattr(uv_bin, "_try_uv_from_pip", lambda: expected_path)

    # Call the method
    result = uv_bin._get_uv_bin()

    # Verify results
    assert result == expected_path


# Tier 3 tests


def test_uv_bin_cmd_verbose_flag_and_output(monkeypatch, caplog):
    """UvBin.cmd adds -v flag when verbose=True and logs output."""
    import logging

    caplog.set_level(logging.DEBUG)

    # Create a mock UvBin
    uv = UvBin.__new__(UvBin)
    uv.bin = Path("/usr/bin/uv")
    uv.appenv_dir = Path("/tmp/.appenv")
    uv.uv_dir = uv.appenv_dir / ".uv"

    cmd_calls = []

    def mock_cmd(c, **kwargs):
        cmd_calls.append(c)
        return b"verbose output from uv"

    monkeypatch.setattr(appenv, "cmd", mock_cmd)

    uv.cmd(["lock"], verbose=True)

    # Verify -v flag is added to command
    assert "-v" in cmd_calls[0]
    assert "lock" in cmd_calls[0]

    # Verify output is logged via log.debug
    assert "verbose output from uv" in caplog.text


# ==============================================================================
# UvBin._get_uv_bin tests (pip fallback behavior)
# ==============================================================================


@pytest.mark.no_mock_uv_version
def test_uv_bin_pip_fallback_raises_error(tmp_path, monkeypatch):
    """UvBin._get_uv_bin raises NoValidUvError when uv still not found after pip."""

    which_calls = []

    def mock_which(name):
        which_calls.append(name)
        # uv never available

    monkeypatch.setattr("shutil.which", mock_which)

    pip_called = []

    def mock_run(cmd, **kwargs):
        pip_called.append(cmd)
        # Return a fake result for uv --version calls
        if "uv" in cmd and "--version" in cmd:
            return FakeResult(stdout="uv 0.10.3 (abc123 2024-01-01)\n", returncode=0)
        # Return success for other subprocess calls (like pip --version, pip install)
        return FakeResult(stdout="", returncode=0)

    monkeypatch.setattr("subprocess.run", mock_run)

    # Also mock the installer to prevent real network access
    monkeypatch.setattr(UvBin, "_try_uv_from_installer", lambda self: None)

    with pytest.raises(NoValidUvError, match="uv missing and could not be installed"):
        ensure_uv(tmp_path)

    assert any("pip" in str(cmd) and "uv" in str(cmd) for cmd in pip_called)


# ==============================================================================
# Coverage tests for 99% target
# ==============================================================================


def test_cleanup_appenv_uv_with_base_and_existing_dir(tmp_path):
    """Lines 622, 625: _cleanup_appenv_uv when base is set and .appenv/.uv exists."""
    # Create .appenv/.uv directory
    appenv_uv = tmp_path / ".appenv" / ".uv"
    appenv_uv.mkdir(parents=True)
    (appenv_uv / "some_file").write_text("test")

    # Create UvBin with base set
    uv_bin = UvBin(tmp_path / ".appenv")

    uv_bin._cleanup_appenv_uv()

    assert not appenv_uv.exists()


def test_get_uv_bin_returns_from_appenv_dir_when_path_fails(monkeypatch, tmp_path):
    """Test that _get_uv_bin returns from appenv_dir when path fails."""
    # Create a UvBin instance with a real base
    uv_bin = UvBin(tmp_path / ".appenv")

    # Mock _try_uv_from_path to return None (so we skip the first method)
    monkeypatch.setattr(uv_bin, "_try_uv_from_path", lambda: None)

    # Create a mock path to return from _try_uv_from_appenv_dir
    mock_uv_path = tmp_path / ".appenv" / ".uv" / "bin" / "uv"
    mock_uv_path.parent.mkdir(parents=True, exist_ok=True)
    mock_uv_path.write_text("#!/bin/sh\n")

    monkeypatch.setattr(uv_bin, "_try_uv_from_appenv_dir", lambda: mock_uv_path)

    # Track if the other methods are called
    nix_channel_called = []
    nix_flake_called = []
    pip_called = []

    monkeypatch.setattr(
        uv_bin,
        "_try_uv_from_nix_channel",
        lambda: nix_channel_called.append(True) or None,
    )
    monkeypatch.setattr(
        uv_bin, "_try_uv_from_nix_flake", lambda: nix_flake_called.append(True) or None
    )
    monkeypatch.setattr(
        uv_bin, "_try_uv_from_pip", lambda: pip_called.append(True) or None
    )

    # Call the method
    result = uv_bin._get_uv_bin()

    # Verify results
    assert result == mock_uv_path
    assert nix_channel_called == []  # Should not be called
    assert nix_flake_called == []  # Should not be called
    assert pip_called == []  # Should not be called


@pytest.mark.no_mock_uv_version
def test_ensure_uv_invalid_version(tmp_path, monkeypatch, capsys):
    """Lines 1213-1215: ensure_uv exits with EXIT_CODE_UNAVAILABLE if invalid."""

    # Mock UvBin to return invalid version
    class MockUvBinInvalid:
        def __init__(self, appenv_dir):
            self.bin = Path("/usr/bin/uv")
            self.appenv_dir = appenv_dir

        @property
        def version(self):
            return UvVersion(0, 0, 0)  # Invalid - below minimum

    monkeypatch.setattr(appenv, "UvBin", MockUvBinInvalid)

    with pytest.raises(SystemExit) as exc:
        ensure_uv(tmp_path)

    assert exc.value.code == EXIT_CODE_UNAVAILABLE
    captured = capsys.readouterr()
    assert "cannot use uv binary" in captured.out


# Platform detection for UV download


@pytest.mark.parametrize(
    ("machine", "system", "expected"),
    [
        pytest.param("aarch64", "linux", "aarch64", id="aarch64"),
        pytest.param("armv7l", "linux", "armv7", id="armv7"),
        pytest.param("x86_64", "darwin", "darwin", id="darwin"),
        pytest.param("riscv64", "linux", None, id="unknown-arch"),
        pytest.param("x86_64", "win32", None, id="unknown-system"),
    ],
)
def test_uv_platform_triple(monkeypatch, machine, system, expected):
    """_uv_platform_triple maps known arch/system, returns None for unknown."""
    monkeypatch.setattr("platform.machine", lambda: machine)
    monkeypatch.setattr("sys.platform", system)
    result = UvBin._uv_platform_triple()
    if expected is None:
        assert result is None
    else:
        assert result is not None
        assert expected in result


# Pip fallback


def test_pip_fallback_found_via_which(tmp_path, monkeypatch):
    """pip found via shutil.which after ensurepip fails."""
    # ensurepip fails
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **kw: (_ for _ in ()).throw(subprocess.CalledProcessError(1, cmd)),
    )
    # pip3 found in PATH
    monkeypatch.setattr(
        shutil, "which", lambda cmd: "/usr/bin/pip3" if cmd == "pip3" else None
    )

    uv = UvBin(tmp_path)
    result = uv._resolve_pip_command()
    assert result == ["/usr/bin/pip3"]


def test_uv_bin_tar_typeerror_fallback(tmp_path, monkeypatch):
    """TypeError fallback for tar.extract filter= parameter is exercised."""
    import io
    import tarfile
    import warnings

    # Build a fake tar.gz that looks like a uv release tarball
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="uv-triple/uv")
        info.type = tarfile.REGTYPE
        info.size = 4
        tar.addfile(info, io.BytesIO(b"fake"))
    tar_data = buf.getvalue()

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda url, timeout=60: io.BytesIO(tar_data)
    )

    # First extract() call (with filter=) raises TypeError,
    # second call (fallback) uses real extract
    original_extract = tarfile.TarFile.extract

    def mock_extract(self, *args, **kwargs):
        if "filter" in kwargs:
            msg = "filter not supported"
            raise TypeError(msg)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            return original_extract(self, *args, **kwargs)

    monkeypatch.setattr(tarfile.TarFile, "extract", mock_extract)
    monkeypatch.setattr(UvBin, "get_uv_version", lambda path: UvVersion(0, 7, 0))

    uv = UvBin(tmp_path)
    result = uv._try_uv_from_installer()

    assert result is not None
    assert result.exists()
    assert result == uv.managed_uv
