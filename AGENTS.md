# Narraiva Arc agent instructions

This repository is the source of truth for Narraiva Arc and its open-source Arc Engine core. The
historical `cyber-novelist-factory` repository is migration evidence only; do not copy it wholesale
or modify it while working here.

Track work in this repository's GitHub Issues unless a task explicitly names a Linear issue during
the incubation pilot. Preserve the boundary between Arc Engine, the hosted Narraiva Arc product,
and Narraiva Cloud adapters.

Before handing off changes, run:

```console
python -m ruff format --check .
python -m ruff check .
python -m mypy
python -m pytest
python scripts/check_repository_policy.py
```

Never commit secrets, real environment files, user manuscripts, generated stories, exports, logs,
local databases, or caches. Use synthetic fixtures only.
