# Narraiva Arc

Narraiva Arc is an incubation-stage product for turning anything from a single sentence to a
free-form creative brief into a structured long-form story generation run. **Arc Engine** is the
open-source generation core that will live in this repository; the hosted Narraiva Arc product may
reuse Narraiva cloud infrastructure without putting cloud accounts, billing, operations, or user
content into the engine.

> This repository is private during pre-Alpha incubation. The intended source license is
> Apache-2.0, with public release considered around Alpha or Closed Beta readiness. Being able to
> read the source does not grant rights to Narraiva names or branding; see [TRADEMARKS.md](TRADEMARKS.md).

## Current status

This is the clean repository baseline established by NAR-30. It deliberately contains package
identity, governance, repository safety checks, and CI—but no story-generation implementation.
The first selective engine migration belongs to NAR-32.

## Repository lineage

`YaochangLiu/cyber-novelist-factory` is a migration reference and historical prototype, not the
source of truth for this project. It remains unchanged. Code will only move here after it is
reviewed, simplified, tested, and shown to belong to Arc Engine. We will not wholesale-copy its
cloud snapshots, old product documents, empty job/worker modules, duplicate runners, secrets,
stories, exports, databases, caches, or logs. See [docs/MIGRATION.md](docs/MIGRATION.md).

## Quick start

Python 3.11 or newer is required.

```console
python -m venv .venv
python -m pip install -e ".[dev]"
python -m narraiva_arc --version
python -m pytest
python scripts/check_repository_policy.py
```

The example verifies the package boundary without pretending the engine has already migrated:

```console
python examples/package_baseline.py
```

## Project boundaries

- **Narraiva Arc**: the user-facing product and eventual hosted experience.
- **Arc Engine**: the portable, open-source story-generation core in this repository.
- **Narraiva Cloud**: shared hosted infrastructure; integration belongs behind explicit adapters.
- **Narraiva clients**: downstream experiences and distribution, not dependencies of Arc Engine.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [CONTRIBUTING.md](CONTRIBUTING.md), and
[SECURITY.md](SECURITY.md) before contributing.
