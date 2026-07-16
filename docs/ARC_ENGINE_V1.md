# Arc Engine v1 interface

Arc Engine is the portable story-generation module used by CLI, local Web, and future Narraiva
Cloud Worker hosts. Its external interface has two operations: `run(GenerationRequest)` and
`resume(checkpoint_id)`.

## Contract versions

| Contract | Version |
| --- | --- |
| Generation Request | `arc.generation-request/v1` |
| Story Brief | `arc.story-brief/v1` |
| Stage Event | `arc.stage-event/v1` |
| Engine Checkpoint | `arc.engine-checkpoint/v1` |
| Generation Result | `arc.generation-result/v1` |
| Story Artifact | `arc.story-artifact/v1` |

Unknown request, Story Brief, or checkpoint versions are rejected. `to_payload()` returns JSON-safe
data for a CLI process, local Web host, or Cloud Worker transport. A Generation Request payload is
private task data because its nested Story Brief retains Creative Input.

Hosts must validate the complete machine-readable identity returned by
`narraiva_arc.compatibility_manifest()` (or `python -m narraiva_arc --compatibility`) rather than
matching only the Python package version. CI builds a wheel from the exact checked-out commit,
installs it into an isolated environment, runs the deterministic checkpoint/resume smoke, and
publishes the wheel with `SHA256SUMS` under an artifact name containing the source commit SHA.

## Stages

Arc Engine completes stages in this order:

1. `intake` — accept and validate the Story Brief;
2. `planned` — produce a three-part story plan;
3. `drafted` — produce story text;
4. `refined` — apply provider refinement, including future rhythm/emotion strategies;
5. `validated` — pass the mandatory Safety Gate;
6. `exported` — return a portable Story Artifact.

Stage Events contain no clock or transport fields. Hosts may attach their own timestamps, job IDs,
or WebSocket envelopes without making the engine depend on infrastructure.

## Offline mode and provider seam

`ArcEngine.offline()` uses `DeterministicStoryProvider`. It performs no network access and produces
the same Story Artifact content for the same Story Brief. It is intended for tests, examples, and
local smoke runs—not as a claim of production prose quality.

Hosted or local-model integrations implement the `StoryProvider` seam (`plan`, `draft`, `refine`)
and inject the adapter into `ArcEngine`. Provider configuration, credentials, retry policy, and
HTTP clients remain outside the engine.

## Checkpoint semantics

In v1, `planned` is the supported pause point. A checkpoint's `completed_stage` means that stage is
already complete. `resume()` therefore continues with drafting and never regenerates the plan.
This resolves the legacy ambiguity where `outlined` meant both “ready to write” and “rerun outline.”

The default adapter is process-local `InMemoryCheckpointStore`. `JsonFileCheckpointStore` performs
UTF-8 JSON writes through flush, fsync, and atomic replace, and supports resume in a new process.
Checkpoint files contain the private Story Brief and must follow the host's user-content retention
policy; they are never ordinary logs.

## Safety and export

The Safety Gate runs on the complete export candidate—title, genre, outline, and refined
Markdown—before a Story Artifact is constructed. A blocked result has:

- status `blocked`;
- completed stage `refined`;
- no artifact;
- explicit `safety_violations`.

Unlike the legacy feedback loop, a high-severity failure cannot continue into export. The bundled
`KeywordSafetyGate` is deterministic infrastructure for local policy terms; production hosts may
inject a stronger adapter through the same seam.

## Scope of the deterministic provider

The v1 engine establishes the orchestration, provider, checkpoint, event, safety, and artifact
contracts. Legacy rhythm, character, cognitive-emotion, and narrative-QC implementations are not
copied as public modules. They may be introduced later behind `StoryProvider.refine` or the Safety
Gate when characterization evidence proves they improve behavior without expanding the external
interface.
