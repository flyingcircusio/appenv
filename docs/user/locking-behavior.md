# Locking Behavior

## How UV Locking Works

**Lockfiles are deterministic by default.** UV won't automatically upgrade packages when new versions are released. Once `uv.lock` exists, UV prefers the locked versions unless you explicitly request an upgrade.

### Three Sync Modes

| Flag | Behavior | When to Use |
|------|----------|-------------|
| (none) | May update `uv.lock` if `pyproject.toml` changed | Default behavior for most operations |
| `--frozen` | Uses existing lockfile, fails if missing | Production deployments, CI/CD |
| `--locked` | Uses existing lockfile, fails if outdated | When you want to ensure lockfile is current |

A lockfile is "outdated" when `pyproject.toml` dependencies changed — **not** when new package versions are available upstream. Changing a version constraint in `pyproject.toml` makes the lockfile outdated; a new PyPI release does not.

## appenv Command Mapping

| Command | Lockfile Mode | UV Command | Behavior |
|---------|---------------|------------|----------|
| `./http` (symlink dispatch) | Frozen | `uv sync --no-dev --frozen` | Production run, exact versions from lockfile |
| `prepare` | Frozen | `uv sync --no-dev --frozen` | Production deps only, requires existing lockfile |
| `update-lockfile` | Updates | `uv lock` | Regenerates lockfile from pyproject.toml |
| `run` | Unfrozen | `uv run` | Delegates to uv run, no frozen enforcement |
| `uv` | Unfrozen | (pass-through) | Delegates to uv directly, no lockfile enforcement |

### Key Rules

1. **Running the application or `prepare` requires an existing `uv.lock`** — these use `--frozen` and fail without it. Run `update-lockfile` first.
2. **Always commit `uv.lock` to version control** — this ensures reproducible builds across machines.

## Handling Missing Lockfiles

If you run `./http` or `prepare` without a lockfile:

```console
$ ./http
No uv.lock found. Run: ./appenv update-lockfile
```

Generate it first:

```console
$ ./appenv update-lockfile
$ ./http  # Now works
```

For examples of adding, upgrading, and reviewing dependencies, see {doc}`workflows`.

## Troubleshooting

### "No uv.lock found"

Run `./appenv update-lockfile` to generate it.

### Lockfile Conflicts in Git

1. Resolve conflicts in `pyproject.toml` first
2. Run `./appenv update-lockfile` to regenerate a clean lockfile
3. Commit the resolved `uv.lock`

### "Lockfile is outdated"

`pyproject.toml` has changed since the lockfile was generated. Run `./appenv update-lockfile` to sync.

## UV Universal Resolution

UV uses **universal resolution**: all dependencies are resolved to be compatible with the entire `requires-python` range. For `requires-python = ">=3.11,<3.14"`, UV ensures every package works across Python 3.11, 3.12, and 3.13. You don't need to generate separate lockfiles per Python version.

For more details on uv's lockfile and resolution concepts, see the [uv lockfile documentation](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile) and [resolution concepts](https://docs.astral.sh/uv/concepts/resolution/).
