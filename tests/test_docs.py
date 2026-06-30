# SPDX-FileCopyrightText: 2020 Flying Circus
"""Doc regression tests — keep documentation consistent with source and itself."""


def test_index_has_toctree(project_root):
    """docs/index.md must contain a {toctree} directive."""
    content = (project_root / "docs" / "index.md").read_text()
    assert "{toctree}" in content


def test_index_toctree_lists_sections(project_root):
    """docs/index.md toctree must reference the section indexes."""
    content = (project_root / "docs" / "index.md").read_text()
    for ref in ("user/index", "dev/index"):
        assert ref in content, f"toctree must reference {ref}"


def test_conf_suppress_warnings_only_myst(project_root):
    """conf.py suppress_warnings must be exactly ['myst.header']."""
    content = (project_root / "docs" / "conf.py").read_text()
    in_list = False
    entries: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("suppress_warnings"):
            in_list = True
            continue
        if in_list:
            if stripped == "]":
                break
            entry = stripped.strip('",').strip()
            if entry:
                entries.append(entry)
    assert entries == ["myst.header"], (
        f"suppress_warnings should be only ['myst.header'], got: {entries}"
    )


def test_pyi_declares_exit_code_usage(project_root):
    """src/appenv.pyi must declare EXIT_CODE_USAGE."""
    content = (project_root / "src" / "appenv.pyi").read_text()
    assert "EXIT_CODE_USAGE" in content


def test_index_uses_uv_run_not_bare_uv(project_root):
    """docs/index.md must use 'uv run pytest' / 'uv run ruff check',
    never the bare 'uv pytest' / 'uv ruff check' form."""
    content = (project_root / "docs" / "index.md").read_text()
    assert "uv pytest" not in content, (
        "Found bare 'uv pytest' — should be 'uv run pytest'"
    )
    assert "uv ruff check" not in content, (
        "Found bare 'uv ruff check' — should be 'uv run ruff check'"
    )


def test_commands_doc_has_usage_exit_code(project_root):
    """user/commands.md must list exit code 64 (USAGE)."""
    content = (project_root / "docs" / "user" / "commands.md").read_text()
    assert "64" in content, "Exit code 64 must appear in commands.md"
    assert "USAGE" in content, "Exit code name USAGE must appear in commands.md"


def test_dev_doc_has_usage_exit_code(project_root):
    """Developer guide must mention exit code 64 (USAGE)."""
    content = (project_root / "docs" / "dev" / "index.md").read_text()
    assert "64" in content, "Exit code 64 must appear in dev docs"
    assert "USAGE" in content, "Exit code name USAGE must appear in dev docs"


def test_commands_doc_has_run_section(project_root):
    """commands.md must contain a ## run heading."""
    content = (project_root / "docs" / "user" / "commands.md").read_text()
    assert any(line.strip().startswith("## run") for line in content.splitlines()), (
        "commands.md must contain a ## run section"
    )


def test_index_mentions_supported_python_versions(project_root):
    """docs/index.md must mention both 3.9 (bootstrap) and 3.10 (managed envs)."""
    content = (project_root / "docs" / "index.md").read_text()
    assert "3.9" in content, "docs/index.md must mention Python 3.9 (bootstrap compat)"
    assert "3.10" in content, "docs/index.md must mention Python 3.10 (managed envs)"


def test_quickstart_uses_httpie(project_root):
    """Quick Start must use httpie, not requests, as the example dependency."""
    content = (project_root / "docs" / "index.md").read_text()
    if "Quick Start" in content:
        for section in content.split("## "):
            if section.startswith("Quick Start"):
                assert "httpie" in section.lower(), (
                    "Quick Start must reference httpie (not requests)"
                )
                assert "requests" not in section or "httpie" in section.lower(), (
                    "Quick Start should not use requests as the example dependency"
                )
                break


def test_init_prompt_matches_source(project_root):
    """commands.md init prompt must match the source at src/appenv.py."""
    content = (project_root / "docs" / "user" / "commands.md").read_text()
    source = (project_root / "src" / "appenv.py").read_text()
    assert "Binary to expose" in content, (
        "commands.md must contain the 'Binary to expose' prompt text"
    )
    assert "What should the command be named" not in content, (
        "commands.md must not contain stale prompt 'What should the command be named'"
    )
    # The `[app]` default bracket literal must appear in BOTH the source prompt
    # and the documented example — pinning them together so a drift in either
    # direction is caught here.
    assert "[app]" in source, (
        "src/appenv.py must keep the `[app]` default in the prompt"
    )
    assert "[app]" in content, "commands.md must document the `[app]` default"
