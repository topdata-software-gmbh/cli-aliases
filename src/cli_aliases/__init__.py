"""Git-style user-global command aliases for Typer CLIs."""

from cli_aliases.config import AliasConfig
from cli_aliases.core import resolve_aliases

__all__ = ["AliasConfig", "resolve_aliases"]
