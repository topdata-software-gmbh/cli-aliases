# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
