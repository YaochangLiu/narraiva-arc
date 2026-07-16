# NAR-32 migration evidence

Source repository: `YaochangLiu/cyber-novelist-factory`

Evidence commit: `94d7a1129e9532997bf222a79e603a1ea03aca3a`

The legacy repository remains unchanged and traceable. The following map records behavior accepted
into Arc Engine and coupling deliberately rejected.

| Arc capability | Legacy evidence | Accepted behavior | Rejected coupling |
| --- | --- | --- | --- |
| Ordered generation | `src/pipeline/orchestrator.py`; `tests/test_orchestrator.py::test_state_machine_sequence` | explicit ordered stages and halt-on-error behavior | config loading, provider construction, Web emitter calls, test-module imports |
| Planning | `src/pipeline/phase2_outline/outline_generator.py`; outline tests in `tests/test_pipeline.py` | a plan precedes drafting and ends with resolution | genre data files and registry mutation as the public interface |
| Rolling writing | `src/pipeline/phase3_writer/rolling_writer.py`; `tests/test_rolling_writer.py` | drafting is resumable after a completed plan | chapter files, private dependency injection, internal round graph |
| Rhythm/emotion refinement | `src/pipeline/phase34_rhythm/`; `src/pipeline/phase35_emotion/` | refinement is a distinct post-draft stage | exposing rhythm/emotion implementations to hosts |
| Narrative validation | `src/pipeline/phase35_emotion/narrative_qc.py`; `tests/test_narrative_qc.py` | validation is later than refinement | optional QC flags that do not control export |
| Output safety | `src/security/content_filter.py`; `src/security/feedback_loop.py`; `tests/test_security.py` | deterministic detection and explicit violation reporting | allowing persistent BLOCK output to continue with only a review flag |
| Checkpoint | `src/registry/checkpoint.py`; `tests/test_checkpoint.py` | UTF-8 JSON, fsync, atomic replace, no temporary residue | importing the legacy StateRegistry or filesystem layout |
| Export | `src/exporter/markdown_exporter.py`; `tests/test_exporter.py` | Markdown story metadata and content are portable output | orchestrator importing Web story-index functions during export |

## Resolved defects

- `outlined` is replaced by the unambiguous completed stage `planned`; resume starts after it.
- Safety failure is a hard gate: blocked results never contain a Story Artifact.
- The engine accepts provider and checkpoint adapters through constructors, never private fields.
- Stage Events are returned as data; there is no Web emitter or duplicate Web runner.
- Offline generation has no network, scraper, sleep, retry, or filesystem requirement, so the first
  test cannot hang on external work.
- Engine source has a repository-contract test preventing FastAPI, Flask, Django, Vue, or Cloud
  Server imports.
