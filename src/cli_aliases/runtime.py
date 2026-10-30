"""Per-tool alias adapter: bind an :class:`AliasConfig` to a Typer app.

The thin ``CONFIG + expand + introspect`` wrapper that every consumer used to
copy is provided once here. A consumer keeps only its ``AliasConfig`` line and
optionally a map of built-in aliases; user aliases in the YAML file win.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from cli_aliases.config import AliasConfig
from cli_aliases.core import load_aliases, merge_aliases, resolve_nested_aliases
from cli_aliases.names import CommandTree, command_tree, native_command_names


@dataclass(frozen=True)
class AliasRuntime:
    """User (and optional built-in) aliases plus Typer tree introspection."""

    config: AliasConfig
    builtin: Mapping[str, str] = field(default_factory=dict)

    def aliases(self) -> dict[str, str]:
        """Built-in aliases layered under the user's YAML file."""
        return merge_aliases(self.builtin, load_aliases(self.config))

    def tree(self, app: Any) -> CommandTree:
        """The nested command tree of *app*."""
        return command_tree(app)

    def known_names(self, app: Any) -> set[str]:
        """Every real command/subcommand name of *app*."""
        return native_command_names(app)

    def expand(self, argv: list[str], app: Any) -> list[str]:
        """Rewrite *argv* using the aliases and *app*'s command tree."""
        return resolve_nested_aliases(argv, aliases=self.aliases(), tree=self.tree(app))
