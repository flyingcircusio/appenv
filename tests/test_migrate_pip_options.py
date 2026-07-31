# SPDX-FileCopyrightText: 2020 Flying Circus
"""Spec-driven tests for ``migrate`` handling pip-options in requirements.txt.

These tests are written before the
implementation: pip-options (``--index-url``, ``--extra-index-url``,
``--find-links``, ``--hash``, ``--trusted-host`` ...) currently leak into the
generated ``dependencies`` list as invalid PEP 508 specifiers, crashing
``uv lock``.

What is pinned (decided by the spec):
  * pip-options are separated from real dependencies and never written as deps.
  * ``--index-url`` / ``--extra-index-url`` become ``[[tool.uv.index]]`` entries.
   * embedded credentials are kept in pyproject.toml (so ``uv lock`` succeeds
     without manual env-var setup), but the user is warned with the exact
     ``UV_INDEX_<NAME>_USERNAME`` / ``_PASSWORD`` env var names and told to
     consider removing the credentials from the URL.
  * options without a pyproject equivalent (``--hash``, ``--no-binary``,
    ``--only-binary``, ``--require-hashes``) are dropped with a warning that
    lists the skipped options.

Deliberately NOT pinned (spec leaves open, so the implementer chooses):
   * how the index ``name`` is derived from the URL.
   * the exact stored URL representation when credentials are present.
     The security guarantee (no literal secret leak to stdout) and the
     env-var guidance are asserted. Credentials in pyproject.toml are an
     accepted trade-off — the warning tells the user to remove them.
"""

import re
from typing import NamedTuple

import pytest

import appenv


class MigrationOutput(NamedTuple):
    pyproject: str
    stdout: str
    stderr: str


_DEPENDENCIES_BLOCK = re.compile(r"dependencies\s*=\s*(\[.*?\])", re.S)
_INDEX_BLOCK = re.compile(r"\[\[tool\.uv\.index\]\]\s*\n(.*?)(?=\n\s*\[|\Z)", re.S)


def _extract_dependencies(pyproject_text):
    """Return the quoted entries of the ``[project] dependencies`` list."""
    block = _DEPENDENCIES_BLOCK.search(pyproject_text)
    if not block:
        return []
    return re.findall(r'"([^"]+)"', block.group(1))


def _extract_uv_indexes(pyproject_text):
    """Return ``[[tool.uv.index]]`` entries as ``{"name", "url"}`` dicts.

    ``name`` and ``url`` may appear in either order; both are optional in the
    regex so a missing field yields "" rather than a crash.
    """
    indexes: list[dict[str, str]] = []
    for block in _INDEX_BLOCK.findall(pyproject_text):
        name = re.search(r'^\s*name\s*=\s*"([^"]*)"', block, re.M)
        url = re.search(r'^\s*url\s*=\s*"([^"]*)"', block, re.M)
        indexes.append(
            {
                "name": name.group(1) if name else "",
                "url": url.group(1) if url else "",
            }
        )
    return indexes


def _index_env_token(index_name):
    """uv maps an index name to an env-var token: upper, non-alnum -> ``_``.

    Per https://docs.astral.sh/uv/concepts/indexes/#providing-credentials-directly
    ``UV_INDEX_<NAME>_USERNAME`` where ``<NAME>`` is the uppercased index name
    with non-alphanumeric characters replaced by underscores.
    """
    return re.sub(r"[^A-Z0-9]", "_", index_name.upper())


@pytest.fixture
def migrate_reqs(tmp_path, monkeypatch, capsys, app_env, mock_uv_lock):
    """Factory: write requirements.txt text into a clean dir and run migrate.

    Returns the generated ``pyproject.toml`` text and captured stdout/stderr.
    """

    def _run(requirements_text: str) -> MigrationOutput:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "requirements.txt").write_text(requirements_text)
        env = app_env(tmp_path)
        env.migrate()
        captured = capsys.readouterr()
        return MigrationOutput(
            (tmp_path / "pyproject.toml").read_text(),
            captured.out,
            captured.err,
        )

    return _run


# ============================================================================
# Baseline: no pip-options -> nothing changes, no spurious index entries.
# ============================================================================


def test_migrate_plain_dependencies_unchanged(migrate_reqs):
    """A requirements.txt without pip-options migrates as before."""
    result = migrate_reqs("requests\nflask\n")

    assert _extract_dependencies(result.pyproject) == ["requests", "flask"]
    assert _extract_uv_indexes(result.pyproject) == []


# ============================================================================
# Separation: pip-options never become dependencies (the core bug fix).
# ============================================================================


