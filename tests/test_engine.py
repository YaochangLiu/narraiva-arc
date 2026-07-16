from pathlib import Path

import pytest

import narraiva_arc
from narraiva_arc.brief import BriefValues, interpret_story_brief
from narraiva_arc.engine import (
    ArcEngine,
    CheckpointNotFoundError,
    EngineStage,
    GenerationContractError,
    GenerationRequest,
    GenerationStatus,
    JsonFileCheckpointStore,
    KeywordSafetyGate,
)


class FixedStoryProvider:
    def plan(self, _brief: object) -> tuple[str, ...]:
        return ("A fixed beginning", "A fixed turn", "A fixed ending")

    def draft(self, _brief: object, _outline: tuple[str, ...]) -> str:
        return "An early draft that should not be exported."

    def refine(
        self,
        _brief: object,
        _outline: tuple[str, ...],
        _draft: str,
    ) -> str:
        return "The provider's final synthetic story."


class ResumeOnlyProvider:
    def plan(self, _brief: object) -> tuple[str, ...]:
        raise AssertionError("resume must not regenerate a completed plan")

    def draft(self, _brief: object, outline: tuple[str, ...]) -> str:
        return f"Resumed from: {outline[0]}"

    def refine(
        self,
        _brief: object,
        _outline: tuple[str, ...],
        draft: str,
    ) -> str:
        return draft


class UnsafeOutlineProvider(FixedStoryProvider):
    def plan(self, _brief: object) -> tuple[str, ...]:
        return ("A forbidden sigil appears", "A safe turn", "A safe ending")

    def refine(
        self,
        _brief: object,
        _outline: tuple[str, ...],
        _draft: str,
    ) -> str:
        return "Safe final prose."


def test_package_exposes_the_versioned_arc_engine_interface() -> None:
    assert narraiva_arc.ArcEngine is ArcEngine
    assert narraiva_arc.GenerationRequest is GenerationRequest


def test_one_sentence_completes_offline_story_generation() -> None:
    engine = ArcEngine.offline()

    result = engine.run(
        GenerationRequest.from_input(
            "A clockmaker discovers tomorrow hidden inside a broken watch."
        )
    )

    assert result.status is GenerationStatus.COMPLETED
    assert result.completed_stage is EngineStage.EXPORTED
    assert result.artifact is not None
    assert result.artifact.version == "arc.story-artifact/v1"
    assert "clockmaker" in result.artifact.markdown.lower()
    assert result.artifact.word_count > 0
    assert result.safety_violations == ()
    assert tuple(event.stage for event in result.events) == (
        EngineStage.INTAKE,
        EngineStage.PLANNED,
        EngineStage.DRAFTED,
        EngineStage.REFINED,
        EngineStage.VALIDATED,
        EngineStage.EXPORTED,
    )
    assert all(event.version == "arc.stage-event/v1" for event in result.events)


def test_explicit_story_brief_drives_the_portable_artifact() -> None:
    brief = interpret_story_brief(
        explicit=BriefValues(
            premise="Mara must return a stolen memory before dawn.",
            genre="fantasy mystery",
            tone="tense but hopeful",
            protagonist="Mara",
            setting="a city where memories are traded",
            central_conflict="return the memory without exposing its owner",
            must_include=("glass fox",),
            ending_preference="resolved",
        )
    )

    result = ArcEngine.offline().run(GenerationRequest.from_story_brief(brief))

    assert result.status is GenerationStatus.COMPLETED
    assert result.artifact is not None
    assert result.artifact.brief_version == "arc.story-brief/v1"
    assert result.artifact.genre == "fantasy mystery"
    assert len(result.artifact.outline) == 3
    assert "Mara" in result.artifact.markdown
    assert "glass fox" in result.artifact.markdown


def test_resume_continues_after_the_completed_checkpoint_stage() -> None:
    engine = ArcEngine.offline()
    paused = engine.run(
        GenerationRequest.from_input(
            "A gardener grows a door that opens onto lost summers.",
            pause_after=EngineStage.PLANNED,
        )
    )

    assert paused.status is GenerationStatus.PAUSED
    assert paused.completed_stage is EngineStage.PLANNED
    assert paused.artifact is None
    assert paused.checkpoint_id is not None

    resumed = engine.resume(paused.checkpoint_id)

    assert resumed.status is GenerationStatus.COMPLETED
    assert resumed.completed_stage is EngineStage.EXPORTED
    assert resumed.artifact is not None
    assert "gardener" in resumed.artifact.markdown.lower()


