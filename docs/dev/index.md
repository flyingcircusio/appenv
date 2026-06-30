# Developer Guide

How appenv works internally and how to contribute.

For usage instructions, see the [User Guide](../user/index.md).

## Development Setup

All CI checks (lint, format, type-check, test) run via:

```console
tox
```

Clone the repository and install default plus `dev` dependencies:

```console
git clone https://github.com/flyingcircusio/appenv
cd appenv
uv sync
```

Run selected tests:

```console
uv run pytest -svx -k test_prepare
```

## Architecture

How appenv's components fit together and why.

### Design Philosophy

appenv is a single-file Python CLI that pins packages to exact versions and exposes their binaries via symlinks, using [uv](https://docs.astral.sh/uv/) for environment management. The single-file constraint is deliberate: appenv gets copied into project repositories as a self-contained bootstrap script with zero runtime dependencies. Commit it alongside `pyproject.toml` and `uv.lock`, and every checkout — local or on a remote deployment target — gets the same tools at the same versions by running `./http` or `./batou`.

This shapes every architectural decision:

- **Zero system modification**: appenv never installs anything outside the project directory. All state lives in `.appenv/` — venv, cached uv binary, logs. No system packages, no global bin directories, no PATH modifications. Drop the script, remove `.appenv/`, and the system is unchanged.
- **Symlink dispatch**: Multiple symlinks can coexist to expose different binaries from the same venv. The script chooses its mode based on its own filename.
- **Type hints in stubs only**: Implementation lives in `appenv.py` with minimal typing. Complete type annotations (public and private methods) live in `appenv.pyi`. Any signature change must update both files. See [](#type-annotations) for the full policy.
- **Guard-then-act pattern**: Preconditions validated upfront — available Python, existing config, current lockfile — each exits with a specific code on failure before the main logic runs.

### Logging

appenv logs to `.appenv/logs/<command_name>.log` (daily rotation) via stdlib `logging`. With `APPENV_VERBOSE=1`, an additional dimmed console handler surfaces user-facing operational messages; internal diagnostics stay file-only. Handler setup is documented in `setup_logging` and `_ConsoleDiagnosticFilter` in `src/appenv.py`.

**Message format**: every message carries a topic prefix followed by `key=value` pairs (`<topic>: key=value key=value`). The topic names the event class (`binary-not-found`, `uv-version-invalid`, `venv-health-check-failed`); the key-value pairs carry the concrete identifiers — paths, versions, commands — that make a message reconstructable. Formatting is lazy via `%s` / `%d`:

```python
log.info("creating-venv: python=%s path=%s", sys.executable, self.venv_real)
```

**Log levels**:

| Level | Use | Example from code |
|-------|---------|----------------------|
| `DEBUG` | Internal diagnostics: discovery chains, fallbacks, binary probes | `log.debug("uv-appenv-probe: path=%s", self.managed_uv)` |
| `INFO` | Operational milestones: init, venv creation, migrations, exec calls | `log.info("exec-command: binary=%s argv=%s", cmd_path, argv)` |
| `WARNING` | Degraded state that appenv handled itself | `log.warning("corrupted-venv: venv=%s bin_python_missing=%s", ...)` |
| `ERROR` | Fatal error immediately before `sys.exit()` | `log.error("pyproject-not-found: path=%s", pyproject.path)` |

## Conventions

(dev-exit-codes)=

### Exit Codes

BSD sysexits.h constants used throughout:

| Constant | Value | Meaning |
|----------|-------|---------|
| `EXIT_CODE_USAGE` | 64 | Invalid arguments or malformed input |
| `EXIT_CODE_DATAERR` | 65 | Input data was correct but could not be processed |
| `EXIT_CODE_NOINPUT` | 67 | Required input file missing |
| `EXIT_CODE_UNAVAILABLE` | 68 | Required resource (binary, Python) not found |

### Type Annotations

Type annotations live in `.pyi` stub files, not in `.py` source files. The `src/appenv.pyi` stub is the complete type surface — it must include all public *and* private methods. Ruff's `ANN` rules are dropped because they ignore `.pyi` files entirely.

The `src/py.typed` marker file signals PEP 561 compliance to type checkers.

Any method signature change requires updating both `src/appenv.py` and `src/appenv.pyi` — see [](#stub-synchronization) for the enforcement gate.

### Documentation

Docs are built with Sphinx using MyST markdown and autoapi:

```console
tox -e docs
```

- **User docs**: `docs/user/` — usage and workflows
- **Dev docs**: `docs/dev/` — this guide

## Tests

```console
uv run pytest                              # all tests, including slow
uv run pytest tests/test_prepare.py        # specific file
uv run pytest -m "not slow"                # exclude slow tests
uv run pytest --cov=appenv                 # with coverage
```

### Two-Tier Model

appenv has no natural seam for an integration tier — `uv` is either mocked (unit) or real (E2E). Tests fall into exactly two tiers:

**Unit tests** (`tests/test_*.py`)
: Fast, no external dependencies, no real venvs. `uv` is mocked via `MockUvBin` where its behavior matters; other tests cover config parsing, gitignore handling, doc consistency, etc.

**E2E tests** (`tests/e2e/`)
: Real `uv`, real subprocess via `pexpect`. Exercises the full init-and-run workflow end-to-end. Requires `uv` installed on the system.

### Slow Marker

Real venvs / installs carry `@pytest.mark.slow` (mostly E2E). All tests run by default; filter with `-m "not slow"` or `-m slow`.

(test-type-stubs)=

### Test Type Stubs

Test stubs live alongside their `.py` files in `tests/`. Every test function, helper, and class has a corresponding stub entry. Markers (`@pytest.mark.slow`, `@pytest.mark.parametrize(...)`) are preserved in stubs.

(stub-synchronization)=

### Stub Synchronization

Every `.pyi` stub must stay in sync with its runtime `.py`. This is enforced by `tools/check_stub_sync.py` (the `check-stub-sync` pre-commit hook), which also runs in CI through the `pre-commit` tox env — drifted stubs cannot be committed. The tool's module docstring documents discovery and stubtest invocation; supporting config lives in `pyproject.toml [tool.mypy]` and `tools/stubtest-allowlist`.

The runtime `.py` is the source of truth. When stubtest reports a difference, fix the stub — never the runtime.

**Validation:**

```console
uv run ruff check --select PYI tests/                              # stub style
uv run --group test --group mypy python tools/check_stub_sync.py   # enforced gate
```
