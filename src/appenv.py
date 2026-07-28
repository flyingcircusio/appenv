#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Flying Circus
"""appenv: pin Python packages to exact versions and expose their
binaries via symlinks. One file, no install step.

Requires `uv` (https://docs.astral.sh/uv/) on PATH.

Commands:
  init              Create a new pyproject.toml project + binary symlink
  prepare           Create/update the venv from pyproject.toml + uv.lock
  update-lockfile   Re-resolve dependencies and write uv.lock
  run CMD ...       Run CMD from the venv
  python ...        Run Python in the venv
  uv ...            Run uv with the project paths set
  reset             Delete the venv
  version           Show appenv version

Design notes (what got cut vs. the original, and why):
  - uv must already be on PATH. No nix/pip/GitHub-download fallback chain.
    If uv is missing, appenv tells you to install it and stops.
  - No requirements.txt -> pyproject.toml migration. If you have an old
    requirements.txt, translate it by hand (or ask an LLM to do it once).
  - No self-update. Re-download appenv.py when you want a new version.
  - No auto-discovery/re-exec across every installed Python. appenv checks
    the current interpreter against requires-python and tells you which
    one to use if it doesn't match, instead of silently switching for you.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

__version__ = "2026.7.28"

EXIT_USAGE = 64  # bad arguments
EXIT_DATAERR = 65  # input was well-formed but unusable (e.g. stale lock)
EXIT_NOINPUT = 67  # a required file is missing
EXIT_UNAVAILABLE = 68  # a required external tool is missing

GITIGNORE_ENTRIES = [".venv", ".appenv"]


def die(msg: str, code: int) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def build_env(overlays: dict[str, str] | None = None) -> dict[str, str]:
    """Child-process env: current env minus PYTHONPATH, plus overlays."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    if overlays:
        env.update(overlays)
    return env


def run_checked(argv: list[str], **kwargs) -> subprocess.CompletedProcess:
    kwargs.setdefault("env", build_env())
    result = subprocess.run(argv, **kwargs)
    if result.returncode != 0:
        die(f"command failed ({result.returncode}): {' '.join(argv)}", EXIT_DATAERR)
    return result


# --------------------------------------------------------------------------
# uv discovery — PATH only
# --------------------------------------------------------------------------

MIN_UV_VERSION = (0, 5, 0)


def find_uv() -> Path:
    uv_path = shutil.which("uv")
    if not uv_path:
        die(
            "uv not found on PATH. Install it from https://docs.astral.sh/uv/",
            EXIT_UNAVAILABLE,
        )
    uv = Path(uv_path)

    try:
        out = subprocess.run(
            [str(uv), "--version"],
            capture_output=True,
            text=True,
            check=True,
            env=build_env(),
        ).stdout.strip()
        version = tuple(int(p) for p in out.split()[1].split(".")[:3])
    except (subprocess.CalledProcessError, IndexError, ValueError):
        die(f"could not determine version of uv at {uv}", EXIT_UNAVAILABLE)

    if version < MIN_UV_VERSION:
        die(
            f"uv at {uv} is version {'.'.join(map(str, version))}, "
            f"need >= {'.'.join(map(str, MIN_UV_VERSION))}",
            EXIT_UNAVAILABLE,
        )
    return uv


# --------------------------------------------------------------------------
# pyproject.toml — minimal, hand-rolled (appenv ships zero deps, so no
# real TOML writer). Only ever writes a fresh [project] section; refuses
# to touch a pyproject.toml that already has one.
# --------------------------------------------------------------------------


def has_project_section(pyproject_path: Path) -> bool:
    if not pyproject_path.exists():
        return False
    for line in pyproject_path.read_text().splitlines():
        s = line.strip()
        if s == "[project]" or s.startswith("[project."):
            return True
    return False


