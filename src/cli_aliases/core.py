"""Git-style user-global command aliases — pure logic, no framework.

Aliases are pre-parse argv rewrites defined in
``{XDG_CONFIG_HOME|~/.config}/{AliasConfig.config_dir}/{AliasConfig.filename}``
(override with ``AliasConfig.resolved_env_var``). :func:`resolve_aliases`
expands a single level before the CLI parses the command line, so aliases
are never registered commands and stay invisible to ``--help``.
"""

from __future__ import annotations

import os
import re
import shlex
import tempfile
from collections.abc import Mapping
from collections.abc import Set as AbstractSet
from functools import lru_cache
from pathlib import Path

import yaml

from cli_aliases.config import AliasConfig

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]*$")


def config_path(cfg: AliasConfig) -> Path:
    """Resolve the aliases file honoring env override + XDG_CONFIG_HOME."""
    env = os.getenv(cfg.resolved_env_var)
    if env:
        return Path(env).expanduser()
    base = Path(os.getenv("XDG_CONFIG_HOME", "~/.config")).expanduser()
    return base / cfg.config_dir / cfg.filename


@lru_cache(maxsize=4)
def load_aliases(cfg: AliasConfig) -> dict[str, str]:
    """Read the aliases map for *cfg*; never raises (broken file -> {})."""
    return read_aliases(config_path(cfg))


def read_aliases(path: Path) -> dict[str, str]:
    """Path-parameterized read; never raises, returns {} on any problem."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError, UnicodeDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    raw = data.get("aliases")
    if not isinstance(raw, dict):
        return {}
    return {
        str(k): str(v)
        for k, v in raw.items()
        if isinstance(k, str) and isinstance(v, str)
    }


def merge_aliases(
    builtin: Mapping[str, str] | None, user: Mapping[str, str] | None
) -> dict[str, str]:
    """Layer user aliases over shipped ones (user keys win)."""
    out = dict(builtin or {})
    out.update(user or {})
    return out


def resolve_aliases(
    argv: list[str],
    aliases: Mapping[str, str] | None = None,
    known: AbstractSet[str] | None = None,
) -> list[str]:
    """Rewrite CLI argv (excluding the program name) via aliases, git-style.

    - ``argv[0]`` in ``known`` (a real command/subcommand) -> unchanged.
    - ``argv[0]`` in ``aliases`` -> substitute the definition + extra args.
    - otherwise -> unchanged, the CLI reports the unknown command normally.

    Expansion is single-level only: the substituted definition is parsed once
    and never re-resolved (loop-proof, matches git).
    """
    if not argv:
        return argv
    if known is None:
        known = frozenset()
    if argv[0] in known:
        return argv
    aliases = aliases or {}
    definition = aliases.get(argv[0])
    if definition is None:
        return argv
    return _apply(definition, argv[1:])


def _apply(definition: str, extras: list[str]) -> list[str]:
    """Substitute ``$1``/``$2``/.../``$@`` placeholders in a definition.

    ``$N`` inserts the Nth extra arg, ``$@`` all extras; leftover extras
    append to the end; unset placeholders collapse to nothing (git behavior).
    """
    tokens = shlex.split(definition)
    used: set[int] = set()
    out: list[str] = []
    for token in tokens:
        if token == "$@":
            out.extend(extras)
            used.update(range(len(extras)))
        elif token.startswith("$") and token[1:2].isdigit():
            index = int(token[1:]) - 1
            if 0 <= index < len(extras):
                out.append(extras[index])
                used.add(index)
        else:
            out.append(token)
    out.extend(item for index, item in enumerate(extras) if index not in used)
    return out


def validate_name(name: str) -> str | None:
    """``None`` when *name* is a valid alias name, else an error string."""
    if not name:
        return "alias name must not be empty"
    if not _NAME_RE.fullmatch(name):
        return (
            f"alias name {name!r} is invalid: use only lowercase letters, "
            "digits, '-' and '_', starting with a letter or digit."
        )
    return None


def write_aliases(
    path: Path, aliases: Mapping[str, str], header: str | None = None
) -> None:
    """Atomically write the aliases map (temp file + os.replace)."""
    text = ""
    if header:
        text = header.rstrip() + "\n\n"
    text += yaml.safe_dump(
        {"aliases": dict(aliases)}, sort_keys=True, allow_unicode=True
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=f"{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def set_alias(cfg: AliasConfig, name: str, definition: str) -> None:
    """Create the file (with the header) or edit one key of the tool's map."""
    path = config_path(cfg)
    header = _existing_header(path) or cfg.header()
    aliases = read_aliases(path)
    aliases[name] = definition
    write_aliases(path, aliases, header=header)


def remove_alias(cfg: AliasConfig, name: str) -> bool:
    """Remove one alias key; False when the name is unknown."""
    path = config_path(cfg)
    aliases = read_aliases(path)
    if name not in aliases:
        return False
    del aliases[name]
    write_aliases(path, aliases, header=_existing_header(path))
    return True


def _existing_header(path: Path) -> str | None:
    """The leading ``#``-comment block of an existing file, or None."""
    if not path.is_file():
        return None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None
    comments: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if comments:
                comments.append("")
            continue
        if stripped.startswith("#"):
            comments.append(line)
        else:
            break
    while comments and comments[-1] == "":
        comments.pop()
    return "\n".join(comments) + "\n" if comments else None
