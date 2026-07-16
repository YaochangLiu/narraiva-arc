# NAR-32 migration evidence

Source repository: `YaochangLiu/cyber-novelist-factory`

Evidence commit for every legacy path below: `94d7a1129e9532997bf222a79e603a1ea03aca3a`

The legacy repository remains unchanged and traceable. Each accepted capability maps to its legacy
evidence, its replacement implementation, and a test at the Arc Engine interface.

| Accepted capability | Legacy file and test evidence | Arc replacement | Arc interface test |
| --- | --- | --- | --- |
| Ordered generation | `src/pipeline/orchestrator.py`; `tests/test_orchestrator.py::test_state_machine_sequence` | `src/narraiva_arc/engine.py::ArcEngine` and `StageEvent` | `tests/test_engine.py::test_one_sentence_completes_offline_story_generation` |
| Story Brief intake | legacy `StoryConfig` and manual `l3_topic` in `src/pipeline/orchestrator.py`; `tests/test_orchestrator.py::test_story_config_defaults` | `GenerationRequest` consuming NAR-31 `StoryBrief` | `test_one_sentence_completes_offline_story_generation`; `test_explicit_story_brief_drives_the_portable_artifact` |
| Planning before drafting | `src/pipeline/phase2_outline/outline_generator.py`; `tests/test_pipeline.py::test_last_chapter_has_resolution_beat` | `StoryProvider.plan` and deterministic adapter | `test_explicit_story_brief_drives_the_portable_artifact` |
| Provider-controlled writing | `src/pipeline/phase3_writer/rolling_writer.py`; `tests/test_rolling_writer.py::test_writes_until_target_words_met` | `StoryProvider.draft/refine` behind `ArcEngine.run` | `test_injected_provider_adapter_controls_generation` |
| Checkpoint/resume | `src/registry/checkpoint.py`; `tests/test_checkpoint.py::test_state_registry_round_trip_preserves_story_id`; conflicting `resume/run_from` in `src/pipeline/orchestrator.py` | `CheckpointStore`, `JsonFileCheckpointStore`, and `ArcEngine.resume` | `test_resume_continues_after_the_completed_checkpoint_stage`; `test_checkpoint_can_resume_in_a_new_engine_instance` |
| Output safety | `src/security/content_filter.py`; `src/security/feedback_loop.py`; `tests/test_security.py::test_block_three_failures_adds_review_flag` | mandatory `SafetyGate` before Story Artifact construction | `test_output_safety_blocks_artifact_before_export`; `test_output_safety_checks_outline_before_export` |
| Portable export | `src/exporter/markdown_exporter.py`; `tests/test_exporter.py::test_export_with_two_chapters_has_frontmatter_and_toc` | in-memory, versioned `StoryArtifact` and `GenerationResult.to_payload` | `test_generation_contract_payload_round_trip_is_portable` |
| Framework isolation | Web calls and `from tests.conftest import MockLLMProvider` in `src/pipeline/orchestrator.py` | returned Stage Events plus injected adapters; no host imports | `tests/test_repository_contract.py::test_engine_source_has_no_host_framework_imports` |

## Explicitly deferred, not migrated

The following legacy implementations are candidates, not accepted NAR-32 modules. Arc Engine v1
preserves a refinement seam for later evidence-based migration without exposing their class graph:

- rhythm: `src/pipeline/phase34_rhythm/rhythm_scheduler.py`, evidenced by
  `tests/test_rhythm_integration.py::test_phase_rhythm_generates_report_and_text`;
- cognitive emotion: `src/pipeline/phase35_emotion/cognitive_rewriter.py`, evidenced by
  `tests/test_cognitive_emotion_rewriter.py`;
- narrative QC rules: `src/pipeline/phase35_emotion/narrative_qc.py`, evidenced by
  `tests/test_narrative_qc.py::test_rewrite_with_forbidden_word_fails`;
- character profiling: `src/pipeline/character_profile/profiler.py`, evidenced by
  `tests/test_character_profiler.py`.

No production HTTP/model adapter is migrated in NAR-32. NAR-33 may implement Narraiva Cloud's
adapter against `StoryProvider`; local-model adapters can use the same seam.

## Resolved defects

- `outlined` is replaced by completed stage `planned`; resume reuses its stored outline and a test
  adapter fails immediately if planning is invoked again.
- Safety evaluates title, genre, outline, and refined prose; blocked results contain no artifact.
- Dependencies enter through constructors, never private fields.
- Stage Events are returned as data; there is no Web emitter or duplicate Web runner.
- Offline generation has no network, scraper, sleep, retry, or filesystem requirement, so the first
  test cannot hang on external work.
