"""cli_aliases.names — Typer command-tree introspection."""

from __future__ import annotations

import typer

from cli_aliases.names import native_command_names


def _app() -> typer.Typer:
    root = typer.Typer()

    @root.command()
    def flat() -> None:
        """A command whose runtime name derives from the function name."""

    @root.command(name="explicit")
    def with_explicit_name() -> None:
        """A command with an explicit name."""

    group = typer.Typer()

    @group.command()
    def sub() -> None:
        """A first-level subcommand."""

    nested = typer.Typer()

    @nested.command()
    def deep() -> None:
        """A second-level subcommand."""

    group.add_typer(nested, name="nested")
    root.add_typer(group, name="grp")
    return root


def test_collects_root_commands_and_groups() -> None:
    names = native_command_names(_app())
    assert {"flat", "explicit", "grp", "sub", "nested", "deep"} <= names


def test_skips_the_root_itself() -> None:
    assert native_command_names(_app())  # non-empty
    assert native_command_names(typer.Typer()) == set()
