#!/usr/bin/env python3
"""Pre-commit hook enforcing .pyi stub ↔ runtime .py consistency via mypy.stubtest.

Discovers every ``.pyi`` under ``src/`` and ``tests/``, reduces them to their
top-level module names (e.g. ``appenv``, ``tests``), and runs a single
``mypy.stubtest`` call. stubtest traverses packages transitively, so passing
``tests`` covers ``tests.test_main``, ``tests.e2e.test_cli``, etc. — no need
to enumerate every leaf.

Uses the project mypy config (``pyproject.toml`` -> ``[tool.mypy]`` provides
``mypy_path`` and the ``pytest_patterns.*`` missing-import override). Exits
non-zero on any mismatch so drifted stubs cannot be committed. Stdlib only.
"""

import subprocess
import sys
from pathlib import Path

# Repo root = parent of this file's directory (tools/).
REPO_ROOT = Path(__file__).resolve().parent.parent
MYPY_CONFIG = REPO_ROOT / "pyproject.toml"
ALLOWLIST = REPO_ROOT / "tools" / "stubtest-allowlist"
STUB_ROOTS = ("src", "tests")


def _module_name(stub: Path) -> str:
    """Map a ``.pyi`` path to its dotted module name.

    ``src/`` is on ``mypy_path`` (see ``[tool.mypy]`` in pyproject.toml), so
    its prefix is stripped. A package's ``__init__.pyi`` maps to the package
    itself, not a submodule named ``__init__``.
    """
    rel = stub.relative_to(REPO_ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def discover_top_level_modules() -> list[str]:
    """Return the minimal set of top-level module names covering all stubs.

    stubtest traverses packages transitively, so ``tests`` alone covers
    ``tests.test_main``, ``tests.e2e``, etc. We only need the first component
    of each module path.
    """
    stubs: list[Path] = []
    for root in STUB_ROOTS:
        stubs.extend((REPO_ROOT / root).rglob("*.pyi"))
    top_level: set[str] = set()
    for stub in sorted(stubs):
        module = _module_name(stub)
        top_level.add(module.split(".")[0])
    return sorted(top_level)


def main() -> int:
    modules = discover_top_level_modules()
    if not modules:
        print(
            "check_stub_sync: no .pyi stubs found under src/ or tests/",
            file=sys.stderr,
        )
        return 1

    cmd = [
        sys.executable,
        "-m",
        "mypy.stubtest",
        *modules,
        "--mypy-config-file",
        str(MYPY_CONFIG),
    ]
    if ALLOWLIST.exists():
        cmd.extend(["--allowlist", str(ALLOWLIST), "--ignore-unused-allowlist"])

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    output = (proc.stdout + proc.stderr).strip()

    if proc.returncode != 0:
        print(output, file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
