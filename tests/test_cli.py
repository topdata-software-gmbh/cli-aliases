"""cli_aliases.cli — the ready-made `alias set|list|rm|path` management group."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli_aliases.cli import make_alias_app
from cli_aliases.config import AliasConfig
from cli_aliases.core import read_aliases

runner = CliRunner()

CFG = AliasConfig(app_name="tst", config_dir="tst", env_var="TST_ALIASES")


@pytest.fixture
def aliases_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "aliases.yaml"
    monkeypatch.setenv("TST_ALIASES", str(path))
    return path


@pytest.fixture
def app():
    return make_alias_app(CFG)


def test_set_creates_file_with_header(app, aliases_path: Path) -> None:
    result = runner.invoke(app, ["set", "o", "docs list"])
    assert result.exit_code == 0
    text = aliases_path.read_text(encoding="utf-8")
    assert text.startswith("# tst aliases")
    assert read_aliases(aliases_path) == {"o": "docs list"}


def test_set_edits_one_key_preserving_others(app, aliases_path: Path) -> None:
    assert runner.invoke(app, ["set", "o", "docs list"]).exit_code == 0
    assert runner.invoke(app, ["set", "d", "dump"]).exit_code == 0
    result = runner.invoke(app, ["set", "o", "ticket list"])
    assert result.exit_code == 0
    assert read_aliases(aliases_path) == {"o": "ticket list", "d": "dump"}


def test_set_joins_multiple_definition_parts(app, aliases_path: Path) -> None:
    result = runner.invoke(app, ["set", "docs-pdf", "markdown", "pdf", "$1"])
    assert result.exit_code == 0
    assert read_aliases(aliases_path) == {"docs-pdf": "markdown pdf $1"}


def test_set_refuses_real_command_collision(aliases_path: Path) -> None:
    app = make_alias_app(CFG, known_fn=lambda: {"sync", "inbox"})
    result = runner.invoke(app, ["set", "sync", "dump"])
    assert result.exit_code == 1
    assert "real tst command" in result.output
    assert not aliases_path.exists()


def test_set_allows_name_when_no_known_fn(app, aliases_path: Path) -> None:
    result = runner.invoke(app, ["set", "sync", "dump"])
    assert result.exit_code == 0
    assert read_aliases(aliases_path) == {"sync": "dump"}


def test_set_refuses_invalid_name(app, aliases_path: Path) -> None:
    result = runner.invoke(app, ["set", "X-y", "dump"])
    assert result.exit_code == 1
    assert "invalid" in result.output
    assert not aliases_path.exists()


def test_set_missing_definition_is_an_error(app, aliases_path: Path) -> None:
    result = runner.invoke(app, ["set", "o"])
    assert result.exit_code != 0
    assert not aliases_path.exists()


def test_list_shows_entries_sorted(app, aliases_path: Path) -> None:
    runner.invoke(app, ["set", "z", "dump"])
    runner.invoke(app, ["set", "a", "docs list"])
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert result.output.index("a") < result.output.index("z")


def test_list_empty_hint(app) -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No aliases configured" in result.output


def test_rm_removes_one_key(app, aliases_path: Path) -> None:
    runner.invoke(app, ["set", "o", "dump"])
    runner.invoke(app, ["set", "d", "dump"])
    result = runner.invoke(app, ["rm", "o"])
    assert result.exit_code == 0
    assert read_aliases(aliases_path) == {"d": "dump"}


def test_rm_missing_name_errors(app) -> None:
    result = runner.invoke(app, ["rm", "o"])
    assert result.exit_code == 1
    assert "no alias named" in result.output


def test_path_prints_resolved_path_and_hint(app, aliases_path: Path) -> None:
    result = runner.invoke(app, ["path"])
    assert result.exit_code == 0
    assert str(aliases_path) in result.output
    assert "tst alias set" in result.output


def test_bare_group_shows_help(app) -> None:
    result = runner.invoke(app, [])
    assert result.exit_code != 0 or "Usage" in result.output
    assert "Usage" in result.output
