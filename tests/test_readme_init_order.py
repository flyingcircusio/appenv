# SPDX-FileCopyrightText: 2020 Flying Circus
"""README regression test for the init walkthrough answer-hint order."""

_DEPENDENCY_HINT = "httpie as dependency"
_BINARY_HINT = "http as binary"
_BLOCK_MARKER = "appenv init is interactive"


def test_readme_init_answer_hints_in_prompt_order(project_root):
    """Every README init hint block lists the dependency before the binary.

    The interactive init wizard asks for dependencies first, then the binary
    (src/appenv.py::_resolve_init_params_interactive_new, documented in
    docs/user/commands.md). The README walkthrough answer hints must follow the
    same order so a new user mentally prepares the answers in the right
    sequence.
    """
    lines = (project_root / "README.md").read_text().splitlines()
    starts = [i for i, line in enumerate(lines) if _BLOCK_MARKER in line]
    assert starts, "README must contain at least one init answer-hint block"

    for start in starts:
        window = lines[start : start + 8]
        dependency = [i for i, line in enumerate(window) if _DEPENDENCY_HINT in line]
        binary = [i for i, line in enumerate(window) if _BINARY_HINT in line]
        assert dependency and binary, (
            f"init block at README line {start + 1} must contain both "
            f"{_DEPENDENCY_HINT!r} and {_BINARY_HINT!r} answer hints"
        )
        assert dependency[0] < binary[0], (
            f"init block at README line {start + 1}: {_DEPENDENCY_HINT!r} must "
            f"precede {_BINARY_HINT!r} to match the interactive prompt "
            f"order (the wizard asks for dependencies before the binary)"
        )
