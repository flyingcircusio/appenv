from collections.abc import Callable
from pathlib import Path

import pytest

def _base_env(**overrides: str) -> dict[str, str]: ...
@pytest.fixture
def setup_isolated_appenv() -> Callable[[Path], Path]: ...
@pytest.fixture
def setup_project_with_lockfile() -> Callable[[Path, str], Path]: ...
@pytest.fixture
def setup_prepared_project(
    setup_project_with_lockfile: Callable[[Path, str], Path],
) -> Callable[[Path, str], Path]: ...
