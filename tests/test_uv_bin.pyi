from pathlib import Path

import pytest
from pytest import CaptureFixture, LogCaptureFixture, MonkeyPatch

class FakeResult:
    returncode: int
    stdout: str
    stderr: str
    def __init__(
        self, returncode: int = ..., stdout: str = ..., stderr: str = ...
    ) -> None: ...

def test_uv_bin_cmd_raises_when_uv_not_found(monkeypatch: MonkeyPatch) -> None: ...
def test_try_uv_from_path_returns_path_when_valid(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None: ...
def test_try_uv_from_path_returns_none_when_invalid_version(
    monkeypatch: MonkeyPatch,
) -> None: ...
def test_try_uv_from_path_returns_none_when_not_in_path(
    monkeypatch: MonkeyPatch,
) -> None: ...
@pytest.mark.no_mock_uv_version
def test_uv_bin_get_uv_version(
    monkeypatch: MonkeyPatch, run_result: object, expected: object
) -> None: ...
def test_try_uv_from_appenv_dir(
    monkeypatch: MonkeyPatch, tmp_path: Path, version_result: object, expected: object
) -> None: ...
def test_try_uv_from_appenv_dir_returns_none_when_not_exists(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None: ...
@pytest.mark.parametrize(
    ("uv_local_preexists", "expected_action_log"),
    [
        pytest.param(True, "Updating", id="updates-existing"),
        pytest.param(False, "Creating", id="creates-new"),
    ],
)
def test_try_uv_from_nix_channel_returns_path(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    caplog: LogCaptureFixture,
    uv_local_preexists: bool,
    expected_action_log: str,
) -> None: ...
def test_try_uv_from_nix_channel_returns_none_when_nix_not_found(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None: ...
def test_try_uv_from_nix_channel_returns_none_when_build_fails(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    caplog: LogCaptureFixture,
    subprocess_run_fail: None,
) -> None: ...
def test_try_uv_from_nix_channel_returns_none_when_invalid_version(
    monkeypatch: MonkeyPatch, tmp_path: Path, caplog: LogCaptureFixture
) -> None: ...
def test_try_uv_from_nix_channel_and_appenv_dir_share_same_path(
    monkeypatch: MonkeyPatch, tmp_path: Path, caplog: LogCaptureFixture
) -> None: ...
def test_try_uv_from_nix_flake(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    caplog: LogCaptureFixture,
    subprocess_success: bool,
    version_result: object,
    expected: object,
    expected_log: str | None,
) -> None: ...
def test_try_uv_from_pip(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    caplog: LogCaptureFixture,
    ensurepip_ok: bool,
    pip_ok: bool,
    version: object,
    mock_which_none: bool,
    expected: object,
    log_check: str | None,
) -> None: ...
def test_get_uv_bin_returns_from_nix_flake_when_previous_fail(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None: ...
def test_get_uv_bin_returns_from_pip_when_previous_fail(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None: ...
def test_uv_bin_cmd_verbose_flag_and_output(
    monkeypatch: MonkeyPatch, caplog: LogCaptureFixture
) -> None: ...
@pytest.mark.no_mock_uv_version
def test_uv_bin_pip_fallback_raises_error(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_cleanup_appenv_uv_with_base_and_existing_dir(tmp_path: Path) -> None: ...
def test_get_uv_bin_returns_from_appenv_dir_when_path_fails(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None: ...
@pytest.mark.no_mock_uv_version
def test_ensure_uv_invalid_version(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None: ...
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
def test_uv_platform_triple(
    monkeypatch: MonkeyPatch, machine: str, system: str, expected: str | None
) -> None: ...
def test_pip_fallback_found_via_which(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
def test_uv_bin_tar_typeerror_fallback(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
