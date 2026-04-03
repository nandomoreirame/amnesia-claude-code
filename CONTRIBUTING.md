# Contributing to Amnesia Claude Code Plugin

Thank you for your interest in contributing. This document describes the development workflow, conventions, and process for submitting changes.

## Dev Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd amnesia-claude-code
```

1. Install dependencies (no virtualenv required):

```bash
pip install pydantic pytest
```

No build step is needed. The CLI (`scripts/amnesia.py`) runs directly with Python.

## Running Tests

Run the full test suite:

```bash
python -m pytest tests/ -v
```

Run only integration tests:

```bash
python -m pytest tests/test_integration.py -v
```

Run with coverage:

```bash
python -m pytest tests/ --cov=scripts --cov-report=term-missing
```

## Code Conventions

### Always output structured JSON

`amnesia.py` and all functions it delegates to must **never** produce plain text. All output follows this envelope:

```json
{"data": <result>, "error": null}
```

On error:

```json
{"data": null, "error": "<error_code>", "file": "<optional_path>"}
```

This ensures Claude can process CLI output reliably without ambiguity.

### TDD is required

Write the failing test first, verify it fails, then write the minimal implementation to make it pass.

### Pydantic v2 for schema validation

All entity/project models use Pydantic v2. Do not use v1-style validators.

### No external dependencies beyond Pydantic

Keep the dependency footprint minimal. `amnesia.py` must be installable with a single `pip install pydantic`.

## Adding Subcommands to amnesia.py

1. Define a handler function following the `cmd_*` naming convention:

```python
def cmd_entity_mycommand(args):
    from scripts.entity import my_function
    try:
        ok(my_function(args.name, root(args)))
    except Exception as e:
        err(f"unexpected_error: {e}")
```

1. Register the subcommand in `main()` by adding it to the relevant `add_subparsers` block.

2. Write a test in `tests/test_cli.py` using the `run_amnesia()` helper.

## Adding New Modules to scripts/

- New modules go in `scripts/` and must be importable as `scripts.<module>`.
- Each module should have a clear single responsibility (e.g., `merge.py` for dedup logic, `paths.py` for path resolution, `native_memory.py` for native MEMORY.md integration).
- Write unit tests in `tests/test_<module>.py`.

## JSON Schema

The `$schema` URL for entity files is defined as `SCHEMA_URL` in `scripts/schema.py`. If you update the schema, also update `schemas/amnesia-entity.schema.json` so editor validation stays in sync.

## Commands (.md files)

Commands in `commands/` are thin Claude Code wrappers (≤40 lines each). They must not contain embedded logic — delegate all computation to `amnesia.py`.

## PR Process

1. Fork the repository and create a feature branch.
2. Follow TDD: write tests first, then implementation.
3. Ensure the full test suite passes: `python -m pytest tests/ -v`.
4. Submit a pull request with a clear description of the change and the REQ-ID it addresses (if applicable).
5. PRs that break existing tests will not be merged.