def test_parse_requirements_separates_pip_options(tmp_path):
    """_parse_requirements_file separates pip-options from real dependencies."""
    (tmp_path / "requirements.txt").write_text(
        "--extra-index-url https://gitlab.example.com/simple\n"
        "requests --hash=sha256:abc123\n"
        "flask\n"
    )

    pyproject = appenv.Pyproject(tmp_path)
    deps = pyproject.requirements_txt_info.dependencies

    assert deps == ["requests", "flask"]
    assert not any(dep.startswith("-") for dep in deps)
    assert not any("--hash" in dep for dep in deps)


def test_migrate_separates_extra_index_url_from_dependencies(migrate_reqs):
    """--extra-index-url is not written into the dependencies list."""
    result = migrate_reqs(
        "--extra-index-url https://gitlab.example.com/api/v4/projects/42"
        "/packages/pypi/simple\n"
        "requests\n"
    )

    deps = _extract_dependencies(result.pyproject)
    assert deps == ["requests"]
    assert not any("index-url" in dep for dep in deps)
    assert not any(dep.startswith("-") for dep in deps)


def test_migrate_converts_index_url_to_uv_index_entry(migrate_reqs):
    """--index-url becomes a [[tool.uv.index]] entry with name and url."""
    result = migrate_reqs("--index-url https://download.pytorch.org/whl/cpu\ntorch\n")

    assert _extract_dependencies(result.pyproject) == ["torch"]

    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 1
    assert indexes[0]["name"]  # a name is required for env-var auth
    assert indexes[0]["url"] == "https://download.pytorch.org/whl/cpu"


def test_migrate_assigns_distinct_names_to_multiple_indexes(migrate_reqs):
    """Two different extra-index-urls yield two distinct named index entries."""
    result = migrate_reqs(
        "--extra-index-url https://gitlab.example.com/simple\n"
        "--extra-index-url https://artifacts.example.com/simple\n"
        "requests\n"
    )

    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 2

    names = [idx["name"] for idx in indexes]
    assert len(set(names)) == 2  # names must not collide

    urls = [idx["url"] for idx in indexes]
    assert any("gitlab.example.com" in u for u in urls)
    assert any("artifacts.example.com" in u for u in urls)

    assert _extract_dependencies(result.pyproject) == ["requests"]


# ============================================================================
# Credentials: kept in pyproject (so uv lock works), warned to stdout.
# ============================================================================


def test_migrate_keeps_credentials_in_pyproject_and_warns_env_vars(
    migrate_reqs, patterns
):
    """Credentialed index URL: the secret IS kept in pyproject.toml (so ``uv
    lock`` works without manual env-var setup), but the user is warned with
    the exact ``UV_INDEX_<NAME>_USERNAME`` / ``_PASSWORD`` names and instructed
    to consider removing credentials from the URL.

    Security contract: no literal secret leak to stdout (pyproject.toml is the
    accepted trade-off — the warning tells the user to fix it).
    """
    result = migrate_reqs(
        "--extra-index-url https://deploy:s3cr3t@gitlab.example.com/simple\nrequests\n"
    )

    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 1
    assert "gitlab.example.com" in indexes[0]["url"]

    # Secret is in pyproject.toml so uv lock can authenticate.
    assert "s3cr3t" in result.pyproject

    # UX: the exact derived env-var token is advertised for each credentialed index.
    for idx in indexes:
        token = _index_env_token(idx["name"])
        assert f"UV_INDEX_{token}_USERNAME" in result.stdout
        assert f"UV_INDEX_{token}_PASSWORD" in result.stdout

    # Structural: env-var guidance appears in order; the secret never leaks to stdout.
    patterns.main.in_order("...UV_INDEX_..._USERNAME...UV_INDEX_..._PASSWORD...")
    patterns.no_errors.optional("...")
    patterns.no_errors.refused("...s3cr3t...")
    full = patterns.full
    full.merge("main", "no_errors")
    assert full == result.stdout


def test_migrate_skips_credential_warning_for_public_index(migrate_reqs):
    """A credential-free index needs no UV_INDEX_*_USERNAME/_PASSWORD warning."""
    result = migrate_reqs("--extra-index-url https://pypi.org/simple\nrequests\n")

    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 1
    assert "pypi.org" in indexes[0]["url"]

    assert "USERNAME" not in result.stdout
    assert "PASSWORD" not in result.stdout


# ============================================================================
# Unsupported options: dropped (not deps) + warning lists what was skipped.
# ============================================================================


