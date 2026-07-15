# Repository content policy

This repository contains reusable source, tests, documentation, and deliberately synthetic
fixtures. It must never contain provider credentials, private keys, real environment files, user
manuscripts, generated stories, exports, logs, caches, or local databases.

`scripts/check_repository_policy.py` checks tracked filenames and required governance files. CI
also scans the Git history for secrets. Synthetic fixtures must live under `tests/fixtures`, state
that they are synthetic, and contain no copied user material.

Before adding a dependency, record every distributed runtime dependency and its license in
`THIRD_PARTY_LICENSES.md`. Development-only tools are verified by dependency audit but are not
represented as bundled runtime components.