def write_pyproject(
    base: Path, name: str, description: str, deps: list[str], python_version: str
) -> Path:
    path = base / "pyproject.toml"
    deps_toml = ",\n    ".join(f'"{d}"' for d in deps)
    deps_block = f"[\n    {deps_toml},\n]" if deps else "[]"
    section = f"""[project]
name = "{name}"
version = "0.1.0"
description = "{description}"
dependencies = {deps_block}
requires-python = ">={python_version}"
"""
    existing = path.read_text() if path.exists() else ""
    path.write_text((existing.rstrip() + "\n\n" + section) if existing else section)
    return path


def requires_python_min(pyproject_path: Path) -> str | None:
    if not pyproject_path.exists():
        return None
    m = re.search(
        r'requires-python\s*=\s*["\']>=\s*(\d+\.\d+)', pyproject_path.read_text()
    )
    return m.group(1) if m else None


def ensure_pyproject(base: Path) -> Path:
    path = base / "pyproject.toml"
    if has_project_section(path):
        return path
    die(
        f"no pyproject.toml with a [project] section in {base}.\nRun: ./appenv init",
        EXIT_NOINPUT,
    )


def parse_requirements_txt(path: Path) -> list[str]:
    """Turn requirements.txt into a plain dependency list.

    Simple on purpose: keeps normal ``pkg==1.2.3`` style lines, skips
    comments/blanks and pip options (``-e``, ``--index-url``, etc). If your
    requirements.txt leans on index URLs or editable installs, add those to
    pyproject.toml by hand after migrating.
    """
    deps = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        deps.append(line)
    return deps


def ensure_gitignore(base: Path) -> None:
    path = base / ".gitignore"
    existing = path.read_text().splitlines() if path.exists() else []
    missing = [e for e in GITIGNORE_ENTRIES if e not in existing]
    if not missing:
        return
    content = "\n".join(existing)
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content + "\n".join(missing) + "\n")


# --------------------------------------------------------------------------
# AppEnv — the actual commands
# --------------------------------------------------------------------------


