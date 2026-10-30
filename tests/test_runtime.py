"""cli_aliases.runtime — the per-tool adapter (built-ins + Typer tree)."""

from __future__ import annotations

from pathlib import Path

import pytest
import typer

from cli_aliases.config import AliasConfig
from cli_aliases.core import load_aliases, write_aliases
from cli_aliases.runtime import AliasRuntime

CFG = AliasConfig(app_name="tst", config_dir="tst", env_var="TST_ALIASES")


@pytest.fixture(autouse=True)
def _clear_alias_cache() -> None:
    load_aliases.cache_clear()
    yield
    load_aliases.cache_clear()


@pytest.fixture
def aliases_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "aliases.yaml"
    monkeypatch.setenv("TST_ALIASES", str(path))
    return path


def _app() -> typer.Typer:
    app = typer.Typer()

    @app.command("ls")
    def root_ls() -> None: ...

    registry = typer.Typer()

    @registry.command("list")
    def registry_list() -> None: ...

    @registry.command("config")
    def registry_config() -> None: ...

    app.add_typer(registry, name="registry")
    return app


def test_builtin_alias_expands_at_nested_position(aliases_path: Path) -> None:
    runtime = AliasRuntime(CFG, builtin={"ls": "list"})
    assert runtime.expand(["registry", "ls"], _app()) == ["registry", "list"]


def test_user_alias_overrides_builtin(aliases_path: Path) -> None:
    write_aliases(aliases_path, {"ls": "config"})
    runtime = AliasRuntime(CFG, builtin={"ls": "list"})
    assert runtime.expand(["registry", "ls"], _app()) == ["registry", "config"]


def test_real_root_command_wins_over_builtin(aliases_path: Path) -> None:
    runtime = AliasRuntime(CFG, builtin={"ls": "list"})
    assert runtime.expand(["ls"], _app()) == ["ls"]


def test_known_names_lists_the_whole_tree(aliases_path: Path) -> None:
    runtime = AliasRuntime(CFG)
    assert {"ls", "registry", "list", "config"} <= runtime.known_names(_app())
