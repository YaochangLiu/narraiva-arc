# Selective migration policy

The historical `cyber-novelist-factory` repository is evidence, not a template. Migration is a
review process: identify one coherent capability, document its inputs and outputs, remove product
and deployment coupling, add behavior-level tests, then move the smallest useful implementation.

Do not migrate:

- Diarina Cloud or NovelOS snapshots;
- stale KATERA planning and product documents;
- empty Cyber job or worker modules;
- duplicate web runners and adapters;
- real environment files, credentials, manuscripts, stories, exports, logs, local databases, or
  caches;
- unrelated agent or product-management artifacts.

The old repository remains unchanged. Narraiva Arc becomes the source of truth only for code
accepted into this repository through review.

NAR-32 applies this policy as a replace migration. It preserves proven behaviors—ordered stages,
deterministic local execution, atomic checkpoints, and Markdown output—but does not preserve the
legacy class graph or its Web/filesystem coupling. The detailed source map is recorded in
`MIGRATION_EVIDENCE_NAR32.md`.
