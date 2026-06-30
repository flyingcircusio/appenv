# appenv

[![E2E Tests](https://github.com/dpausp/appenv/actions/workflows/e2e.yml/badge.svg)](https://github.com/dpausp/appenv/actions/workflows/e2e.yml) [![Tox Tests](https://github.com/dpausp/appenv/actions/workflows/main.yml/badge.svg)](https://github.com/dpausp/appenv/actions/workflows/main.yml)

appenv pins Python packages to exact versions and exposes their binaries
via symlinks — one file, no installation step. Drop it into a repository,
commit it, and every checkout (local or remote) gets the same tools at the
same versions by running `./http`, `./pytest`, `./batou`, or whatever you need.

**appenv never modifies your system** — all state lives in `.appenv/` inside
the project directory. Remove that folder and nothing is left behind.

Built on [uv](https://docs.astral.sh/uv/) for environment management.

## Using an existing appenv project

Someone gave you a project that already uses appenv? Just run the command:

```console
git clone <project> && cd <project>
./http  # First run sets up everything automatically
```

Running the command will get an appenv-managed [uv](https://docs.astral.sh/uv/) if it's not globally available on your system.

No `uv.lock` (should be committed) or dependencies changed?

```console
./appenv update-lockfile
```

(Only needed again after manually editing `pyproject.toml`)

Use `./appenv uv add/remove` to manage your dependencies or just use `uv` as you are used to it.


### Upgrading from requirements.txt

Already an appenv user and still using `requirements.txt` instead of `pyproject.toml`?

```console
uvx appenv migrate
```

## New Project

Requires Python 3.9+ (managed environments need 3.10+). [uv](https://docs.astral.sh/uv/) 0.5.0+ is auto-installed if not found.
Get appenv via `uvx` or download the single-file script.

`appenv init` will ask you some questions and set up the project (interactive
by default — pass `--binary` and `--dep` for non-interactive use). The example
assumes that you want to run a binary called `http` from the `httpie` package.

### uvx (uv)

`uvx` is part of [uv](https://docs.astral.sh/uv/) — the easiest way to start:

```shell
# appenv init is interactive
# Answer:
# httpie as dependency
# http as binary
uvx appenv init
./http
```

### Manual Download

No uv installed? Download appenv directly:

```shell
curl -sL https://raw.githubusercontent.com/flyingcircusio/appenv/master/src/appenv.py -o appenv
chmod +x appenv
# appenv init is interactive
# Answer:
# httpie as dependency
# http as binary
./appenv init
./http
```

**What just happened?**

- appenv installed itself inplace by adding the `./appenv` script.
- `init` created `pyproject.toml` and a symlink `http → appenv`.
- `./http` set up the venv with pinned versions from `uv.lock`, then ran the `http` binary (from the [httpie](https://github.com/httpie/httpie) package)

The repository now contains:

```shell
myproject/
├── appenv          # The appenv script
├── http -> appenv  # Runs the `http` binary from installed deps
├── pyproject.toml  # Project config and dependency list
└── uv.lock         # Exact versions of all dependencies
```

All of these files should be VCS-tracked to ensure a consistent environment across all machines.

### Non-Interactive / CI

For scripts and CI pipelines — no TTY needed:

```shell
appenv init --binary http --dep httpie --name myproject
```

### Development

For dev tooling, `uv run` and other `uv` commands work transparently.
`appenv` automatically creates a `.venv` symlink to make this work:

```shell
# includes dev dependencies automatically
uv run pytest -xvs
```

## Documentation

Full documentation at [Readthedocs](https://appenv-test.readthedocs.io):

- [User Guide](docs/user/index.md) -- how to get started with appenv
- [Commands Reference](docs/user/commands.md) -- all commands with options
- [Workflows](docs/user/workflows.md) -- common usage patterns
- [Locking Behavior](docs/user/locking-behavior.md) -- how uv.lock works
- [Developer Guide](docs/dev/index.md) -- development setup and architecture