def test_checkpoint_can_resume_in_a_new_engine_instance(tmp_path: Path) -> None:
    first_engine = ArcEngine.offline(
        checkpoint_store=JsonFileCheckpointStore(tmp_path / "checkpoints")
    )
    paused = first_engine.run(
        GenerationRequest.from_input(
            "A courier carries the final letter between two vanished cities.",
            pause_after=EngineStage.PLANNED,
        )
    )
    assert paused.checkpoint_id is not None

    restarted_engine = ArcEngine(
        provider=ResumeOnlyProvider(),
        checkpoint_store=JsonFileCheckpointStore(tmp_path / "checkpoints"),
    )
    resumed = restarted_engine.resume(paused.checkpoint_id)

    assert resumed.status is GenerationStatus.COMPLETED
    assert resumed.artifact is not None
    assert resumed.artifact.outline == (
        "Opening: The protagonist encounters the central problem in an unfamiliar place.",
        "Escalation: The protagonist must make a choice that cannot be undone while "
        "confronting a revealing clue.",
        "Resolution: the choice reaches an ending that feels open.",
    )
    assert resumed.artifact.markdown.startswith("Resumed from: Opening:")
    assert list((tmp_path / "checkpoints").glob("*.tmp")) == []


def test_output_safety_blocks_artifact_before_export() -> None:
    brief = interpret_story_brief(
        explicit=BriefValues(
            premise="An archivist opens a sealed map.",
            must_include=("forbidden sigil",),
        )
    )
    engine = ArcEngine.offline(safety_gate=KeywordSafetyGate(blocked_terms=("forbidden sigil",)))

    result = engine.run(GenerationRequest.from_story_brief(brief))

    assert result.status is GenerationStatus.BLOCKED
    assert result.completed_stage is EngineStage.REFINED
    assert result.artifact is None
    assert result.safety_violations == ("forbidden sigil",)


def test_output_safety_checks_outline_before_export() -> None:
    engine = ArcEngine(
        provider=UnsafeOutlineProvider(),
        safety_gate=KeywordSafetyGate(blocked_terms=("forbidden sigil",)),
    )

    result = engine.run(
        GenerationRequest.from_input("A safe premise with provider-controlled planning.")
    )

    assert result.status is GenerationStatus.BLOCKED
    assert result.artifact is None
    assert result.safety_violations == ("forbidden sigil",)


def test_injected_provider_adapter_controls_generation() -> None:
    result = ArcEngine(provider=FixedStoryProvider()).run(
        GenerationRequest.from_input("A premise delegated through the provider seam.")
    )

    assert result.status is GenerationStatus.COMPLETED
    assert result.artifact is not None
    assert result.artifact.outline == (
        "A fixed beginning",
        "A fixed turn",
        "A fixed ending",
    )
    assert result.artifact.markdown == "The provider's final synthetic story."


def test_versioned_generation_interface_rejects_unknown_request_version() -> None:
    brief = interpret_story_brief("A diver hears a bell beneath a dry sea.")

    with pytest.raises(GenerationContractError, match="request version"):
        ArcEngine.offline().run(
            GenerationRequest(version="arc.generation-request/v2", story_brief=brief)
        )


def test_resume_rejects_missing_or_invalid_checkpoint_identifiers(tmp_path: Path) -> None:
    engine = ArcEngine.offline(checkpoint_store=JsonFileCheckpointStore(tmp_path / "checkpoints"))

    with pytest.raises(CheckpointNotFoundError):
        engine.resume("00000000-0000-0000-0000-000000000000")
    with pytest.raises(CheckpointNotFoundError):
        engine.resume("../../outside")


def test_generation_contract_payload_round_trip_is_portable() -> None:
    request = GenerationRequest.from_input(
        "A cartographer maps a country that only exists at dusk.",
        pause_after=EngineStage.PLANNED,
    )

    restored = GenerationRequest.from_payload(request.to_payload())
    paused = ArcEngine.offline().run(restored)
    payload = paused.to_payload()

    assert restored.story_brief == request.story_brief
    assert restored.pause_after is EngineStage.PLANNED
    assert payload["version"] == "arc.generation-result/v1"
    assert payload["status"] == "paused"
    assert payload["completed_stage"] == "planned"
    assert payload["artifact"] is None
    assert payload["events"] == [
        {"version": "arc.stage-event/v1", "stage": "intake"},
        {"version": "arc.stage-event/v1", "stage": "planned"},
    ]