@pytest.mark.parametrize(
    "requirements_text,expected_deps,skipped_option",
    [
        # --hash riding on the same line as a requirement.
        (
            "requests --hash=sha256:abc123\n",
            ["requests"],
            "--hash",
        ),
        # Multiple --hash on one pinned requirement.
        (
            "requests==2.31.0 --hash=sha256:aaa --hash=sha256:bbb\n",
            ["requests==2.31.0"],
            "--hash",
        ),
        # Standalone --require-hashes flag.
        (
            "--require-hashes\nrequests\n",
            ["requests"],
            "--require-hashes",
        ),
        # --no-binary / --only-binary have no pyproject equivalent.
        (
            "--no-binary :all:\nrequests\n",
            ["requests"],
            "--no-binary",
        ),
        (
            "--only-binary :all:\nrequests\n",
            ["requests"],
            "--only-binary",
        ),
    ],
)
def test_migrate_drops_unsupported_pip_option(
    requirements_text, expected_deps, skipped_option, migrate_reqs
):
    """Options without a pyproject equivalent are dropped, not turned into deps."""
    result = migrate_reqs(requirements_text)

    assert _extract_dependencies(result.pyproject) == expected_deps
    assert not any(
        dep.startswith("-") for dep in _extract_dependencies(result.pyproject)
    )

    # The spec requires the dropped option to be reported to the user.
    assert skipped_option in result.stdout


def test_migrate_warns_lists_all_skipped_pip_options(migrate_reqs):
    """When several unsupported options appear, all are listed in the warning."""
    result = migrate_reqs(
        "--require-hashes\n--no-binary :all:\nrequests --hash=sha256:deadbeef\nflask\n"
    )

    assert _extract_dependencies(result.pyproject) == ["requests", "flask"]
    assert "--require-hashes" in result.stdout
    assert "--no-binary" in result.stdout
    assert "--hash" in result.stdout


# ============================================================================
# Headline scenario: a realistic private-registry requirements.txt end-to-end.
# This is exactly the project profile the spec says migration must unblock.
# ============================================================================


def test_migrate_gitlab_private_registry_end_to_end(migrate_reqs):
    """A GitLab Package Registry requirements.txt migrates cleanly.

    Credentials are kept in pyproject (so uv lock works) but not in stdout;
    the user is warned to replace them with env vars.
    """
    result = migrate_reqs(
        "--extra-index-url https://deploy:s3cr3t@gitlab.example.com/api/v4/"
        "projects/42/packages/pypi/simple\n"
        "--require-hashes\n"
        "internal-pkg==1.0.0 --hash=sha256:deadbeef\n"
        "requests\n"
    )

    # Real dependencies survive, options do not.
    assert _extract_dependencies(result.pyproject) == [
        "internal-pkg==1.0.0",
        "requests",
    ]

    # Index entry created, host preserved, secret kept in pyproject (so uv
    # lock works), not leaked to stdout.
    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 1
    assert (
        "gitlab.example.com/api/v4/projects/42/packages/pypi/simple"
        in indexes[0]["url"]
    )
    assert "s3cr3t" not in result.stdout

    # Credential env-var guidance + skipped-option warnings are emitted.
    token = _index_env_token(indexes[0]["name"])
    assert f"UV_INDEX_{token}_USERNAME" in result.stdout
    assert f"UV_INDEX_{token}_PASSWORD" in result.stdout
    assert "--require-hashes" in result.stdout
    assert "--hash" in result.stdout

    assert "Migration completed" in result.stdout


# ============================================================================
# Validity: the generated pyproject.toml must parse as TOML.
# The original bug produced *invalid* TOML that crashed uv lock.
# ============================================================================


def test_migrate_writes_valid_toml_with_pip_options(migrate_reqs):
    """Generated pyproject.toml containing pip-options is valid TOML."""
    tomllib = pytest.importorskip("tomllib")  # Python <3.11 has no tomllib

    result = migrate_reqs(
        "--extra-index-url https://gitlab.example.com/simple\n"
        "requests --hash=sha256:abc123\n"
    )

    data = tomllib.loads(result.pyproject)  # raises on invalid TOML
    assert "project" in data
    assert data["project"]["dependencies"] == ["requests"]


# ============================================================================
# Edge branches in the migrate-pip-options helpers (coverage gap closure).
# Each test pins the observable behavior of one previously-uncovered branch
# in _index_name_from_url / _build_index_entries / _consume_next_value /
# _apply_pip_option. No mocks of the functions under test — all paths are
# driven through the public ``migrate`` API.
# ============================================================================


