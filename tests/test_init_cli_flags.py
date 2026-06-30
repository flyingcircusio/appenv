# SPDX-FileCopyrightText: 2020 Flying Circus
"""Tests for the init subcommand CLI flags.

* ``--python-version`` validates its value as ``\\d+\\.\\d+`` and exits
  ``EXIT_CODE_USAGE`` (64) on anything else — before any file is written.
* ``--description`` is exposed as a non-interactive flag and written into
  ``pyproject.toml``. Interactive pre-fill is out of scope for the spec.

Every test drives ``AppEnv.meta()`` — the real argparse entry point that
``./appenv init`` uses — so the validator, the help text, and the
non-interactive/interactive resolvers are all exercised end to end.
"""

import pytest

import appenv

# -- python-version-validation ------------------------------------------------
# Spec decision: a ``type=`` validator accepts only ``^\d+\.\d+$``. argparse's
# ArgumentTypeError routes through UsageArgumentParser.error() → exit 64 before
# create_pyproject runs. No minimum is enforced, only the format.


@pytest.mark.parametrize(
    "bad_version",
    [
        pytest.param("garbage", id="non-numeric"),
        pytest.param("3", id="single-component"),
        pytest.param("3.13.1", id="three-components"),
        pytest.param("v3.13", id="leading-v"),
        pytest.param("3.x", id="non-numeric-minor"),
        pytest.param("", id="empty"),
    ],
)
def test_init_rejects_malformed_python_version(bad_version, workdir, app_env, capsys):
    """init --python-version <bad> exits 64 via the usage parser and writes no
    pyproject.toml (spec requirement: garbage → exit 64, no file)."""
    env = app_env(workdir)

    with pytest.raises(SystemExit) as exc_info:
        env.meta(
            [
                "init",
                "--binary",
                "http",
                "--dep",
                "httpie",
                "--python-version",
                bad_version,
            ]
        )

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    err = capsys.readouterr().err
    assert "--python-version" in err, (
        f"usage error should name the offending flag; got: {err!r}"
    )
    assert not (workdir / "pyproject.toml").exists()


@pytest.mark.parametrize("good_version", ["3.9", "3.13", "4.0"])
def test_init_accepts_major_minor_python_version(good_version, workdir, app_env):
    """init --python-version <major>.<minor> writes requires-python verbatim —
    only the format is validated, no minimum is enforced (spec decision)."""
    env = app_env(workdir)

    env.meta(
        [
            "init",
            "--binary",
            "http",
            "--dep",
            "httpie",
            "--python-version",
            good_version,
        ]
    )

    pyproject = (workdir / "pyproject.toml").read_text()
    assert f'requires-python = ">={good_version}"' in pyproject


# -- description-flag ---------------------------------------------------------


def test_init_help_lists_description_flag(workdir, app_env, capsys):
    """init --help advertises --description alongside --name/--binary/--dep/
    --python-version (spec requirement: flag appears in --help)."""
    env = app_env(workdir)

    with pytest.raises(SystemExit):  # argparse --help always exits
        env.meta(["init", "--help"])

    help_text = capsys.readouterr().out
    for flag in (
        "--name",
        "--binary",
        "--dep",
        "--python-version",
        "--description",
    ):
        assert flag in help_text, f"{flag} missing from `init --help`"


def test_init_noninteractive_writes_description_flag(workdir, app_env):
    """init --binary http --dep httpie --description 'My Tool' writes
    description = 'My Tool' into pyproject.toml (spec requirement; the bug was
    a hardcoded description = '' in _resolve_init_params_noninteractive)."""
    env = app_env(workdir)

    env.meta(
        ["init", "--binary", "http", "--dep", "httpie", "--description", "My Tool"]
    )

    pyproject = (workdir / "pyproject.toml").read_text()
    assert 'description = "My Tool"' in pyproject


def test_init_description_stays_empty_when_flag_absent(workdir, app_env):
    """Without --description, non-interactive init still writes description = ''
    — no regression for users who do not pass the flag (spec consequence)."""
    env = app_env(workdir)

    env.meta(["init", "--binary", "http", "--dep", "httpie"])

    pyproject = (workdir / "pyproject.toml").read_text()
    assert 'description = ""' in pyproject


# -- dep-without-binary --------------------------------------------------------


def test_init_dep_without_binary_no_tty(workdir, monkeypatch, capsys, app_env):
    """--dep without --binary in non-interactive mode (no TTY) must say
    --binary is required, not the generic "needs a TTY" message."""
    import sys

    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    env = app_env(workdir)

    with pytest.raises(SystemExit) as exc_info:
        env.meta(["init", "--dep", "httpie"])

    assert exc_info.value.code == appenv.EXIT_CODE_USAGE
    err = capsys.readouterr().err
    assert "--binary" in err, f"should name --binary as required; got: {err!r}"
    assert "needs a TTY" not in err, (
        f"should not say 'needs a TTY' when --dep is provided; got: {err!r}"
    )
