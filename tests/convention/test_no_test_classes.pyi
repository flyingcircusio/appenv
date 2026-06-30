from pathlib import Path

import pytest

TESTS_DIR: Path

@pytest.mark.convention
def test_no_test_classes_in_test_files() -> None: ...