def test_migrate_assigns_numeric_suffix_when_index_hosts_collide(migrate_reqs):
    """Two index URLs sharing a host get distinct numeric-suffixed names.

    Drives the collision-disambiguation loop: the second URL derives the same
    base name as the first, so it must be suffixed (``<base>-2``) rather than
    silently shadowing the first ``[[tool.uv.index]]`` entry.
    """
    result = migrate_reqs(
        "--extra-index-url https://gitlab.example.com/api/v4/projects/42"
        "/packages/pypi/simple\n"
        "--extra-index-url https://gitlab.example.com/api/v4/projects/43"
        "/packages/pypi/simple\n"
        "requests\n"
    )

    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 2

    names = [idx["name"] for idx in indexes]
    assert len(set(names)) == 2  # no shadowing
    assert any(name.endswith("-2") for name in names)  # numeric suffix applied

    # Both distinct URLs survive (they differ in path, so neither is deduped).
    urls = [idx["url"] for idx in indexes]
    assert any("projects/42" in u for u in urls)
    assert any("projects/43" in u for u in urls)

    assert _extract_dependencies(result.pyproject) == ["requests"]


def test_migrate_dedups_repeated_identical_index_url(migrate_reqs):
    """Two identical --extra-index-url lines collapse to a single index entry.

    Drives the de-duplication ``continue`` branch: a URL already seen (the
    dedup key is the credential-free ``url``) is not emitted a second time,
    matching pip's own de-duplication of repeated ``--extra-index-url`` lines.
    """
    result = migrate_reqs(
        "--extra-index-url https://gitlab.example.com/simple\n"
        "--extra-index-url https://gitlab.example.com/simple\n"
        "requests\n"
    )

    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 1
    assert "gitlab.example.com" in indexes[0]["url"]

    assert _extract_dependencies(result.pyproject) == ["requests"]


def test_migrate_index_url_without_value_creates_no_index(migrate_reqs):
    """A bare ``--index-url`` with no following value creates no index entry.

    Drives the ``_consume_next_value`` end-of-tokens guard (no value to
    consume) and the falsy-``url`` branch in ``_apply_pip_option``: with no
    URL, nothing is appended. The option is silently dropped rather than
    crashing or emitting a malformed empty index.
    """
    result = migrate_reqs("--index-url\nrequests\n")

    assert _extract_uv_indexes(result.pyproject) == []
    assert _extract_dependencies(result.pyproject) == ["requests"]


def test_migrate_index_url_inline_equals_form_creates_entry(migrate_reqs):
    """``--index-url=URL`` inline form creates an index entry without consuming
    the next token.

    Drives the truthy-inline branch: when the value is attached with ``=``,
    ``_apply_pip_option`` uses it directly and skips the
    ``_consume_next_value`` call entirely.
    """
    result = migrate_reqs("--index-url=https://download.pytorch.org/whl/cpu\ntorch\n")

    indexes = _extract_uv_indexes(result.pyproject)
    assert len(indexes) == 1
    assert indexes[0]["url"] == "https://download.pytorch.org/whl/cpu"
    assert indexes[0]["name"]

    assert _extract_dependencies(result.pyproject) == ["torch"]


def test_migrate_skips_unknown_option_followed_by_another_option(migrate_reqs):
    """An unrecognized option is dropped; its would-be value — when that value
    is itself an option token — is NOT consumed and is parsed on its own.

    Drives the unknown-option branch and the ``_consume_next_value`` guard that
    refuses to eat a following ``-``-prefixed token as a value. Observable
    proof the guard fired: the following option (``--require-hashes``) is
    reported as its own skipped option rather than vanishing as the unknown
    option's value.
    """
    result = migrate_reqs("--global-option --require-hashes\nrequests\n")

    assert _extract_dependencies(result.pyproject) == ["requests"]
    assert _extract_uv_indexes(result.pyproject) == []

    # The unknown option is reported as skipped...
    assert "--global-option" in result.stdout
    # ...and so is the option that followed it (it was not eaten as a value).
    assert "--require-hashes" in result.stdout


def test_migrate_skips_unknown_option_with_inline_value(migrate_reqs):
    """An unrecognized option given as ``--opt=value`` is dropped without
    consuming the next token.

    Drives the inline-value branch of the unknown-option path: with an inline
    value present, ``_consume_next_value`` is not invoked, so the following
    requirement is preserved.
    """
    result = migrate_reqs("--global-option=build_ext\nrequests\n")

    assert _extract_dependencies(result.pyproject) == ["requests"]
    assert "--global-option" in result.stdout
