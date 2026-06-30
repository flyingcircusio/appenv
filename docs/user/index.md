# User Guide

## Topics

```{toctree}
:titlesonly:
workflows
commands
locking-behavior
```

## Requirements

- **Python**: 3.9+ for the appenv script, 3.10+ for managed environments
- **uv**: 0.5.0 or later (auto-installed if not found)

## New Project

Which install method is right for you?

- **Want the easiest setup?** → Use `uvx appenv init` (pulls latest version from PyPI)
- **No uv available on your machine?** → Download appenv script from GitHub directly

All methods give you the same `./appenv` file — the only difference is how you get it.

### New project using uvx

`uvx` is part of [uv](https://docs.astral.sh/uv/) — the easiest way to start:

```console
# appenv init is interactive
# Answer:
# httpie as dependency
# http as binary
uvx appenv init myproject
cd myproject
./http
```

**What just happened?**

- appenv installed itself inplace by adding the `./myproject/appenv` script
- `init` created `pyproject.toml` in `myproject` and a symlink `http → appenv`
- `./http` runs the `http` binary from the appenv-managed venv, with pinned versions from `uv.lock`.

The repository now contains:

```
myproject/
├── appenv          # The appenv script (single file, committed to git)
├── http -> appenv  # Symlink which tells appenv to run the http binary from the venv
├── .appenv         # appenv-managed venv, logs
├── .venv           # links to .appenv/venv (for standard dev tools)
├── pyproject.toml  # Project config and dependency list
└── uv.lock         # Exact versions of all dependencies (committed to git)
```

### Download appenv directly

Just one file:

```console
mkdir myproject && cd myproject
curl -sL https://raw.githubusercontent.com/flyingcircusio/appenv/master/src/appenv.py -o appenv
chmod +x appenv
# appenv init is interactive
# Answer:
# http as binary
# httpie as dependency
./appenv init
```

### Prereleases

For alpha/beta pre-release versions of `appenv`, use:

```console
uvx --prerelease allow appenv version
```

## Next Steps

- {doc}`workflows` — Common usage tips
- {doc}`commands` — All subcommands and options
- Learn more about dependency management: appenv builds on [uv](https://docs.astral.sh/uv/)
    - [What is uv?](https://docs.astral.sh/uv/) — Overview and key features
    - [Installing uv](https://docs.astral.sh/uv/getting-started/installation/) — All installation methods
    - [uv as pip/virtualenv replacement](https://docs.astral.sh/uv/pip/) — How uv replaces traditional Python tooling
    - [What is uv.lock?](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile) — Understanding the lockfile
    - [The uv run command](https://docs.astral.sh/uv/reference/cli/#uv-run) — How appenv executes your tools
