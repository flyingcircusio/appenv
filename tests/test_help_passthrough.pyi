from collections.abc import Callable
from pathlib import Path

from pytest import CaptureFixture, MonkeyPatch

from appenv import AppEnv

def test_help_routes_to_delegate(
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    capsys: CaptureFixture[str],
    no_ensure_python: None,
    mock_logdir: Path,
    delegate_method: str,
    remaining_args: list[str],
    expected_remaining: list[str],
    usage_not_in: str,
) -> None: ...
def test_init_help_keeps_appenv_init_help(
    app_env: Callable[..., AppEnv],
    capsys: CaptureFixture[str],
    no_ensure_python: None,
    mock_logdir: Path,
) -> None: ...
