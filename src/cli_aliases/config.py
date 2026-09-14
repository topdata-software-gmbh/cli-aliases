"""Tool-specific configuration for the git-style CLI alias subsystem."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AliasConfig:
    """Parameterize the alias subsystem for one CLI application.

    One frozen instance per CLI tool (e.g. ``sb``, ``ctx``). Every public
    function in :mod:`cli_aliases` takes it, so no tool-specific naming leaks
    into the shared code (open/closed: new tools only add a config object).
    """

    #: Short tool name used in headers, help text and messages ("sb", "ctx").
    app_name: str
    #: Directory under ``$XDG_CONFIG_HOME`` (or ``~/.config``) holding the file.
    config_dir: str
    #: Aliases filename inside *config_dir* — kept explicit so historical
    #: names like ``ctx-aliases.yaml`` stay loadable.
    filename: str = "aliases.yaml"
    #: Path-override env var; defaults to ``{APP}_ALIASES``.
    env_var: str | None = None
    #: Name of the management subgroup ("alias" for both consumers today).
    command_name: str = "alias"

    @property
    def resolved_env_var(self) -> str:
        return self.env_var or f"{self.app_name.upper()}_ALIASES"

    def header(self) -> str:
        return (
            f"# {self.app_name} aliases - git-style pre-parse command rewrites.\n"
            f"# Managed with: {self.app_name} {self.command_name} "
            "set <name> <cmd...> | list | rm <name> | path\n"
        )
