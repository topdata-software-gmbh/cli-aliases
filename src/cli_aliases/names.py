"""Introspect a Typer app's command tree (used by the alias resolvers)."""

from __future__ import annotations

from typing import Any

#: Nested command tree: name -> subtree. A leaf command maps to ``{}``.
type CommandTree = dict[str, CommandTree]


def _command_name(cmd: object) -> str | None:
    """A command's registered name, falling back to its callback name."""
    name = getattr(cmd, "name", None)
    if name:
        return str(name)
    callback = getattr(cmd, "callback", None)
    if callback is not None:
        return str(callback.__name__.replace("_", "-"))
    return None


def _group_name(group: object) -> str | None:
    name = getattr(group, "name", None)
    return str(name) if name else None


def _group_tree(group: object) -> CommandTree:
    node: CommandTree = {}
    sub = getattr(group, "typer_instance", None)
    if sub is None:
        return node
    for cmd in getattr(sub, "registered_commands", ()):
        name = _command_name(cmd)
        if name:
            node[name] = {}
    for nested in getattr(sub, "registered_groups", ()):
        name = _group_name(nested)
        if name:
            node[name] = _group_tree(nested)
    return node


def command_tree(app: Any) -> CommandTree:
    """Nested tree of real commands/groups (leaves map to ``{}``).

    Used by :func:`cli_aliases.core.resolve_nested_aliases` to know which
    argv positions are command positions, so subcommand aliases work without
    ever rewriting a positional argument.
    """
    tree: CommandTree = {}
    for cmd in getattr(app, "registered_commands", ()):
        name = _command_name(cmd)
        if name:
            tree[name] = {}
    for group in getattr(app, "registered_groups", ()):
        name = _group_name(group)
        if name:
            tree[name] = _group_tree(group)
    return tree


def native_command_names(app: Any) -> set[str]:
    """Every real name a user could type: root commands, group names, subgroups."""
    names: set[str] = set()

    def add_command(cmd: object) -> None:
        name = _command_name(cmd)
        if name:
            names.add(name)

    def add_group(group: object) -> None:
        name = _group_name(group)
        if name:
            names.add(name)
        sub = getattr(group, "typer_instance", None)
        if sub is None:
            return
        for cmd in getattr(sub, "registered_commands", ()):
            add_command(cmd)
        for nested in getattr(sub, "registered_groups", ()):
            add_group(nested)

    for cmd in getattr(app, "registered_commands", ()):
        add_command(cmd)
    for group in getattr(app, "registered_groups", ()):
        add_group(group)
    return names
