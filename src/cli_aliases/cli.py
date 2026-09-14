"""Reusable Typer management subgroup: ``alias set|list|rm|path``."""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Set as AbstractSet

import typer
from rich.console import Console
from rich.table import Table

from cli_aliases.config import AliasConfig
from cli_aliases.core import (
    config_path,
    read_aliases,
    remove_alias,
    set_alias,
    validate_name,
)

console = Console()


def make_alias_app(
    cfg: AliasConfig, known_fn: Callable[[], AbstractSet[str]] | None = None
) -> typer.Typer:
    """A ready-made ``alias`` subgroup branded for the given tool.

    ``known_fn`` (when given) returns the tool's real command names; the
    ``set`` command then refuses alias names that would shadow a real command.
    """

    app = typer.Typer(
        name=cfg.command_name,
        context_settings={"help_option_names": ["-h", "--help"]},
        no_args_is_help=True,
        help=f"Manage git-style user-global {cfg.app_name} aliases "
        f"({cfg.filename}).",
    )

    @app.command("path")
    def path_cmd() -> None:
        """Print the resolved aliases config path."""
        path = config_path(cfg)
        console.print(path)
        if not path.is_file():
            console.print(
                f"[yellow]No aliases file yet - run "
                f"'{cfg.app_name} {cfg.command_name} set <name> <cmd...>' "
                "to create it.[/yellow]"
            )

    @app.command("list")
    def list_aliases() -> None:
        """Show every configured alias (name -> definition), sorted."""
        path = config_path(cfg)
        aliases = read_aliases(path)
        if not aliases:
            console.print(
                f"[yellow]No aliases configured in {path}. "
                f"Add one with '{cfg.app_name} {cfg.command_name} "
                "set <name> <cmd...>'.[/yellow]"
            )
            return
        table = Table(title=f"Aliases ({path})")
        table.add_column("name", style="bold")
        table.add_column("definition", overflow="fold")
        for name in sorted(aliases):
            table.add_row(name, aliases[name])
        console.print(table)

    @app.command("set")
    def set_cmd(
        name: str = typer.Argument(
            ..., help="Alias name (lowercase letters/digits/_/-)"
        ),
        parts: list[str] = typer.Argument(
            ..., help="The full command string the alias expands to"
        ),
    ) -> None:
        """Define or overwrite an alias: `<name> <cmd...>` (quote flag-bearing)."""
        if not parts:
            console.print(
                "[bold red]Error:[/bold red] missing the command string "
                f"({cfg.app_name} {cfg.command_name} set <name> <cmd...>)."
            )
            raise typer.Exit(code=1)
        error = validate_name(name)
        if error is not None:
            console.print(f"[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1)
        if known_fn is not None and name in known_fn():
            console.print(
                f"[bold red]Error:[/bold red] '{name}' is a real {cfg.app_name} "
                "command or subcommand and cannot be used as an alias name."
            )
            raise typer.Exit(code=1)
        definition = " ".join(parts)
        set_alias(cfg, name, definition)
        console.print(
            f"[green]alias '{name}' -> {definition!r} "
            f"(wrote {config_path(cfg)})[/green]"
        )

    @app.command("rm")
    def rm_cmd(name: str = typer.Argument(..., help="Alias name to remove")) -> None:
        """Remove an alias by name."""
        if not remove_alias(cfg, name):
            console.print(f"[bold red]Error:[/bold red] no alias named '{name}'.")
            raise typer.Exit(code=1)
        console.print(
            f"[green]removed alias '{name}' (from {config_path(cfg)})[/green]"
        )

    return app
