"""Versioned Story Brief contract for Arc Engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from re import findall
from typing import Any, Generic, Literal, TypeVar, overload

STORY_BRIEF_VERSION = "arc.story-brief/v1"


class FieldSource(StrEnum):
    """Provenance of a structured Story Brief field."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    DEFAULT = "default"


class CreativeInputMode(StrEnum):
    """How unstructured Creative Input may contribute a premise."""

    AUTO = "auto"
    PREMISE = "premise"
    FREEFORM = "freeform"


T = TypeVar("T")


class BriefValidationError(ValueError):
    """Raised when candidate values cannot form a valid Story Brief."""


class BriefConflictError(BriefValidationError):
    """Raised when mutually exclusive creator constraints overlap."""


@dataclass(frozen=True, slots=True)
class SourcedValue(Generic[T]):
    """A Story Brief value paired with its provenance."""

    value: T
    source: FieldSource


@dataclass(frozen=True, slots=True)
class BriefValues:
    """Candidate structured values supplied explicitly or by an interpreter."""

    premise: str | None = None
    genre: str | None = None
    tone: str | None = None
    target_length: str | None = None
    protagonist: str | None = None
    setting: str | None = None
    central_conflict: str | None = None
    ending_preference: str | None = None
    must_include: tuple[str, ...] | None = None
    must_avoid: tuple[str, ...] | None = None
    creative_freedom: float | None = None


DEFAULT_PREMISE = "An unexpected choice changes an ordinary life."
DEFAULT_GENRE = "general fiction"
DEFAULT_TONE = "balanced"
DEFAULT_TARGET_LENGTH = "short"
DEFAULT_ENDING_PREFERENCE = "open"
DEFAULT_CREATIVE_FREEDOM = 0.8

DEFAULT_BRIEF_VALUES = BriefValues(
    premise=DEFAULT_PREMISE,
    genre=DEFAULT_GENRE,
    tone=DEFAULT_TONE,
    target_length=DEFAULT_TARGET_LENGTH,
    protagonist=None,
    setting=None,
    central_conflict=None,
    ending_preference=DEFAULT_ENDING_PREFERENCE,
    must_include=(),
    must_avoid=(),
    creative_freedom=DEFAULT_CREATIVE_FREEDOM,
)


def _validate_values(values: BriefValues, source_name: str) -> None:
    text_fields = {
        "premise": values.premise,
        "genre": values.genre,
        "tone": values.tone,
        "protagonist": values.protagonist,
        "setting": values.setting,
        "central_conflict": values.central_conflict,
        "ending_preference": values.ending_preference,
    }
    for field_name, value in text_fields.items():
        if value is not None and not value.strip():
            raise BriefValidationError(f"{source_name}.{field_name} must not be blank")

    if values.target_length is not None and values.target_length not in {"short", "medium", "long"}:
        raise BriefValidationError(f"{source_name}.target_length must be short, medium, or long")
    if values.creative_freedom is not None and (
        not isfinite(values.creative_freedom) or not 0.0 <= values.creative_freedom <= 1.0
    ):
        raise BriefValidationError(f"{source_name}.creative_freedom must be between 0 and 1")

    for field_name, items in (
        ("must_include", values.must_include),
        ("must_avoid", values.must_avoid),
    ):
        if items is not None and any(not item.strip() for item in items):
            raise BriefValidationError(f"{source_name}.{field_name} must not contain blank items")


