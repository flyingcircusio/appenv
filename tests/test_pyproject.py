# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for Pyproject, ensure_pyproject, ensure_uv, and related utilities."""

import subprocess

import pytest

import appenv


@pytest.mark.no_mock_uv_version
def test_ensure_uv_returns_uvbin_from_path(monkeypatch, tmp_path):
    """ensure_uv returns UvBin with uv from PATH if available."""
    monkeypatch.setattr(
        "shutil.which", lambda name: "/usr/bin/uv" if name == "uv" else None
    )

    # Mock subprocess.run to return version
    def mock_run(cmd, **kwargs):
        text_mode = kwargs.get("text", False)
        stdout = "uv 0.5.0\n" if text_mode else b"uv 0.5.0\n"
        return subprocess.CompletedProcess(cmd, 0, stdout, b"")

    monkeypatch.setattr(subprocess, "run", mock_run)

    result = appenv.ensure_uv(tmp_path)
    assert isinstance(result, appenv.UvBin)
    assert str(result.bin) == "/usr/bin/uv"


def test_pyproject_requires_python_edge_cases(tmp_path):
    """Pyproject.requires_python handles various regex formats."""
    base = tmp_path

    # Non-existent file returns (None, None)
    pyproject = appenv.Pyproject(base)
    assert pyproject.requires_python == (None, None)

    pyproject_path = base / "pyproject.toml"

    # Format: >=3.13 (no space around operators)
    pyproject_path.write_text('[project]\nname = "test"\nrequires-python = ">=3.13"\n')
    assert appenv.Pyproject(base).requires_python == ("3.13", None)

    # Format: = "3.14" (with space after = and before value)
    pyproject_path.write_text('[project]\nname = "test"\nrequires-python = ">=3.14"\n')
    assert appenv.Pyproject(base).requires_python == ("3.14", None)

    # Format: >3.10 (greater than, not >=) - regex handles >=? so just > matches
    pyproject_path.write_text('[project]\nname = "test"\nrequires-python = ">3.10"\n')
    assert appenv.Pyproject(base).requires_python == ("3.10", None)

    # Format with extra whitespace around = (regex allows \s*)
    pyproject_path.write_text('[project]\nname = "test"\nrequires-python=">=3.11"\n')
    assert appenv.Pyproject(base).requires_python == ("3.11", None)

    # No match returns (None, None)
    pyproject_path.write_text('[project]\nname = "test"\n')
    assert appenv.Pyproject(base).requires_python == (None, None)


def test_pyproject_requires_python_with_upper_bound(tmp_path):
    """Pyproject.requires_python handles upper bounds like >=3.11,<3.15."""
    base = tmp_path
    pyproject_path = base / "pyproject.toml"

    # Format: >=3.11,<3.15
    pyproject_path.write_text(
        '[project]\nname = "test"\nrequires-python = ">=3.11,<3.15"\n'
    )
    assert appenv.Pyproject(base).requires_python == ("3.11", "3.15")

    # Format: >=3.11.0,<3.15.0 (with patch version)
    pyproject_path.write_text(
        '[project]\nname = "test"\nrequires-python = ">=3.11.0,<3.15.0"\n'
    )
    assert appenv.Pyproject(base).requires_python == ("3.11", "3.15")

    # Format: >=3.10,<=3.14 (inclusive upper bound)
    pyproject_path.write_text(
        '[project]\nname = "test"\nrequires-python = ">=3.10,<=3.14"\n'
    )
    assert appenv.Pyproject(base).requires_python == ("3.10", "3.14")

    # Format with spaces: >= 3.11, < 3.15
    pyproject_path.write_text(
        '[project]\nname = "test"\nrequires-python = ">= 3.11, < 3.15"\n'
    )
    assert appenv.Pyproject(base).requires_python == ("3.11", "3.15")


def test_pyproject_builder_merges_with_existing_content(tmp_path):
    """Line 282: PyprojectBuilder merges with existing pyproject content."""
    base = tmp_path
    pyproject_path = base / "pyproject.toml"

    # Create existing pyproject content (e.g., tool settings)
    pyproject_path.write_text("[tool.ruff]\nline-length = 100\n")

    # Create Pyproject instance and add project section
    pyproject = appenv.Pyproject(base)
    pyproject.with_project_section(
        project_name="myproject",
        description="A test project",
        dependencies=["requests"],
        requires_python=">=3.10",
    )

    # Verify content includes both original and new section
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content
    assert "line-length = 100" in content
    assert "[project]" in content
    assert 'name = "myproject"' in content
    assert "requests" in content


def test_ensure_pyproject_no_project_section_no_requirements(
    tmp_path, monkeypatch, capsys
):
    """Lines 1204, 1209-1211: ensure_pyproject exits when no [project].

    Also no requirements.txt.
    """
    base = tmp_path

    # Create pyproject.toml without [project] section
    (base / "pyproject.toml").write_text("[tool.ruff]\nline-length = 100\n")

    with pytest.raises(SystemExit) as exc_info:
        appenv.ensure_pyproject(base)

    assert exc_info.value.code == appenv.EXIT_CODE_NOINPUT
    captured = capsys.readouterr()
    assert "has no [project] section" in captured.out
    assert "Run ./appenv init" in captured.out


def test_ensure_pyproject_no_file_with_requirements(tmp_path, monkeypatch, capsys):
    """Lines 1209-1211: ensure_pyproject exits with DATAERR.

    When requirements.txt exists.
    """
    base = tmp_path

    # Create requirements.txt (no pyproject.toml)
    (base / "requirements.txt").write_text("requests\n")

    with pytest.raises(SystemExit) as exc_info:
        appenv.ensure_pyproject(base)

    assert exc_info.value.code == appenv.EXIT_CODE_DATAERR
    captured = capsys.readouterr()
    assert "No pyproject.toml found" in captured.out
    assert "Legacy requirements.txt found" in captured.out
    assert "Run: ./appenv migrate" in captured.out


def test_print_migration_info_skips_minimum_version_with_single_python(
    tmp_path, capsys
):
    """Line 242->246: Skips 'Using minimum version' print when only 1 Python version."""
    base = tmp_path
    requirements_path = base / "requirements.txt"
    requirements_path.write_text(
        "# appenv-python-preference: 3.12\nrequests\n",
    )

    pyproject = appenv.Pyproject(base)
    req_info = pyproject.requirements_txt_info

    # Should have single python version
    assert len(req_info.python_versions) == 1
    assert req_info.python_versions == ["3.12"]

    # Call print_migration_info
    pyproject.print_migration_info()

    captured = capsys.readouterr()
    # "Using minimum version" should NOT be printed with single version
    assert "Using minimum version" not in captured.out


def test_pyproject_python_preference_empty_after_filter(tmp_path, capsys):
    """Line 257->253: Empty preferences list falls through to default."""
    base = tmp_path
    # Create requirements.txt with empty preference comment
    requirements_path = base / "requirements.txt"
    requirements_path.write_text(
        "# appenv-python-preference:   \nrequests\n",
    )

    pyproject = appenv.Pyproject(base)
    req_info = pyproject.requirements_txt_info

    # Should return default list when comment has only whitespace
    assert req_info.python_versions == ["3.10", "3.11", "3.12", "3.13", "3.14"]

    # Call print_migration_info and verify output
    pyproject.print_migration_info()

    captured = capsys.readouterr()
    # With default 5 versions, "Using minimum version" SHOULD be printed
    assert "Using minimum version" in captured.out
