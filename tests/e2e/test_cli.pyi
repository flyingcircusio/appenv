from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture

@pytest.mark.slow(reason=...)
def test_init_cli(
    tmp_path: Path, setup_isolated_appenv: Callable[[Path], Path]
) -> None: ...
def test_migrate_cli(
    tmp_path: Path, setup_isolated_appenv: Callable[[Path], Path]
) -> None: ...
@pytest.mark.slow(reason="Installs httpie package, takes ~10 seconds")
def test_bootstrap_flow_like_readme(
    tmp_path: Path,
    capsys: CaptureFixture[str],
    setup_isolated_appenv: Callable[[Path], Path],
) -> None: ...
