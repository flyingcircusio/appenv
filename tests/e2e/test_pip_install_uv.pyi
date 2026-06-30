from pathlib import Path

from pytest import MonkeyPatch

def test_try_uv_from_pip_integration(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None: ...
