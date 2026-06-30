# appenv

appenv pins Python packages to exact versions and exposes their binaries
via symlinks — one file, no installation step. Drop it into a repository,
commit it, and every checkout (local or remote) gets the same tools at the
same versions by running `./http`, `./pytest`, `./batou`, or whatever you need.

Built on [uv](https://docs.astral.sh/uv/) for environment management.
**appenv never modifies your system** — all state lives in `.appenv/` inside
the project directory. Remove that folder and nothing is left behind.


## Core Concepts

- **Single-file deployment**: `appenv.py` is the entire tool — drop it into any repository
- **Symlink dispatch**: `./http` (where `http → appenv`) runs the `http` binary from the pinned venv
- **Reproducible everywhere**: commit `appenv`, `pyproject.toml`, and `uv.lock` — every checkout gets identical versions
- **Multiple binaries**: create additional symlinks to expose more tools from the same venv

Requires Python 3.9+ (managed environments need 3.10+). [uv](https://docs.astral.sh/uv/) 0.5.0+ is auto-installed if not found. `pyproject.toml` must sit next to the appenv script.

## Getting Started

New to appenv? Start with the {doc}`user/index` for installation,
adding dependencies, and CI/CD — or see {doc}`user/workflows`
for practical examples including migrating existing legacy appenv projects.

For reference material, see {doc}`user/commands` and {doc}`user/locking-behavior`.

```{toctree}
:caption: Contents
user/index
dev/index
```
