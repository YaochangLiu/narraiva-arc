"""Portable Arc Engine interface and deterministic offline implementation."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol
from uuid import UUID, uuid4

from narraiva_arc.brief import StoryBrief, interpret_story_brief


class GenerationContractError(ValueError):
    """Raised when a caller uses an unsupported generation contract."""


class CheckpointNotFoundError(LookupError):
    """Raised when a checkpoint identifier is invalid or unavailable."""


class EngineStage(StrEnum):
    """Last successfully completed stage in an Arc Engine run."""

    INTAKE = "intake"
    PLANNED = "planned"
    DRAFTED = "drafted"
    REFINED = "refined"
    VALIDATED = "validated"
    EXPORTED = "exported"


class GenerationStatus(StrEnum):
    """Observable outcome of a generation request."""

    COMPLETED = "completed"
    PAUSED = "paused"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    """Versioned request accepted by Arc Engine."""

    version: str
    story_brief: StoryBrief
    pause_after: EngineStage | None = None

    @classmethod
    def from_input(
        cls,
        creative_input: str = "",
        *,
        pause_after: EngineStage | None = None,
    ) -> GenerationRequest:
        return cls(
            version="arc.generation-request/v1",
            story_brief=interpret_story_brief(creative_input),
            pause_after=pause_after,
        )

    @classmethod
    def from_story_brief(
        cls,
        story_brief: StoryBrief,
        *,
        pause_after: EngineStage | None = None,
    ) -> GenerationRequest:
        return cls(
            version="arc.generation-request/v1",
            story_brief=story_brief,
            pause_after=pause_after,
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "story_brief": self.story_brief.to_engine_payload(),
            "pause_after": self.pause_after.value if self.pause_after else None,
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> GenerationRequest:
        if set(payload) != {"version", "story_brief", "pause_after"}:
            raise GenerationContractError("Generation request fields are invalid")
        version = payload["version"]
        if version != "arc.generation-request/v1":
            raise GenerationContractError(f"Unsupported request version: {version}")
        raw_brief = payload["story_brief"]
        if not isinstance(raw_brief, Mapping):
            raise GenerationContractError("story_brief must be an object")
        raw_pause_after = payload["pause_after"]
        try:
            pause_after = None if raw_pause_after is None else EngineStage(str(raw_pause_after))
        except ValueError as error:
            raise GenerationContractError("pause_after is invalid") from error
        return cls(
            version=version,
            story_brief=StoryBrief.from_engine_payload(raw_brief),
            pause_after=pause_after,
        )


@dataclass(frozen=True, slots=True)
class StoryArtifact:
    """Portable story output returned without writing to a filesystem."""

    version: str
    brief_version: str
    title: str
    genre: str
    outline: tuple[str, ...]
    markdown: str
    word_count: int

    def to_payload(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "brief_version": self.brief_version,
            "title": self.title,
            "genre": self.genre,
            "outline": list(self.outline),
            "markdown": self.markdown,
            "word_count": self.word_count,
        }


@dataclass(frozen=True, slots=True)
class StageEvent:
    """Versioned stage event returned to hosts without transport coupling."""

    stage: EngineStage
    version: str = "arc.stage-event/v1"

    def to_payload(self) -> dict[str, str]:
        return {"version": self.version, "stage": self.stage.value}


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Result returned through the Arc Engine interface."""

    status: GenerationStatus
    completed_stage: EngineStage
    artifact: StoryArtifact | None
    safety_violations: tuple[str, ...] = ()
    checkpoint_id: str | None = None
    events: tuple[StageEvent, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "version": "arc.generation-result/v1",
            "status": self.status.value,
            "completed_stage": self.completed_stage.value,
            "artifact": self.artifact.to_payload() if self.artifact else None,
            "safety_violations": list(self.safety_violations),
            "checkpoint_id": self.checkpoint_id,
            "events": [event.to_payload() for event in self.events],
        }


@dataclass(frozen=True, slots=True)
class _EngineCheckpoint:
    checkpoint_id: str
    brief: StoryBrief
    completed_stage: EngineStage
    outline: tuple[str, ...]


class CheckpointStore(Protocol):
    """Persistence seam for private Arc Engine checkpoint payloads."""

    def save(self, checkpoint_id: str, payload: Mapping[str, Any]) -> None: ...

    def load(self, checkpoint_id: str) -> Mapping[str, Any]: ...


class SafetyGate(Protocol):
    """Output-validation seam invoked before an artifact may be exported."""

    def violations(self, text: str) -> tuple[str, ...]: ...


