from collections.abc import Callable

from pytest import MonkeyPatch

from appenv import AppEnv

def test_build_env_returns_dict_instance(app_env: Callable[..., AppEnv]) -> None: ...
def test_build_env_preserves_path_and_home(
    app_env: Callable[..., AppEnv], monkeypatch: MonkeyPatch
) -> None: ...
def test_build_env_drops_pythonpath(
    app_env: Callable[..., AppEnv], monkeypatch: MonkeyPatch
) -> None: ...
def test_build_env_applies_overlays(app_env: Callable[..., AppEnv]) -> None: ...
def test_build_env_overlays_override_os_environ(
    app_env: Callable[..., AppEnv], monkeypatch: MonkeyPatch
) -> None: ...
def test_build_env_does_not_mutate_os_environ(
    app_env: Callable[..., AppEnv], monkeypatch: MonkeyPatch
) -> None: ...