class AppEnv:
    def __init__(self, base: Path, original_cwd: Path) -> None:
        self.base = base.resolve()
        self.original_cwd = original_cwd
        self.appenv_dir = self.base / ".appenv"
        self.appenv_script = self.base / "appenv"
        self.venv_real = self.appenv_dir / "venv"
        self.venv_link = self.base / ".venv"
        self.venv_python = self.venv_real / "bin" / "python"

    # ---- init ----

    def init(self, args: argparse.Namespace) -> None:
        target = (
            (self.original_cwd / args.path).resolve()
            if args.path
            else self.original_cwd
        )
        target.mkdir(parents=True, exist_ok=True)
        os.chdir(target)
        self.base = target
        self.appenv_dir = target / ".appenv"
        self.appenv_script = target / "appenv"
        self.venv_real = self.appenv_dir / "venv"
        self.venv_link = target / ".venv"

        pyproject_path = target / "pyproject.toml"
        if has_project_section(pyproject_path):
            die(
                f"{pyproject_path} already has a [project] section. "
                "Edit it directly or use `./appenv uv add`.",
                EXIT_DATAERR,
            )

        name = args.binary or "app"
        deps = args.deps or [name]
        if any(not d.strip() for d in deps):
            die("--dep must not be empty", EXIT_USAGE)
        deps = list(dict.fromkeys(deps))  # dedupe, preserve order

        if (
            "/" in name
            or "\\" in name
            or name in (".", "..")
            or any(c.isspace() for c in name)
        ):
            die(f"--binary must be a bare name, got {name!r}", EXIT_USAGE)
        link = target / name
        if link.exists() and not (link.is_symlink() and os.readlink(link) == "appenv"):
            die(f"{link} already exists and is not an appenv symlink", EXIT_USAGE)

        if not self.appenv_script.exists():
            self.appenv_script.write_bytes(Path(__file__).read_bytes())
            self.appenv_script.chmod(0o755)
            print(f"Created {self.appenv_script}")

        write_pyproject(
            target,
            name=args.name or target.name,
            description=args.description or "",
            deps=deps,
            python_version=args.python_version or "3.13",
        )
        print(f"Created {pyproject_path}")

        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to("appenv")
        print(f"Created ./{name} -> appenv")

        uv = find_uv()
        print("Generating lock file ...")
        run_checked([str(uv), "lock"], cwd=target, env=build_env())

        ensure_gitignore(target)
        print("\n=== Appenv project initialized ===")
        print(f"Use `./{name}` to run the {name} binary")

    # ---- migrate ----

    def migrate(self, args: argparse.Namespace) -> None:
        target = (
            (self.original_cwd / args.path).resolve()
            if args.path
            else self.original_cwd
        )
        target.mkdir(parents=True, exist_ok=True)
        os.chdir(target)
        self.base = target
        self.appenv_dir = target / ".appenv"
        self.appenv_script = target / "appenv"

        pyproject_path = target / "pyproject.toml"
        if has_project_section(pyproject_path):
            print(
                f"{pyproject_path} already has a [project] section — nothing to migrate."
            )
            return

        req_path = target / "requirements.txt"
        if not req_path.exists():
            die(f"no requirements.txt found in {target}", EXIT_NOINPUT)

        deps = parse_requirements_txt(req_path)
        write_pyproject(
            target,
            name=target.name,
            description="Migrated appenv project",
            deps=deps,
            python_version="3.13",
        )
        print(
            f"Wrote {pyproject_path} with {len(deps)} dependency(ies): {', '.join(deps)}"
        )

        if not self.appenv_script.exists():
            self.appenv_script.write_bytes(Path(__file__).read_bytes())
            self.appenv_script.chmod(0o755)
            print(f"Created {self.appenv_script}")

        uv = find_uv()
        print("Generating lock file ...")
        run_checked([str(uv), "lock"], cwd=target, env=build_env())

        ensure_gitignore(target)
        print("\n=== Migration complete ===")
        print(
            "requirements.txt kept as-is; you can delete it once you've checked pyproject.toml."
        )

    # ---- prepare / venv ----

    def _check_python_compatible(self) -> None:
        min_v = requires_python_min(self.base / "pyproject.toml")
        if not min_v:
            return
        current = f"{sys.version_info[0]}.{sys.version_info[1]}"
        if tuple(map(int, current.split("."))) < tuple(map(int, min_v.split("."))):
            die(
                f"running Python {current}, but this project needs >= {min_v}.\n"
                f"Re-run appenv with a compatible python: e.g. `python{min_v} ./appenv ...`",
                EXIT_DATAERR,
            )

    def prepare(self) -> Path:
        ensure_pyproject(self.base)
        lock = self.base / "uv.lock"
        if not lock.exists():
            die("no uv.lock found. Run: ./appenv update-lockfile", EXIT_NOINPUT)

        self._check_python_compatible()
        uv = find_uv()
        self.appenv_dir.mkdir(exist_ok=True)

        # Drop a corrupted venv (bin/python missing).
        if self.venv_real.exists() and not self.venv_python.exists():
            shutil.rmtree(self.venv_real)

        run_env = build_env({"UV_PROJECT_ENVIRONMENT": str(self.venv_real)})

        if not self.venv_real.exists():
            print("Creating venv ...")
            run_checked(
                [str(uv), "venv", "--python", sys.executable, str(self.venv_real)],
                env=run_env,
            )

        try:
            run_checked([str(uv), "lock", "--check"], cwd=self.base, env=run_env)
        except SystemExit:
            die(
                "lockfile is stale (pyproject.toml changed). Run: ./appenv update-lockfile",
                EXIT_DATAERR,
            )

        print("Syncing dependencies ...")
        run_checked(
            [str(uv), "sync", "--no-dev", "--frozen"], cwd=self.base, env=run_env
        )

        if self.venv_link.is_symlink():
            self.venv_link.unlink()
        if not self.venv_link.exists():
            self.venv_link.symlink_to(
                os.path.relpath(self.venv_real, self.base), target_is_directory=True
            )

        return self.venv_real

    def update_lockfile(self) -> None:
        ensure_pyproject(self.base)
        uv = find_uv()
        print("Updating lock file ...")
        run_checked([str(uv), "lock"], cwd=self.base, env=build_env())

    def reset(self) -> None:
        if self.venv_link.is_symlink():
            self.venv_link.unlink()
        if self.venv_real.exists():
            print(f"Removing {self.venv_real} ...")
            shutil.rmtree(self.venv_real)

    # ---- run / python / uv ----

    def run(self, command: str, argv: list[str]) -> None:
        venv = self.prepare()
        cmd_path = venv / "bin" / command
        if not cmd_path.exists():
            available = sorted(p.name for p in (venv / "bin").iterdir() if p.is_file())
            die(
                f"'{command}' not found in {venv}/bin/. Available: {', '.join(available) or '(none)'}",
                EXIT_NOINPUT,
            )
        os.chdir(self.original_cwd)
        run_env = build_env({"APPENV_BASEDIR": str(self.base)})
        os.execve(str(cmd_path), [str(cmd_path), *argv], run_env)

    def run_uv(self, argv: list[str]) -> None:
        ensure_pyproject(self.base)
        uv = find_uv()
        os.chdir(self.base)
        run_env = build_env({"UV_PROJECT_ENVIRONMENT": str(self.venv_real)})
        os.execve(str(uv), [str(uv), *argv], run_env)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="appenv", description=__doc__.split("\n\n")[0]
    )
    parser.add_argument("--version", action="version", version=f"appenv {__version__}")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("init", help="Create project")
    p.add_argument("path", nargs="?")
    p.add_argument("--name")
    p.add_argument("--binary")
    p.add_argument("--dep", action="append", dest="deps")
    p.add_argument("--python-version")
    p.add_argument("--description")

    p = sub.add_parser("migrate", help="Convert requirements.txt to pyproject.toml")
    p.add_argument("path", nargs="?")

    sub.add_parser("prepare", help="Create the venv")
    sub.add_parser("update-lockfile", help="Re-resolve dependencies")
    sub.add_parser("reset", help="Delete the venv")
    sub.add_parser("version", help="Show version")

    p = sub.add_parser("run", help="Run a command in the venv", add_help=False)
    p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sub.add_parser("python", help="Run Python in the venv", add_help=False)
    p.add_argument("rest", nargs=argparse.REMAINDER)
    p = sub.add_parser("uv", help="Run uv with project paths set", add_help=False)
    p.add_argument("rest", nargs=argparse.REMAINDER)

    return parser