class StoryProvider(Protocol):
    """Model seam used internally by Arc Engine planning and writing stages."""

    def plan(self, brief: StoryBrief) -> tuple[str, ...]: ...

    def draft(self, brief: StoryBrief, outline: tuple[str, ...]) -> str: ...

    def refine(self, brief: StoryBrief, outline: tuple[str, ...], draft: str) -> str: ...


@dataclass(frozen=True, slots=True)
class KeywordSafetyGate:
    """Deterministic local safety adapter for host-supplied blocked terms."""

    blocked_terms: tuple[str, ...] = ()

    def violations(self, text: str) -> tuple[str, ...]:
        normalized_text = text.casefold()
        return tuple(term for term in self.blocked_terms if term.casefold() in normalized_text)


class DeterministicStoryProvider:
    """Network-free provider adapter for examples, tests, and local smoke runs."""

    def plan(self, brief: StoryBrief) -> tuple[str, ...]:
        protagonist = brief.protagonist.value or "The protagonist"
        setting = brief.setting.value or "an unfamiliar place"
        conflict = brief.central_conflict.value or "make a choice that cannot be undone"
        required_details = ", ".join(brief.must_include.value) or "a revealing clue"
        return (
            f"Opening: {protagonist} encounters the central problem in {setting}.",
            f"Escalation: {protagonist} must {conflict} while confronting {required_details}.",
            f"Resolution: the choice reaches a {brief.ending_preference.value} ending.",
        )

    def draft(self, brief: StoryBrief, outline: tuple[str, ...]) -> str:
        del outline
        premise = brief.premise.value
        protagonist = brief.protagonist.value or "The protagonist"
        setting = brief.setting.value or "an unfamiliar place"
        conflict = brief.central_conflict.value or "make a choice that cannot be undone"
        required_details = ", ".join(brief.must_include.value) or "a revealing clue"
        title = f"{protagonist}'s Unexpected Choice"
        return (
            f"# {title}\n\n"
            f"{premise}\n\n"
            f"In {setting}, {protagonist} found {required_details}. "
            f"The discovery forced {protagonist} to {conflict}.\n\n"
            f"The pressure sharpened, but the story remained {brief.tone.value}. "
            f"At last, {protagonist} accepted the consequence and moved toward "
            f"an ending that felt {brief.ending_preference.value}."
        )

    def refine(self, brief: StoryBrief, outline: tuple[str, ...], draft: str) -> str:
        del brief, outline
        return draft


class InMemoryCheckpointStore:
    """Process-local checkpoint adapter used by the default offline engine."""

    def __init__(self) -> None:
        self._payloads: dict[str, dict[str, Any]] = {}

    def save(self, checkpoint_id: str, payload: Mapping[str, Any]) -> None:
        self._payloads[checkpoint_id] = dict(payload)

    def load(self, checkpoint_id: str) -> Mapping[str, Any]:
        return self._payloads[checkpoint_id]


