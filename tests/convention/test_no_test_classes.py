# SPDX-FileCopyrightText: 2020 Flying Circus
"""Convention: no test classes — only module-level test functions.

pytest's class-based grouping is an xUnit holdover. It encourages shared
mutable state via ``self.``, hides fixture parameter lists behind
self-reference, complicates ``@pytest.mark.parametrize``, and obscures
the test-to-fixture contract (a flat ``def test_foo(monkeypatch, tmp_path)``
signature is self-documenting; a method is not).

This module-level convention enforces the flat, functional style already
used by the majority of this suite: every test is a top-level
``def test_...`` function. ``conftest.py`` is excluded (helper classes
like ``MockUvBin`` live there).

Marked ``convention`` — these checks are language-version-independent and
run only once (in the ``cov`` environment) to avoid redundant execution
across all Python versions.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent


def _find_violators(tests_dir=TESTS_DIR):
    """Walk test files and find class definitions."""
    for py_file in sorted(tests_dir.rglob("test_*.py")):
        if "conftest" in py_file.name:
            continue
        tree = ast.parse(py_file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                yield py_file, node


def _format_violators(violators):
    """Format violators for assertion message."""
    lines = []
    for path, node in violators:
        lines.append(f"  {path}:{node.lineno}: class {node.name}")
    return "\n".join(lines)


@pytest.mark.convention
def test_no_test_classes_in_test_files():
    """No ``class Test...`` declarations in any ``tests/**/test_*.py``.

    Class-based test grouping is forbidden in favour of module-level test
    functions. Helper classes (no ``Test`` prefix) remain allowed, and
    ``conftest.py`` is excluded entirely so MockUvBin-style helpers survive.
    """
    violators = list(_find_violators(TESTS_DIR))
    assert not violators, _format_violators(violators)
