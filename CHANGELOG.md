# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-30

### Added
- `command_tree()` — nested Typer command tree (groups vs. leaf commands),
  complementing the flat `native_command_names()`.
- `resolve_nested_aliases()` — command-position-aware rewriting, so aliases
  work for subcommands too (e.g. `registry ls` when `list` is the real
  command) without ever rewriting positional arguments. Alias chains resolve
  with a cycle guard; scanning stops at options, `--`, and leaf commands.
- `AliasRuntime` (`cli_aliases.runtime`) — the reusable per-tool adapter that
  binds an `AliasConfig` (and optional built-in aliases) to a Typer app,
  replacing the near-identical `CONFIG + expand + introspect` wrapper that
  consumers used to copy.

## [0.1.1] - 2026-09-14

### Added
- `py.typed` marker (PEP 561) so downstream consumers type-check the library
  with mypy instead of treating it as untyped.

## [0.1.0] - 2026-09-14

### Added
- `AliasConfig` — frozen per-tool parameterization (`app_name`, `config_dir`,
  `filename`, `env_var`, `command_name`, generated header).
- `cli_aliases.core` — pure logic: `config_path`, `load_aliases`, `read_aliases`,
  `merge_aliases`, `resolve_aliases` (single-level `$N`/`$@` substitution,
  known-set guard), `validate_name`, atomic `write_aliases`, `set_alias`,
  `remove_alias`, header preservation.
- `cli_aliases.names.native_command_names()` — recursive Typer command-tree
  introspection (root commands, groups, nested subgroups).
- `cli_aliases.cli.make_alias_app()` — ready-made `alias set|list|rm|path`
  management subgroup with an optional `known_fn` reserved-name guard.
- Extracted from the `ctx` (atlas) alias subsystem so `ctx` and `sb` share one
  implementation.
