# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.2.0] - 2026-04-03

### Added

- Add bidirectional sync with Claude Code native MEMORY.md system (`/amnesia sync`).
- Add `scripts/native_memory.py` for read-only native memory integration: path resolution, YAML frontmatter parsing, entity filtering, and sync report generation.
- Add JSON Schema at `schemas/amnesia-entity.schema.json` with `$schema` URL pointing to raw GitHub for editor validation.
- Add `argument-hint` frontmatter field for CLI autocomplete hints in commands.
- Add "Why Amnesia?" section to README with competitive comparison table covering 12 other memory plugins.
- Add plugin installation instructions from GitHub marketplace to README.

### Changed

- Unify save flow: `/amnesia save` now writes both entity memory and session log in a single command.
- Remove separate `/amnesia project` command — session save is always part of the unified flow.
- Update `$schema` field from string identifier to full GitHub raw URL for editor validation.

### Fixed

- Fix `--project-root` flag parsing in any argument position using `argparse.SUPPRESS` on subparsers.

---

## [0.1.0] - 2026-04-03

### Added

- Add Python CLI (`scripts/amnesia.py`) with deterministic entity and project memory operations.
- Add core modules: schema validation (Pydantic v2), merge/dedup engine, path resolution, and language detection.
- Add entity operations: load, save, diff, and list with structured JSON output.
- Add project session operations: load with git log integration, save with daily session logs.
- Add automatic schema migration from `etl-client-memory-v1` to `amnesia-entity` on read.
- Add thin `.md` command wrappers for `/amnesia`, `/amnesia entity`, and `/amnesia project`.
- Add Claude Code plugin manifest (`.claude-plugin/plugin.json` and `marketplace.json`).
- Add comprehensive test suite with 41 unit and integration tests.

### Changed

- Replace example entity name from domain-specific to generic `my-project` across docs and tests.

### Fixed

- Fix `marketplace.json` and `plugin.json` schemas to match Claude Code plugin specification.

