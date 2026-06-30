from collections.abc import Callable
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch
from pytest_patterns.plugin import PatternsLib

from appenv import AppEnv

def test_migrate_uses_python_preference_from_requirements(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_existing_symlinks(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_empty_dependencies(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_uses_directory_name(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_already_exists(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_no_requirements_txt(
    workdir: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_full_flow_pattern(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
def test_migrate_editable_missing_package_warns(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_editable_mixed_valid_and_invalid(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_editable_unsupported_warns(
    requirements: str,
    warning_pattern: str,
    regular_deps: list[str],
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
) -> None: ...
def test_migrate_existing_pyproject_no_project_section(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    patterns: PatternsLib,
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
@pytest.mark.parametrize(
    (
        "script_content",
        "expects_update",
        "old_version_in_output",
        "expects_unknown",
        "expects_unchanged",
    ),
    [
        pytest.param(
            '#!/usr/bin/env python3\n__version__ = "0.0.1"\n',
            True,
            "0.0.1",
            False,
            False,
            id="version-mismatch",
        ),
        pytest.param(
            '#!/usr/bin/env python3\n__version__ = "x.y.z"\n',
            False,
            None,
            False,
            True,
            id="same-version",
        ),
        pytest.param(
            '#!/usr/bin/env python3\nprint("old")\n',
            True,
            None,
            True,
            False,
            id="without-version",
        ),
    ],
)
def test_migrate_appenv_script(
    script_content: str,
    expects_update: bool,
    old_version_in_output: str | None,
    expects_unknown: bool,
    expects_unchanged: bool,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
def test_migrate_with_path_argument(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
def test_migrate_rejects_invalid_pep508_requirement(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
@pytest.mark.parametrize(
    "specifier",
    [
        pytest.param("requests", id="plain-name"),
        pytest.param("requests>=2.0", id="version-specifier"),
        pytest.param("requests[security]==2.31.0", id="extras-and-version"),
        pytest.param('requests>=2.0,<3.0; python_version>"3.10"', id="marker"),
    ],
)
def test_migrate_accepts_valid_pep508_specifiers(
    specifier: str,
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    app_env: Callable[..., AppEnv],
    mock_uv_lock: None,
) -> None: ...
@pytest.mark.parametrize(
    ("dep", "expected"),
    [
        pytest.param("requests @ https://example.com/r.tar.gz", True, id="name-at-url"),
        pytest.param("git+https://github.com/u/r.git", True, id="git-plus-url"),
        pytest.param("hg+https://example.com/repo", True, id="hg-plus-url"),
        pytest.param("https://example.com/package.tar.gz", True, id="https-url"),
        pytest.param("file:///local/path", True, id="file-url"),
        pytest.param("requests", True, id="plain-name"),
        pytest.param("requests[security]>=2.0", True, id="extras-and-version"),
        pytest.param("!!!invalid!!!", False, id="invalid-chars"),
        pytest.param("@broken", False, id="leading-at"),
        pytest.param("", False, id="empty"),
        pytest.param("   ", False, id="whitespace-only"),
    ],
)
def test_is_likely_valid_pep508_dep(dep: str, expected: bool) -> None: ...