class JsonFileCheckpointStore:
    """Crash-safe local JSON checkpoint adapter for CLI and local Web hosts."""

    def __init__(self, checkpoint_dir: str | Path) -> None:
        self._dir = Path(checkpoint_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(self, checkpoint_id: str, payload: Mapping[str, Any]) -> None:
        path = self._path(checkpoint_id)
        temporary = path.with_suffix(".json.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def load(self, checkpoint_id: str) -> Mapping[str, Any]:
        with self._path(checkpoint_id).open(encoding="utf-8") as stream:
            payload: object = json.load(stream)
        if not isinstance(payload, dict):
            raise ValueError("Checkpoint payload must be an object")
        return payload

    def _path(self, checkpoint_id: str) -> Path:
        return self._dir / f"{checkpoint_id}.json"


class ArcEngine:
    """Deep module that turns a Story Brief into a portable story artifact."""

    def __init__(
        self,
        provider: StoryProvider | None = None,
        checkpoint_store: CheckpointStore | None = None,
        safety_gate: SafetyGate | None = None,
    ) -> None:
        self._provider = provider or DeterministicStoryProvider()
        self._checkpoint_store = checkpoint_store or InMemoryCheckpointStore()
        self._safety_gate = safety_gate or KeywordSafetyGate()

    @classmethod
    def offline(
        cls,
        checkpoint_store: CheckpointStore | None = None,
        safety_gate: SafetyGate | None = None,
    ) -> ArcEngine:
        """Create the deterministic, network-free Arc Engine adapter."""
        return cls(
            provider=DeterministicStoryProvider(),
            checkpoint_store=checkpoint_store,
            safety_gate=safety_gate,
        )

    def run(self, request: GenerationRequest) -> GenerationResult:
        """Run every generation stage and return a portable artifact."""
        if request.version != "arc.generation-request/v1":
            raise GenerationContractError(f"Unsupported request version: {request.version}")
        pause_after = request.pause_after
        if pause_after is not None and pause_after is not EngineStage.PLANNED:
            raise GenerationContractError(f"Unsupported pause stage: {pause_after.value}")
        brief = request.story_brief
        outline = self._provider.plan(brief)
        if pause_after is EngineStage.PLANNED:
            checkpoint_id = str(uuid4())
            checkpoint = _EngineCheckpoint(
                checkpoint_id=checkpoint_id,
                brief=brief,
                completed_stage=EngineStage.PLANNED,
                outline=outline,
            )
            self._save_checkpoint(checkpoint)
            return GenerationResult(
                status=GenerationStatus.PAUSED,
                completed_stage=EngineStage.PLANNED,
                artifact=None,
                checkpoint_id=checkpoint_id,
                events=self._events_through(EngineStage.PLANNED),
            )
        return self._complete(brief, outline)

    def resume(self, checkpoint_id: str) -> GenerationResult:
        """Continue strictly after the stage recorded by a checkpoint."""
        checkpoint = self._load_checkpoint(checkpoint_id)
        if checkpoint.completed_stage is not EngineStage.PLANNED:
            raise ValueError(
                f"Cannot resume after unsupported stage: {checkpoint.completed_stage.value}"
            )
        return self._complete(checkpoint.brief, checkpoint.outline)

    def _save_checkpoint(self, checkpoint: _EngineCheckpoint) -> None:
        self._checkpoint_store.save(
            checkpoint.checkpoint_id,
            {
                "version": "arc.engine-checkpoint/v1",
                "checkpoint_id": checkpoint.checkpoint_id,
                "completed_stage": checkpoint.completed_stage.value,
                "story_brief": checkpoint.brief.to_engine_payload(),
                "outline": list(checkpoint.outline),
            },
        )

    def _load_checkpoint(self, checkpoint_id: str) -> _EngineCheckpoint:
        try:
            UUID(checkpoint_id)
            payload = self._checkpoint_store.load(checkpoint_id)
        except (FileNotFoundError, KeyError, ValueError) as error:
            raise CheckpointNotFoundError(f"Checkpoint is unavailable: {checkpoint_id}") from error
        if payload.get("version") != "arc.engine-checkpoint/v1":
            raise ValueError("Unsupported checkpoint version")
        if payload.get("checkpoint_id") != checkpoint_id:
            raise ValueError("Checkpoint identifier mismatch")
        raw_outline = payload.get("outline")
        raw_brief = payload.get("story_brief")
        if not isinstance(raw_outline, list) or not all(
            isinstance(item, str) for item in raw_outline
        ):
            raise ValueError("Checkpoint outline must be a list of strings")
        if not isinstance(raw_brief, Mapping):
            raise ValueError("Checkpoint Story Brief must be an object")
        return _EngineCheckpoint(
            checkpoint_id=checkpoint_id,
            brief=StoryBrief.from_engine_payload(raw_brief),
            completed_stage=EngineStage(str(payload.get("completed_stage"))),
            outline=tuple(raw_outline),
        )

    def _complete(self, brief: StoryBrief, outline: tuple[str, ...]) -> GenerationResult:
        protagonist = brief.protagonist.value or "The protagonist"
        title = f"{protagonist}'s Unexpected Choice"
        draft = self._provider.draft(brief, outline)
        markdown = self._provider.refine(brief, outline, draft)
        violations = self._safety_gate.violations(markdown)
        if violations:
            return GenerationResult(
                status=GenerationStatus.BLOCKED,
                completed_stage=EngineStage.REFINED,
                artifact=None,
                safety_violations=violations,
                events=self._events_through(EngineStage.REFINED),
            )
        return GenerationResult(
            status=GenerationStatus.COMPLETED,
            completed_stage=EngineStage.EXPORTED,
            artifact=StoryArtifact(
                version="arc.story-artifact/v1",
                brief_version=brief.schema_version,
                title=title,
                genre=brief.genre.value,
                outline=outline,
                markdown=markdown,
                word_count=len(markdown.split()),
            ),
            events=self._events_through(EngineStage.EXPORTED),
        )

    @staticmethod
    def _events_through(completed_stage: EngineStage) -> tuple[StageEvent, ...]:
        stages = (
            EngineStage.INTAKE,
            EngineStage.PLANNED,
            EngineStage.DRAFTED,
            EngineStage.REFINED,
            EngineStage.VALIDATED,
            EngineStage.EXPORTED,
        )
        end = stages.index(completed_stage) + 1
        return tuple(StageEvent(stage) for stage in stages[:end])
