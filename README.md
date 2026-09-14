# cli-aliases

Git-style user-global **pre-parse command aliases** for [Typer](https://typer.tiangolo.com/)
CLIs. Define shortcuts once in a YAML file (e.g. `~/.config/sb/aliases.yaml`) and they are
rewritten into real commands before Typer ever parses the command line — so aliases never
show up in `--help`, never collide with real commands, and work exactly like git aliases.

Extracted from the `ctx` (atlas) alias subsystem and shared with `sb` (super-bin).

## Features

- **Pre-parse argv rewriting** — single level, loop-proof, git-style.
- **Placeholder substitution** — `$1`, `$2`, … insert the Nth extra argument, `$@` all of
  them; leftover args append; unset placeholders collapse.
- **Real commands always win** — pass the app's command names as `known` and a real
  command/subcommand can never be shadowed.
- **Shipped + user aliases** — `merge_aliases()` layers user definitions over built-ins.
- **Ready-made management group** — `make_alias_app(cfg)` gives you
  `alias set|list|rm|path` with a `known_fn` reserved-name guard.
- **Generic Typer introspection** — `native_command_names(app)` walks groups and
  subgroups to build the `known` set (also usable as `known_fn`).
- **Safe file handling** — atomic writes (temp file + `os.replace`), header preservation,
  malformed files degrade to `{}` instead of crashing the CLI.

## Install

```bash
uv add cli-aliases
# or from git:
uv add "cli-aliases @ git+https://github.com/topdata-software-gmbh/cli-aliases.git@v0.1.0"
```

## Quick start

```python
import sys

import typer

from cli_aliases.cli import make_alias_app
from cli_aliases.config import AliasConfig
from cli_aliases.core import load_aliases, merge_aliases, resolve_aliases
from cli_aliases.names import native_command_names

CONFIG = AliasConfig(app_name="mytool", config_dir="mytool")

app = typer.Typer()

@app.command()
def deploy(target: str) -> None:
    """Deploy somewhere."""


def main() -> None:
    argv = sys.argv[1:]
    known = native_command_names(app)
    aliases = merge_aliases({"d": "deploy"}, load_aliases(CONFIG))
    sys.argv[1:] = resolve_aliases(argv, aliases=aliases, known=known)
    app()


app.add_typer(make_alias_app(CONFIG, known_fn=lambda: native_command_names(app)), name="alias")
```

Now:

```bash
mytool alias set prod "deploy production"   # user alias
mytool prod                                  # -> mytool deploy production
mytool d staging                             # built-in -> mytool deploy staging
```

## API

| Symbol | Purpose |
|---|---|
| `AliasConfig` | Frozen per-tool parameterization (`app_name`, `config_dir`, `filename`, `env_var`, `command_name`). |
| `config_path(cfg)` | Resolves the aliases file (`$<APP>_ALIASES` > `$XDG_CONFIG_HOME`/`~/.config` + `config_dir`). |
| `load_aliases(cfg)` / `read_aliases(path)` | Cached / direct read; never raises. |
| `merge_aliases(builtin, user)` | Layer user aliases over shipped ones. |
| `resolve_aliases(argv, aliases, known)` | The pre-parse rewrite. |
| `validate_name(name)` | Alias-name validation (lowercase letters/digits/`_`/`-`). |
| `set_alias` / `remove_alias` / `write_aliases` | File mutation (atomic, header-preserving). |
| `native_command_names(app)` | Typer tree introspection. |
| `make_alias_app(cfg, known_fn)` | Ready-made management subgroup. |

## Development

```bash
uv venv && uv pip install -e ".[dev]"
uv run pytest -q
uv run black --check . && uv run ruff check . && uv run mypy src
```

## License

MIT — see [LICENSE](LICENSE).
