"""cli_aliases.core — resolver, config paths, load/write round-trips."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli_aliases.config import AliasConfig
from cli_aliases.core import (
    _apply,
    config_path,
    load_aliases,
    merge_aliases,
    read_aliases,
    remove_alias,
    resolve_aliases,
    set_alias,
    validate_name,
    write_aliases,
)

CFG = AliasConfig(app_name="tst", config_dir="tst", env_var="TST_ALIASES")


@pytest.fixture(autouse=True)
def _clear_alias_cache() -> None:
    """load_aliases caches per AliasConfig; each test uses a temp file."""
    load_aliases.cache_clear()
    yield
    load_aliases.cache_clear()


@pytest.fixture
def aliases_path(tmp_path: Path) -> Path:
    return tmp_path / "aliases.yaml"


def _env(monkeypatch: pytest.MonkeyPatch, aliases_path: Path) -> None:
    monkeypatch.setenv("TST_ALIASES", str(aliases_path))


# ------------------------------------------------------------------ resolver


def test_resolve_plain_rewrite() -> None:
    aliases = {"o": "docs list --kind plan"}
    assert resolve_aliases(["o"], aliases=aliases) == ["docs", "list", "--kind", "plan"]


def test_resolve_appends_trailing_args() -> None:
    aliases = {"d": "dump"}
    assert resolve_aliases(["d", "--kind", "note"], aliases=aliases) == [
        "dump",
        "--kind",
        "note",
    ]


def test_resolve_dollar_insertion_and_all() -> None:
    aliases = {"c": "create --title $1 --priority $2", "a": "docs list $@"}
    assert resolve_aliases(["c", "Ship it", "high"], aliases=aliases) == [
        "create",
        "--title",
        "Ship it",
        "--priority",
        "high",
    ]
    assert resolve_aliases(["a", "x", "y"], aliases=aliases) == [
        "docs",
        "list",
        "x",
        "y",
    ]


def test_resolve_unset_placeholder_collapses() -> None:
    aliases = {"o": "docs list $1 extra"}
    assert resolve_aliases(["o"], aliases=aliases) == ["docs", "list", "extra"]


def test_resolve_real_command_wins_over_alias_key() -> None:
    aliases = {"sync": "dump", "o": "docs list"}
    assert resolve_aliases(["sync"], aliases=aliases, known={"sync"}) == ["sync"]
    assert resolve_aliases(["o"], aliases=aliases, known={"sync"}) == ["docs", "list"]


def test_resolve_unknown_token_passthrough() -> None:
    assert resolve_aliases(["nope"], aliases={"o": "docs list"}, known={"sync"}) == [
        "nope"
    ]
    assert resolve_aliases([], aliases={"o": "docs list"}) == []


def test_resolve_single_level_no_recursion() -> None:
    aliases = {"a": "b extra", "b": "docs list"}
    assert resolve_aliases(["a", "x"], aliases=aliases) == ["b", "extra", "x"]


def test_resolve_empty_definition_passthrough() -> None:
    assert resolve_aliases(["a"], aliases={"a": ""}) == []


def test_apply_quoted_definition_is_one_token() -> None:
    assert _apply('echo "two words"', []) == ["echo", "two words"]


def test_apply_leftover_extras_append_once() -> None:
    assert _apply("one $1", ["a", "b"]) == ["one", "a", "b"]


# --------------------------------------------------------------- name/config


@pytest.mark.parametrize("name", ["o", "st", "sync2", "f_1", "a-b", "0x"])
def test_validate_name_accepts(name: str) -> None:
    assert validate_name(name) is None


@pytest.mark.parametrize("name", ["", "-x", "x y", "X", "пустой", "a/b", "a.b"])
def test_validate_name_rejects(name: str) -> None:
    assert validate_name(name) is not None


def test_config_path_honors_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TST_ALIASES", "~/my/aliases.yaml")
    assert config_path(CFG) == Path.home() / "my/aliases.yaml"


def test_config_path_honors_xdg(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("TST_ALIASES", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    assert config_path(CFG) == tmp_path / "cfg" / "tst" / "aliases.yaml"


def test_config_path_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TST_ALIASES", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    assert config_path(CFG) == Path.home() / ".config" / "tst" / "aliases.yaml"


def test_resolved_env_var_defaults_to_app_name(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = AliasConfig(app_name="sb", config_dir="sb")
    assert cfg.resolved_env_var == "SB_ALIASES"
    assert (
        AliasConfig(
            app_name="ctx", config_dir="atlas", env_var="CTX_ALIASES"
        ).resolved_env_var
        == "CTX_ALIASES"
    )


def test_header_mentions_app_and_management_command() -> None:
    header = CFG.header()
    assert "tst aliases" in header
    assert "tst alias set" in header


def test_merge_aliases_user_wins() -> None:
    merged = merge_aliases({"md": "markdown", "convert": "conv"}, {"convert": "other"})
    assert merged == {"md": "markdown", "convert": "other"}


def test_merge_aliases_none_inputs() -> None:
    assert merge_aliases(None, None) == {}
    assert merge_aliases({"a": "b"}, None) == {"a": "b"}


# ------------------------------------------------------------------- load/rw


def test_load_aliases_valid_file(
    monkeypatch: pytest.MonkeyPatch, aliases_path: Path
) -> None:
    write_aliases(aliases_path, {"o": "docs list", "d": "dump"})
    _env(monkeypatch, aliases_path)
    assert load_aliases(CFG) == {"o": "docs list", "d": "dump"}


def test_load_aliases_malformed_yaml(
    monkeypatch: pytest.MonkeyPatch, aliases_path: Path
) -> None:
    aliases_path.write_text("aliases: [unclosed", encoding="utf-8")
    _env(monkeypatch, aliases_path)
    assert load_aliases(CFG) == {}


def test_load_aliases_missing_file(
    monkeypatch: pytest.MonkeyPatch, aliases_path: Path
) -> None:
    _env(monkeypatch, aliases_path)
    assert load_aliases(CFG) == {}


def test_load_aliases_ignores_non_string_entries(
    monkeypatch: pytest.MonkeyPatch, aliases_path: Path
) -> None:
    aliases_path.write_text("aliases:\n  o: docs list\n  n: 42\n", encoding="utf-8")
    _env(monkeypatch, aliases_path)
    assert load_aliases(CFG) == {"o": "docs list"}


def test_read_aliases_unknown_top_level_key_ignored(aliases_path: Path) -> None:
    aliases_path.write_text("aliases:\n  o: docs list\nother: 1\n", encoding="utf-8")
    assert read_aliases(aliases_path) == {"o": "docs list"}


def test_read_aliases_non_dict_root(aliases_path: Path) -> None:
    aliases_path.write_text("- a\n- b\n", encoding="utf-8")
    assert read_aliases(aliases_path) == {}


def test_write_aliases_atomic_no_partial_file_on_failure(aliases_path: Path) -> None:
    write_aliases(aliases_path, {"a": "b"})
    before = aliases_path.read_bytes()
    aliases_path.parent.chmod(0o500)  # make the temp-file write fail
    try:
        with pytest.raises(OSError):
            write_aliases(aliases_path, {"c": "d"})
    finally:
        aliases_path.parent.chmod(0o755)
    assert aliases_path.read_bytes() == before
    assert not list(aliases_path.parent.glob(f"{aliases_path.name}.*.tmp"))


def test_set_and_remove_alias_roundtrip(
    monkeypatch: pytest.MonkeyPatch, aliases_path: Path
) -> None:
    _env(monkeypatch, aliases_path)
    set_alias(CFG, "o", "docs list")
    set_alias(CFG, "d", "dump")
    assert read_aliases(aliases_path) == {"o": "docs list", "d": "dump"}
    set_alias(CFG, "o", "ticket list")
    assert read_aliases(aliases_path) == {"o": "ticket list", "d": "dump"}
    assert remove_alias(CFG, "o") is True
    assert remove_alias(CFG, "o") is False
    assert read_aliases(aliases_path) == {"d": "dump"}


def test_header_preserved_on_update(
    monkeypatch: pytest.MonkeyPatch, aliases_path: Path
) -> None:
    _env(monkeypatch, aliases_path)
    aliases_path.write_text(
        "# my custom header\n\naliases:\n  a: b\n", encoding="utf-8"
    )
    set_alias(CFG, "c", "d")
    text = aliases_path.read_text(encoding="utf-8")
    assert text.startswith("# my custom header")
    assert read_aliases(aliases_path) == {"a": "b", "c": "d"}


def test_set_alias_creates_parent_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target = tmp_path / "deep" / "nested" / "aliases.yaml"
    monkeypatch.setenv("TST_ALIASES", str(target))
    set_alias(CFG, "o", "docs list")
    assert target.is_file()
