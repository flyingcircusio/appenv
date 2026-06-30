# Commands Reference

Complete reference for all appenv commands.

## Global Options

```
./appenv --help
```

## update-lockfile

Update the dependency lockfile (`uv.lock`). See {doc}`locking-behavior` for details on UV's locking model.

```console
./appenv update-lockfile           # Update lockfile
./appenv update-lockfile --diff    # Show changes without writing
```

### Options

| Option | Description |
|--------|-------------|
| `--diff` | Show full diff without writing lockfile |

Use `APPENV_VERBOSE=1` for verbose output.

### When to Use

- After changing dependencies in `pyproject.toml` (add, remove, or update version constraints)
- Before deploying — ensures the lockfile reflects current requirements
- When onboarding — run once after cloning to generate `uv.lock`

See {doc}`workflows` for detailed examples.

## init

Create a new `pyproject.toml` project. Interactive by default; use flags for scripting.

### Interactive Mode (default)

Run without flags — `init` asks five questions:

1. Dependencies (one per line, empty line to finish; default: `app`)
2. Binary to expose — creates `./<name>` symlink that runs the installed `<name>` binary (default: `app`)
3. Project name (default: `<directory name>`)
4. Description
5. Minimum Python version (default: `3.13`)

```console
$ ./appenv init
Let's create a new appenv project in myproject
I'll ask a few questions, then create pyproject.toml here

Enter dependencies (one per line, empty line to finish):
  Default: app
  Dependency: httpie

Binary to expose (creates ./<name> symlink) [app] http
```

The default binary name is always `app`. To expose a different binary (e.g. `http`), type it at the prompt or create a symlink: `ln -s appenv http`.

### Non-Interactive Mode (scripting / CI)

Pass `--binary` to skip all prompts. `--dep` is required (at least one) — `init` only creates new projects and refuses to touch an existing `[project]` section.

```console
appenv init --binary http --dep httpie --dep pytest --name myproject
```

Without a TTY and missing required flags, `init` prints an error with a usage example and exits with code 64 (USAGE).

### Options

| Flag | Description |
|------|-------------|
| `path` | Target directory for the new project (default: current directory) |
| `--binary NAME` | Binary to expose as `./<name>` symlink. Required for non-interactive. |
| `--dep PACKAGE` | Package dependency. Repeat for multiple: `--dep httpie --dep pytest`. Required (at least one). |
| `--name NAME` | Project name (default: directory name). |
| `--python-version VER` | Minimum Python version, format `X.Y` (default: `3.13`). |
| `--description TEXT` | Project description (default: empty). Non-interactive only. |

### Additional Symlinks

The symlink name must match a binary installed by your dependencies.
Create additional symlinks to expose more binaries:

```console
# After installing ruff and pytest as dependencies
ln -s appenv ruff
ln -s appenv pytest
./ruff check .
./pytest -xvs
```

### Existing Project: Refused

If `pyproject.toml` already has a `[project]` section, `init` exits with code 65 (DATAERR) and prints guidance pointing at `./appenv uv add` and direct editing. This prevents silent field loss: earlier versions rewrote the whole `[project]` section, dropping fields appenv cannot round-trip without a TOML writer (readme, license, classifiers, urls, dynamic, scripts, gui-scripts, `[project.scripts]`, `[project.optional-dependencies]`).

```console
$ ./appenv init
pyproject.toml already has a [project] section.
appenv `init` no longer updates existing projects (silent field loss risk).
Use `./appenv uv add` to manage dependencies, or edit pyproject.toml directly.
```

This behavior is identical on every supported Python version (3.9+).

### If appenv Script Is Outdated

When the local `./appenv` script has a different version than the running appenv, `init` prints a warning:

```console
Warning: ./appenv is version 0.0.1, running appenv is 2026.3.19.
Run './appenv self-update' to update the script.
```

(migrate)=
## migrate

Convert an existing `requirements.txt` into `pyproject.toml`. For appenv projects that still use `requirements.txt` instead of `pyproject.toml`.

```console
./appenv migrate
```

### Options

- `path` — Target directory (default: current directory)

### What It Does

