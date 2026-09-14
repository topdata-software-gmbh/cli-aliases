"""Introspect a Typer app's real command names (used as the ``known`` set)."""

from __future__ import annotations

from typing import Any


def native_command_names(app: Any) -> set[str]:
    """Every real name a user could type: root commands, group names, subgroups."""
    names: set[str] = set()

    def add_command(cmd: object) -> None:
        name = getattr(cmd, "name", None)
        if name:
            names.add(name)
            return
        callback = getattr(cmd, "callback", None)
        if callback is not None:
            names.add(callback.__name__.replace("_", "-"))

    def add_group(group: object) -> None:
        name = getattr(group, "name", None)
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
