# Contributing

Thanks for helping build Narraiva Arc. During private incubation, discuss substantial behavior or
architecture changes in an issue before implementation. Contributions should preserve the
product/engine/cloud boundaries in `docs/ARCHITECTURE.md`.

## Development setup

```console
python -m venv .venv
python -m pip install -e ".[dev]"
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
python scripts/check_repository_policy.py
python -m pip_audit --cache-dir .cache/pip-audit
```

Add behavior-level tests before implementation where practical. Never use real manuscripts,
credentials, or provider responses as fixtures. Keep commits focused and explain externally visible
behavior in the pull request.

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Bug reports and
feature proposals belong in GitHub Issues. Security reports follow [SECURITY.md](SECURITY.md).
