# Common Workflows

Practical workflows for using appenv in existing projects. See the [User Guide](index.md) for new projects.

## Migrating from requirements.txt

When you have an existing project with `requirements.txt` and want to switch to appenv:

```console
# If appenv is already in your project
./appenv migrate

# If not (e.g. running via uvx)
uvx appenv migrate

# After migration, verify and clean up
./appenv run http --help  # or: ln -s appenv http && ./http --help
rm requirements.txt
```

Version pins from `requirements.txt` are **not** preserved — `uv.lock` resolves fresh. Check the lockfile if exact versions matter.

See {ref}`migrate` for more details.

## Developing an Appenv-managed Project

```console
# Run dev tools — use uv run to include dev dependencies
uv run pytest -xvs
uv run ruff check .
uv run ruff format .

# Add dependencies
./appenv uv add --group dev pytest
./appenv update-lockfile
```

Symlinks like `./pytest → appenv` always run **without** dev dependencies — they expose only production binaries from the pinned venv. A dev tool reached through a symlink breaks unless it is also a production dependency.

### Adding and Upgrading Dependencies

```console
# Add a production dependency (updates both pyproject.toml and uv.lock)
./appenv uv add requests

# Add a development dependency
./appenv uv add --group dev pytest

# Upgrade a specific package
./appenv uv lock --upgrade-package requests

# Upgrade all packages
./appenv uv lock --upgrade
```

### Managing Multiple Python Versions

```toml
# pyproject.toml
[project]
requires-python = ">=3.11,<3.14"
```

appenv automatically selects the best available Python version. See {doc}`locking-behavior` for details on UV universal resolution across the `requires-python` range.

## Troubleshooting

### Logs

appenv writes a structured log file to `.appenv/logs/appenv.log` for every invocation. Every step — uv discovery, version checks, Python selection, venv creation, the final exec call — is recorded with a topic prefix and `key=value` context, so you can reconstruct exactly what appenv did without re-running it.

```console
$ tail -5 .appenv/logs/appenv.log
2026-06-23 14:52:27 [DEBUG] ensure_uv:2216 ensure-uv-bin: path=/srv/s-dev/.local/bin/uv
2026-06-23 14:52:27 [DEBUG] get_uv_version:855 uv-version-raw: output=uv 0.11.19 (x86_64-unknown-linux-gnu)
2026-06-23 14:52:27 [DEBUG] ensure_uv:2219 ensure-uv-version: version=0.11.19
2026-06-23 14:52:27 [INFO] run_uv:1901 exec-uv: binary=/srv/s-dev/.local/bin/uv argv=['...', 'run', 'http', '--version']
```

Each line is `timestamp [LEVEL] function:lineNo topic: key=value key=value`. The topic names the event class (`uv-discovery-start`, `python-re-exec`, `exec-uv`); the key-value pairs carry the concrete paths, versions, and commands. To diagnose a failure, find the last line before the error and read upwards — the topic tells you which step failed, the keys tell you why.

### Verbose Mode

```console
APPENV_VERBOSE=1 ./http --version
```

Prints the same operational messages (uv commands, Python selection, venv steps) to the console with a dimmed `→` prefix — a live view of what the log file captures. Internal diagnostics are filtered out; for the full trace, read the log file.

```console
→ uv-discovery-start: appenv_dir=/tmp/myproject/.appenv
→ uv-path-probe: found=/usr/local/bin/uv
→ ensure-uv-version: version=0.11.19
→ exec-uv: binary=/usr/local/bin/uv argv=['...', 'run', 'http', '--version']
```

### Container Environments

In containers or on CIFS mounts, uv may warn about failed hardlinks:

```console
warning: Failed to hardlink files; falling back to full copy.
```

This is harmless. To suppress it, set `UV_LINK_MODE=copy`:

```console
UV_LINK_MODE=copy ./http
```

See [astral-sh/uv#6101](https://github.com/astral-sh/uv/issues/6101) for details.

### Python Version Selection

If the wrong Python version is selected, check in this order:

1. **`requires-python`** in `pyproject.toml` — this is the constraint appenv enforces
2. **Installed Pythons** — appenv scans `python3.X` binaries on `PATH` newest-first and picks the highest that satisfies `requires-python`
3. **Verbose output** — `APPENV_VERBOSE=1` prints the candidate chain (`python-skip-constraint`, `python-already-best`, `python-re-exec`)

To force a specific Python and skip appenv's selection entirely, set `APPENV_BEST_PYTHON` before the call — appenv checks for it at startup and short-circuits:

```console
APPENV_BEST_PYTHON=/usr/bin/python3.12 ./mkdocs build
```