@dataclass(frozen=True, slots=True)
class StoryBrief:
    """Arc Engine's versioned, structured statement of story intent."""

    raw_input: str
    premise: SourcedValue[str]
    genre: SourcedValue[str]
    tone: SourcedValue[str]
    target_length: SourcedValue[str]
    protagonist: SourcedValue[str | None]
    setting: SourcedValue[str | None]
    central_conflict: SourcedValue[str | None]
    ending_preference: SourcedValue[str]
    must_include: SourcedValue[tuple[str, ...]]
    must_avoid: SourcedValue[tuple[str, ...]]
    creative_freedom: SourcedValue[float]
    schema_version: str = STORY_BRIEF_VERSION
    resolution_notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.schema_version != STORY_BRIEF_VERSION:
            raise BriefValidationError("unsupported schema_version")
        if not isinstance(self.raw_input, str):
            raise BriefValidationError("raw_input must be a string")
        if not all(isinstance(note, str) for note in self.resolution_notes):
            raise BriefValidationError("resolution_notes must contain strings")

        fields: dict[str, SourcedValue[Any]] = {
            "premise": self.premise,
            "genre": self.genre,
            "tone": self.tone,
            "target_length": self.target_length,
            "protagonist": self.protagonist,
            "setting": self.setting,
            "central_conflict": self.central_conflict,
            "ending_preference": self.ending_preference,
            "must_include": self.must_include,
            "must_avoid": self.must_avoid,
            "creative_freedom": self.creative_freedom,
        }
        for field_name, sourced_value in fields.items():
            if not isinstance(sourced_value, SourcedValue) or not isinstance(
                sourced_value.source, FieldSource
            ):
                raise BriefValidationError(f"{field_name} must have a valid FieldSource")

        default_values: dict[str, Any] = {
            field_name: getattr(DEFAULT_BRIEF_VALUES, field_name) for field_name in fields
        }
        for field_name, sourced_value in fields.items():
            if (
                sourced_value.source is FieldSource.DEFAULT
                and sourced_value.value != default_values[field_name]
            ):
                raise BriefValidationError(
                    f"{field_name} with source default must use the canonical default"
                )
            if sourced_value.source is not FieldSource.DEFAULT and sourced_value.value is None:
                raise BriefValidationError(
                    f"{field_name} with source {sourced_value.source.value} must have a value"
                )

        for field_name in ("premise", "genre", "tone", "target_length", "ending_preference"):
            if not isinstance(fields[field_name].value, str):
                raise BriefValidationError(f"{field_name} must be a string")
        for field_name in ("protagonist", "setting", "central_conflict"):
            value = fields[field_name].value
            if value is not None and not isinstance(value, str):
                raise BriefValidationError(f"{field_name} must be a string or null")
        for field_name in ("must_include", "must_avoid"):
            value = fields[field_name].value
            if not isinstance(value, tuple) or not all(isinstance(item, str) for item in value):
                raise BriefValidationError(f"{field_name} must be a string tuple")
        freedom = self.creative_freedom.value
        if isinstance(freedom, bool) or not isinstance(freedom, (int, float)):
            raise BriefValidationError("creative_freedom must be a number")

        final_values = BriefValues(
            premise=self.premise.value,
            genre=self.genre.value,
            tone=self.tone.value,
            target_length=self.target_length.value,
            protagonist=self.protagonist.value,
            setting=self.setting.value,
            central_conflict=self.central_conflict.value,
            ending_preference=self.ending_preference.value,
            must_include=self.must_include.value,
            must_avoid=self.must_avoid.value,
            creative_freedom=float(freedom),
        )
        _validate_values(final_values, "StoryBrief")
        _raise_for_constraint_overlap(self.must_include.value, self.must_avoid.value)

    def to_engine_payload(self) -> dict[str, Any]:
        """Return the JSON-compatible, private payload consumed by Arc Engine."""

        fields: dict[str, SourcedValue[Any]] = {
            "premise": self.premise,
            "genre": self.genre,
            "tone": self.tone,
            "target_length": self.target_length,
            "protagonist": self.protagonist,
            "setting": self.setting,
            "central_conflict": self.central_conflict,
            "ending_preference": self.ending_preference,
            "must_include": self.must_include,
            "must_avoid": self.must_avoid,
            "creative_freedom": self.creative_freedom,
        }
        encoded_fields: dict[str, dict[str, Any]] = {}
        for field_name, sourced_value in fields.items():
            value = sourced_value.value
            encoded_fields[field_name] = {
                "value": list(value) if isinstance(value, tuple) else value,
                "source": sourced_value.source.value,
            }

        return {
            "schema_version": self.schema_version,
            "raw_input": self.raw_input,
            "fields": encoded_fields,
            "resolution_notes": list(self.resolution_notes),
        }

    def to_user_view(self) -> dict[str, Any]:
        """Return the creator-visible System Understanding without the original input."""

        engine_payload = self.to_engine_payload()
        return {
            "schema_version": self.schema_version,
            "fields": engine_payload["fields"],
            "resolution_notes": list(self.resolution_notes),
            "generation_policy": {
                "auto_start": True,
                "confirmation_available": True,
            },
        }

    def to_log_context(self) -> dict[str, Any]:
        """Return bounded observability metadata without creative text or field values."""

        fields = self.to_engine_payload()["fields"]
        field_sources = {
            field_name: field_payload["source"] for field_name, field_payload in fields.items()
        }
        return {
            "schema_version": self.schema_version,
            "input_characters": len(self.raw_input),
            "input_sha256": sha256(self.raw_input.encode("utf-8")).hexdigest(),
            "field_sources": field_sources,
        }

    @classmethod
    def from_engine_payload(cls, payload: Mapping[str, Any]) -> StoryBrief:
        """Validate and restore an Arc Story Brief v1 engine payload."""

        if payload.get("schema_version") != STORY_BRIEF_VERSION:
            raise BriefValidationError("unsupported schema_version")
        raw_input = payload.get("raw_input")
        if not isinstance(raw_input, str):
            raise BriefValidationError("raw_input must be a string")
        raw_fields = payload.get("fields")
        if not isinstance(raw_fields, Mapping):
            raise BriefValidationError("fields must be an object")

        expected_fields = {
            "premise",
            "genre",
            "tone",
            "target_length",
            "protagonist",
            "setting",
            "central_conflict",
            "ending_preference",
            "must_include",
            "must_avoid",
            "creative_freedom",
        }
        if set(raw_fields) != expected_fields:
            raise BriefValidationError("fields must contain exactly the Story Brief v1 fields")

        def read_field(field_name: str) -> tuple[Any, FieldSource]:
            node = raw_fields[field_name]
            if not isinstance(node, Mapping) or set(node) != {"value", "source"}:
                raise BriefValidationError(f"fields.{field_name} must contain value and source")
            try:
                source = FieldSource(node["source"])
            except (TypeError, ValueError) as error:
                raise BriefValidationError(f"fields.{field_name}.source is invalid") from error
            return node["value"], source

        @overload
        def read_text(
            field_name: str, *, optional: Literal[False] = False
        ) -> SourcedValue[str]: ...

        @overload
        def read_text(field_name: str, *, optional: Literal[True]) -> SourcedValue[str | None]: ...

        def read_text(
            field_name: str, *, optional: bool = False
        ) -> SourcedValue[str] | SourcedValue[str | None]:
            value, source = read_field(field_name)
            if value is None and optional:
                optional_value: SourcedValue[str | None] = SourcedValue(None, source)
                return optional_value
            if not isinstance(value, str):
                raise BriefValidationError(f"fields.{field_name}.value must be a string")
            return SourcedValue(value, source)

        def read_items(field_name: str) -> SourcedValue[tuple[str, ...]]:
            value, source = read_field(field_name)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise BriefValidationError(f"fields.{field_name}.value must be a string array")
            return SourcedValue(tuple(value), source)

        premise = read_text("premise")
        genre = read_text("genre")
        tone = read_text("tone")
        target_length = read_text("target_length")
        protagonist = read_text("protagonist", optional=True)
        setting = read_text("setting", optional=True)
        central_conflict = read_text("central_conflict", optional=True)
        ending_preference = read_text("ending_preference")
        must_include = read_items("must_include")
        must_avoid = read_items("must_avoid")
        creative_freedom_value, creative_freedom_source = read_field("creative_freedom")
        if isinstance(creative_freedom_value, bool) or not isinstance(
            creative_freedom_value, (int, float)
        ):
            raise BriefValidationError("fields.creative_freedom.value must be a number")
        creative_freedom = SourcedValue(float(creative_freedom_value), creative_freedom_source)

        raw_notes = payload.get("resolution_notes", [])
        if not isinstance(raw_notes, list) or not all(isinstance(note, str) for note in raw_notes):
            raise BriefValidationError("resolution_notes must be a string array")

        restored_values = BriefValues(
            premise=premise.value,
            genre=genre.value,
            tone=tone.value,
            target_length=target_length.value,
            protagonist=protagonist.value,
            setting=setting.value,
            central_conflict=central_conflict.value,
            ending_preference=ending_preference.value,
            must_include=must_include.value,
            must_avoid=must_avoid.value,
            creative_freedom=creative_freedom.value,
        )
        _validate_values(restored_values, "fields")
        _raise_for_constraint_overlap(must_include.value, must_avoid.value)

        return cls(
            raw_input=raw_input,
            premise=SourcedValue(premise.value, premise.source),
            genre=SourcedValue(genre.value, genre.source),
            tone=SourcedValue(tone.value, tone.source),
            target_length=SourcedValue(target_length.value, target_length.source),
            protagonist=protagonist,
            setting=setting,
            central_conflict=central_conflict,
            ending_preference=SourcedValue(ending_preference.value, ending_preference.source),
            must_include=must_include,
            must_avoid=must_avoid,
            creative_freedom=creative_freedom,
            resolution_notes=tuple(raw_notes),
        )


