from collections.abc import Callable
from pathlib import Path

import pytest

@pytest.mark.slow(reason="Creates real venv with uv, takes ~10 seconds")
def test_subprocess_main_flow(
    tmp_path: Path, setup_project_with_lockfile: Callable[[Path, str], Path]
) -> None: ...