- Reads `requirements.txt` from the current directory
- Creates or updates `pyproject.toml` with those dependencies
- Generates `uv.lock` automatically
- Separates pip-options (`--index-url`, `--extra-index-url`, `--hash`, …) from dependencies instead of writing them as broken specifiers — see {ref}`Handling pip-options <handling-pip-options>`
- Skips editable installs (`-e`) with a warning
- Cleans up old `.appenv/` artifacts
- Updates the local `./appenv` script if the running version differs from the one on disk
- Creates or updates `.gitignore` with `.venv`, `.appenv`, and `.batou-lock` entries

(handling-pip-options)=
### Handling pip-options

Every line starting with `-` is treated as a pip-option and kept out of the `[project] dependencies` list. This is what lets migration work for `requirements.txt` files that previously crashed `uv lock`. Each category of option is handled differently:

#### Index URLs → `[[tool.uv.index]]`

`--index-url` and `--extra-index-url` are translated into [`[[tool.uv.index]]`](https://docs.astral.sh/uv/configuration/indexes/) entries in `pyproject.toml`. This is what unblocks projects using private registries (GitLab Package Registry, AWS CodeArtifact, Artifactory).

**Credentials are never copied into `pyproject.toml`.** If an index URL carries embedded credentials (deploy token, API key), migrate strips them and writes only the clean URL, then tells you which environment variables to set so `uv lock` can authenticate. The names follow uv's [index authentication](https://docs.astral.sh/uv/configuration/indexes/#authenticated-private-registries) convention:

| Variable | Purpose |
|----------|---------|
| `UV_INDEX_<NAME>_USERNAME` | Username for index `<NAME>` |
| `UV_INDEX_<NAME>_PASSWORD` | Password or token for index `<NAME>` |

`<NAME>` is the index name in uppercase. Set these in your shell (or CI secrets) before running `uv lock`. As an alternative to environment variables, you can put credentials in `~/.netrc`.

#### Unsupported options → dropped with warning

These pip-options have no `pyproject.toml` equivalent and are dropped:

- `--hash`, `--require-hashes`
- `--no-binary`
- `--only-binary`

migrate lists each skipped option so nothing disappears silently. If you depend on hash-pinning, audit the generated `uv.lock` yourself — uv computes its own hashes.

#### Editable installs

`-e` lines are skipped with a warning. Add them to `pyproject.toml` manually if you still need them.

### Running via uvx

If appenv is not yet in your project, you can run migrate directly:

```console
uvx appenv migrate
```

If appenv is not yet on stable PyPI:

```console
uvx --prerelease allow appenv migrate
```

This downloads the latest appenv into your project and runs the migration. Run the command from the project directory that contains `requirements.txt`.

### After Migrating

Test it (`./appenv run <binary> --help` — or create a symlink with `ln -s appenv <binary>` first), then remove `requirements.txt`.

See {doc}`workflows` for a full migration walkthrough.

### Failure Cases

- No `requirements.txt` found — exits normally with a suggestion to use `init`
- `pyproject.toml` already has `[project]` section — exits normally without changes

(self-update)=
## self-update

Update the local `./appenv` script to match the currently running version.

```console
./appenv self-update
```

### Options

| Option | Description |
|--------|-------------|
| `--check` | Check for version drift without updating (exit 0 if up-to-date, exit 1 if drift detected) |
| `path` | Target directory containing the appenv script (default: project directory) |

### What It Does

- Compares the `__version__` in the local `./appenv` script with the currently running version
- If versions differ: replaces the script with the running version
- If versions match: reports that the script is already up-to-date
- With `--check`: only reports drift status, does not modify any files

### Running via uvx

When running via `uvx`, appenv runs from an externally managed environment and cannot update itself in place. Specify the target directory:

```console
uvx appenv self-update .
uvx appenv self-update /path/to/project
```

If appenv is not yet on stable PyPI:

```console
uvx --prerelease allow appenv self-update .
```

### --check Mode

Use `--check` in CI or scripts to detect version drift:

```console
./appenv self-update --check
```

Exit codes:
- 0 — script is up-to-date
- 1 — version drift detected

### Failure Cases

- No `./appenv` script found — prints error, exits with code 67 (NOINPUT)

## prepare

Create the virtual environment with production dependencies. Requires an existing `uv.lock` — run {doc}`update-lockfile <commands>` first.

```console
./appenv prepare
```

### What It Does

- Validates that `pyproject.toml` and `uv.lock` exist
- Creates `.appenv/venv` with `uv venv`
- Installs production dependencies with `uv sync --no-dev --frozen`
- Updates `.venv` symlink to point to `.appenv/venv`

### When to Use

- CI/CD pipelines that need the venv before running commands
- Debugging: recreate the venv without removing and rebuilding from scratch
- Deployment scripts that prepare the environment explicitly

### Symlink Dispatch Alternative

Running `./http` (symlink to appenv) auto-prepares on first use. Explicit `prepare` is only needed when you want to control the timing.

## reset

Remove the virtual environment and clean up legacy artifacts.

```console
./appenv reset
```

### What It Removes

- `.venv` symlink
- `.appenv/venv` directory
- Old hash-based venvs in `.appenv/`

### What It Preserves

- Logs in `.appenv/logs/`
- Cached uv binary in `.appenv/.uv/`
- Profiling data in `.appenv/profiling/`
- Legacy symlink to current venv at `.appenv/current`
- `pyproject.toml` and `uv.lock`
- Source code and other project files

### Example Usage

```console
# After experiencing issues with the virtual environment
$ ./appenv reset
Removing .venv symlink ...
Removing .appenv/venv ...

# Then recreate it
$ ./appenv prepare
```

## version

Show appenv version.

```console
./appenv version
./appenv --version
```


## python

Start a Python REPL in the virtual environment.

```console
./appenv python                           # Start REPL
./appenv python -c "print('hello')"       # Execute code
./appenv python script.py --verbose       # Run script with args
```

### Details

- Automatically ensures the virtual environment is prepared (equivalent to running `prepare` first)
- Production dependencies only — dev dependencies are excluded
- For `python -m pytest` or other dev tool usage, use `uv run` instead:
  `uv run python -m pytest`

### Example

```console
$ ./appenv python
Python 3.x.x ...
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

## run

Run a command in the project virtual environment. Equivalent to `uv run` with appenv's configured paths.

```console
./appenv run pytest -xvs
./appenv run ruff check .
./appenv run python -c "print('hello')"
```

All arguments are passed through to `uv run` unchanged. This is useful for CI or deployment scripts that need to run arbitrary commands in the venv.

**Tip:** For commands you use frequently, create a symlink instead of typing `appenv run` every time:

```console
ln -s appenv pytest
ln -s appenv ruff
./pytest -xvs          # equivalent to: appenv run pytest -xvs
```

See the `init` command for details on symlink setup.


## uv

Pass-through to the uv binary with appenv's configured environment (Python interpreter, venv paths). Use this when you need uv functionality not covered by dedicated appenv commands.

```console
./appenv uv add requests           # Add production dependency
./appenv uv add --group dev pytest  # Add dev dependency
./appenv uv sync                    # Re-sync dependencies
./appenv uv lock --upgrade          # Upgrade all packages
```

All arguments are passed through to uv unchanged. See {doc}`workflows` for dependency management examples.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `APPENV_VERBOSE` | Show verbose output (uv commands, Python selection) |
| `APPENV_EXTRAS` | Extras to install (comma-separated) |
| `APPENV_BASEDIR` | Base directory of the project (auto-set) |
| `APPENV_BEST_PYTHON` | Selected Python interpreter (auto-set) |

See {doc}`workflows` for verbose mode example.

(exit-codes)=
## Exit Codes

appenv uses BSD sysexits.h exit codes:

| Code | Name | Description |
|------|------|-------------|
| 64 | USAGE | Incorrect command usage — unrecognized arguments or self-update from externally managed environment |
| 65 | DATAERR | Input data issue (e.g., invalid pyproject.toml) |
| 67 | NOINPUT | Missing input file (e.g., no pyproject.toml found) |
| 68 | UNAVAILABLE | Resource unavailable (e.g., required tool not found) |
| passthrough | run / uv / python | These commands delegate to the underlying tool; that tool's exit code propagates unchanged. |
| 1 | (self-update --check only) | Version drift detected by `self-update --check`. See the [self-update section](#self-update) for details. |

## Working with Extras

```toml
# pyproject.toml
[project.optional-dependencies]
dev = ["pytest", "ruff"]
```

```console
APPENV_EXTRAS=dev ./http
```
