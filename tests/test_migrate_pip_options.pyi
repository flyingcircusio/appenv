import re
from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

import pytest
from pytest import CaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnv

class MigrationOutput(NamedTuple):
    pyproject: str
    stdout: str
    stderr: str

_DEPENDENCIES_BLOCK: re.Pattern[str]
_INDEX_BLOCK: re.Pattern[str]

def _extract_dependencies(pyproject_text: str) -> list[str]: ...
def _extract_uv_indexes(pyproject_text: str) -> list[dict[str, str]]: ...
def _index_env_token(index_name: str) -> str: ...
@pytest.fixture
def migrate_reqs(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> Callable[[str], MigrationOutput]: ...
def test_migrate_plain_dependencies_unchanged(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_parse_requirements_separates_pip_options(tmp_path: Path) -> None: ...
def test_migrate_separates_extra_index_url_from_dependencies(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_converts_index_url_to_uv_index_entry(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_assigns_distinct_names_to_multiple_indexes(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_strips_index_credentials_and_warns_env_vars(
    migrate_reqs: Callable[[str], MigrationOutput], patterns: PatternsLib
) -> None: ...
def test_migrate_skips_credential_warning_for_public_index(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_drops_unsupported_pip_option(
    requirements_text: str,
    expected_deps: list[str],
    skipped_option: str,
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_warns_lists_all_skipped_pip_options(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_gitlab_private_registry_end_to_end(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_writes_valid_toml_with_pip_options(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_assigns_numeric_suffix_when_index_hosts_collide(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_dedups_repeated_identical_index_url(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_index_url_without_value_creates_no_index(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_index_url_inline_equals_form_creates_entry(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_skips_unknown_option_followed_by_another_option(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
def test_migrate_skips_unknown_option_with_inline_value(
    migrate_reqs: Callable[[str], MigrationOutput],
) -> None: ...
