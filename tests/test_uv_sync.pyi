from collections.abc import Callable
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch

from .conftest import MockUvBin

def test_uv_sync_with_extras(
    tmp_path: Path, monkeypatch: MonkeyPatch, make_mock_uv: Callable[..., MockUvBin]
) -> None: ...
def test_uv_sync_stale_lockfile_exits(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    make_mock_uv: Callable[..., MockUvBin],
    capsys: CaptureFixture[str],
) -> None: ...
def test_uv_sync_valid_lockfile_proceeds(
    tmp_path: Path, monkeypatch: MonkeyPatch, make_mock_uv: Callable[..., MockUvBin]
) -> None: ...
