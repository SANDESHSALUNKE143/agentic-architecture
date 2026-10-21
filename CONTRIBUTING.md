# Contributing

Shared contracts and runtime behavior belong in core/contracts/adapters/services/sdk; agent-specific business logic belongs in consumer repositories. See [source layout](doc/source-layout.md) and [folder index](doc/folder-index.md). Preserve public compatibility exports and package mappings when moving files.

Install an isolated development environment with `python -m pip install -e '.[dev,runtime,service,providers,telemetry]'`, then run:

```sh
ruff format --check .
ruff check .
python deployment/scripts/check_repository.py
python -m unittest discover -s tests -v
python examples/minimal.py
python tests/evaluation/run.py
python deployment/scripts/validate_config.py
python -m build
```

The repository pins Ruff for repeatable formatting. Public classes/functions need useful docstrings explaining responsibilities and significant errors/side effects; avoid comments that simply repeat each line. Each maintained folder needs a README explaining ownership, actual contents and verification. Keep local Markdown links valid and distinguish active implementation, reference design, compatibility exports and template material. Update the folder index when adding a folder.

Tests should prove denied work causes no external operation, scopes remain isolated, profiles match and limits are enforced. Run full-platform acceptance only against the local synthetic stack; it creates test revisions/documents. Do not upload real data or commit credentials. Tests do not grant deployment/publication permission.

Release gates include live integration, dependency/image locking and scanning, backup/restore and capacity validation. See doc/release-gates.md. A passing local check is not evidence that hosted CI or paid providers were exercised.