def main() -> None:
    basedir_str = os.environ.get("APPENV_BASEDIR")
    basedir = Path(basedir_str) if basedir_str else Path(__file__).parent
    original_cwd = Path.cwd()
    appenv = AppEnv(basedir, original_cwd)

    application_name = Path(__file__).stem
    if application_name != "appenv":
        # Invoked as a generated symlink, e.g. ./mytool
        appenv.run(application_name, sys.argv[1:])
        return

    parser = build_parser()
    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
        sys.exit(0)
    elif args.cmd == "init":
        appenv.init(args)
    elif args.cmd == "migrate":
        appenv.migrate(args)
    elif args.cmd == "prepare":
        appenv.prepare()
    elif args.cmd == "update-lockfile":
        appenv.update_lockfile()
    elif args.cmd == "reset":
        appenv.reset()
    elif args.cmd == "version":
        print(f"appenv {__version__}")
    elif args.cmd == "run":
        rest = args.rest
        if not rest:
            die("usage: appenv run CMD [ARGS...]", EXIT_USAGE)
        os.environ["APPENV_BASEDIR"] = str(basedir)
        appenv.run(rest[0], rest[1:])
    elif args.cmd == "python":
        appenv.run("python", args.rest)
    elif args.cmd == "uv":
        appenv.run_uv(args.rest)


if __name__ == "__main__":
    main()