def _raise_for_constraint_overlap(
    must_include: tuple[str, ...],
    must_avoid: tuple[str, ...],
) -> None:
    include_keys = {item.strip().casefold() for item in must_include if item.strip()}
    avoid_keys = {item.strip().casefold() for item in must_avoid if item.strip()}
    overlap = sorted(include_keys & avoid_keys)
    if overlap:
        joined = ", ".join(overlap)
        raise BriefConflictError(f"must_include and must_avoid conflict: {joined}")


def _looks_like_single_sentence(value: str) -> bool:
    if "\n" in value or len(value) > 280:
        return False
    sentence_endings = findall(r"[.!?。！？]+", value)
    return len(sentence_endings) <= 1


def interpret_story_brief(
    raw_input: str = "",
    *,
    input_mode: CreativeInputMode = CreativeInputMode.AUTO,
    explicit: BriefValues | None = None,
    inferred: BriefValues | None = None,
) -> StoryBrief:
    """Create a complete Story Brief using deterministic defaults."""

    default = FieldSource.DEFAULT
    explicit_values = explicit or BriefValues()
    inferred_values = inferred or BriefValues()
    _validate_values(explicit_values, "explicit")
    _validate_values(inferred_values, "inferred")
    resolution_notes: list[str] = []
    normalized_input = raw_input.strip()

    if not isinstance(input_mode, CreativeInputMode):
        raise BriefValidationError("input_mode must be auto, premise, or freeform")

    raw_is_premise = bool(normalized_input) and (
        input_mode is CreativeInputMode.PREMISE
        or (input_mode is CreativeInputMode.AUTO and _looks_like_single_sentence(normalized_input))
    )

    if explicit_values.premise is not None:
        premise = SourcedValue(explicit_values.premise, FieldSource.EXPLICIT)
        if (
            inferred_values.premise is not None
            and explicit_values.premise != inferred_values.premise
        ):
            resolution_notes.append("premise: explicit value overrides inferred value")
    elif raw_is_premise:
        premise = SourcedValue(normalized_input, FieldSource.EXPLICIT)
        if inferred_values.premise is not None and normalized_input != inferred_values.premise:
            resolution_notes.append("premise: explicit value overrides inferred value")
    elif inferred_values.premise is not None:
        premise = SourcedValue(inferred_values.premise, FieldSource.INFERRED)
    else:
        premise = SourcedValue(DEFAULT_PREMISE, default)

    def choose(
        field_name: str,
        explicit_value: T | None,
        inferred_value: T | None,
        fallback: T,
    ) -> SourcedValue[T]:
        if explicit_value is not None:
            if inferred_value is not None and explicit_value != inferred_value:
                resolution_notes.append(f"{field_name}: explicit value overrides inferred value")
            return SourcedValue(explicit_value, FieldSource.EXPLICIT)
        if inferred_value is not None:
            return SourcedValue(inferred_value, FieldSource.INFERRED)
        return SourcedValue(fallback, default)

    must_include = choose(
        "must_include", explicit_values.must_include, inferred_values.must_include, ()
    )
    must_avoid = choose("must_avoid", explicit_values.must_avoid, inferred_values.must_avoid, ())
    _raise_for_constraint_overlap(must_include.value, must_avoid.value)

    return StoryBrief(
        raw_input=raw_input,
        premise=premise,
        genre=choose("genre", explicit_values.genre, inferred_values.genre, DEFAULT_GENRE),
        tone=choose("tone", explicit_values.tone, inferred_values.tone, DEFAULT_TONE),
        target_length=choose(
            "target_length",
            explicit_values.target_length,
            inferred_values.target_length,
            DEFAULT_TARGET_LENGTH,
        ),
        protagonist=choose(
            "protagonist",
            explicit_values.protagonist,
            inferred_values.protagonist,
            DEFAULT_BRIEF_VALUES.protagonist,
        ),
        setting=choose(
            "setting",
            explicit_values.setting,
            inferred_values.setting,
            DEFAULT_BRIEF_VALUES.setting,
        ),
        central_conflict=choose(
            "central_conflict",
            explicit_values.central_conflict,
            inferred_values.central_conflict,
            DEFAULT_BRIEF_VALUES.central_conflict,
        ),
        ending_preference=choose(
            "ending_preference",
            explicit_values.ending_preference,
            inferred_values.ending_preference,
            DEFAULT_ENDING_PREFERENCE,
        ),
        must_include=must_include,
        must_avoid=must_avoid,
        creative_freedom=choose(
            "creative_freedom",
            explicit_values.creative_freedom,
            inferred_values.creative_freedom,
            DEFAULT_CREATIVE_FREEDOM,
        ),
        resolution_notes=tuple(resolution_notes),
    )
