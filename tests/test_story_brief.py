from copy import deepcopy
from dataclasses import replace

import pytest

from narraiva_arc.brief import (
    BriefConflictError,
    BriefValidationError,
    BriefValues,
    FieldSource,
    SourcedValue,
    StoryBrief,
    interpret_story_brief,
)


def test_zero_input_produces_a_complete_default_brief() -> None:
    brief = interpret_story_brief()

    assert brief.schema_version == "arc.story-brief/v1"
    assert brief.premise.value == "An unexpected choice changes an ordinary life."
    assert brief.premise.source is FieldSource.DEFAULT
    assert brief.genre.value == "general fiction"
    assert brief.genre.source is FieldSource.DEFAULT
    assert brief.target_length.value == "short"
    assert brief.creative_freedom.value == 0.8


def test_one_sentence_becomes_an_explicit_premise() -> None:
    brief = interpret_story_brief(
        "A clockmaker discovers that every repaired watch erases a memory."
    )

    assert brief.raw_input == "A clockmaker discovers that every repaired watch erases a memory."
    assert (
        brief.premise.value == "A clockmaker discovers that every repaired watch erases a memory."
    )
    assert brief.premise.source is FieldSource.EXPLICIT
    assert brief.genre.source is FieldSource.DEFAULT


def test_free_form_input_uses_structured_inference_without_claiming_it_was_explicit() -> None:
    raw_input = (
        "Maybe a city on the moon. The lead repairs old machines; I want grief, but also hope. "
        "There should be a red garden and perhaps a vanished sibling."
    )
    brief = interpret_story_brief(
        raw_input,
        inferred=BriefValues(
            premise="A lunar mechanic searches a forbidden garden for her vanished sibling.",
            genre="science fiction",
            tone="melancholic but hopeful",
            protagonist="a lunar mechanic",
            setting="a city on the moon",
            central_conflict="finding her sibling risks exposing the city's hidden history",
            must_include=("red garden",),
        ),
    )

    assert brief.raw_input == raw_input
    assert (
        brief.premise.value
        == "A lunar mechanic searches a forbidden garden for her vanished sibling."
    )
    assert brief.premise.source is FieldSource.INFERRED
    assert brief.genre.value == "science fiction"
    assert brief.genre.source is FieldSource.INFERRED
    assert brief.protagonist.source is FieldSource.INFERRED
    assert brief.must_include.value == ("red garden",)
    assert brief.must_include.source is FieldSource.INFERRED
    assert brief.target_length.source is FieldSource.DEFAULT


def test_explicit_settings_override_inference_and_record_the_resolution() -> None:
    brief = interpret_story_brief(
        "A detective investigates impossible footprints.",
        inferred=BriefValues(genre="fantasy", tone="whimsical", target_length="short"),
        explicit=BriefValues(genre="mystery", target_length="long", creative_freedom=0.25),
    )

    assert brief.genre.value == "mystery"
    assert brief.genre.source is FieldSource.EXPLICIT
    assert brief.tone.value == "whimsical"
    assert brief.tone.source is FieldSource.INFERRED
    assert brief.target_length.value == "long"
    assert brief.target_length.source is FieldSource.EXPLICIT
    assert brief.creative_freedom.value == 0.25
    assert brief.creative_freedom.source is FieldSource.EXPLICIT
    assert "genre: explicit value overrides inferred value" in brief.resolution_notes
    assert "target_length: explicit value overrides inferred value" in brief.resolution_notes


def test_contradictory_explicit_constraints_are_rejected() -> None:
    with pytest.raises(BriefConflictError, match="red garden"):
        interpret_story_brief(
            "A gardener protects a lunar city.",
            explicit=BriefValues(
                must_include=("Red Garden",),
                must_avoid=(" red garden ",),
            ),
        )


@pytest.mark.parametrize(
    ("explicit", "message"),
    [
        (BriefValues(creative_freedom=1.1), "creative_freedom"),
        (BriefValues(target_length="epic"), "target_length"),
        (BriefValues(genre="   "), "genre"),
        (BriefValues(must_include=("",)), "must_include"),
    ],
)
def test_invalid_structured_values_are_rejected(
    explicit: BriefValues,
    message: str,
) -> None:
    with pytest.raises(BriefValidationError, match=message):
        interpret_story_brief("A valid premise.", explicit=explicit)


def test_engine_payload_is_versioned_json_data_and_round_trips() -> None:
    brief = interpret_story_brief(
        "A lighthouse keeper hears tomorrow's distress calls.",
        inferred=BriefValues(genre="speculative fiction", setting="an isolated lighthouse"),
        explicit=BriefValues(tone="tense", must_avoid=("graphic violence",)),
    )

    payload = brief.to_engine_payload()

    assert payload["schema_version"] == "arc.story-brief/v1"
    assert payload["raw_input"] == "A lighthouse keeper hears tomorrow's distress calls."
    assert payload["fields"]["genre"] == {
        "value": "speculative fiction",
        "source": "inferred",
    }
    assert payload["fields"]["tone"] == {"value": "tense", "source": "explicit"}
    assert payload["fields"]["must_avoid"] == {
        "value": ["graphic violence"],
        "source": "explicit",
    }
    assert StoryBrief.from_engine_payload(payload) == brief


def test_user_view_and_log_context_do_not_expose_raw_creative_input() -> None:
    raw_input = "PRIVATE NOTE: use the family story, but never print this note in logs."
    brief = interpret_story_brief(
        raw_input,
        inferred=BriefValues(premise="A family secret reshapes three generations."),
    )

    user_view = brief.to_user_view()
    log_context = brief.to_log_context()

    assert "raw_input" not in user_view
    assert user_view["fields"]["premise"] == {
        "value": "A family secret reshapes three generations.",
        "source": "inferred",
    }
    assert user_view["generation_policy"] == {
        "auto_start": True,
        "confirmation_available": True,
    }
    assert set(log_context) == {
        "schema_version",
        "input_characters",
        "input_sha256",
        "field_sources",
    }
    assert log_context["input_characters"] == len(raw_input)
    assert raw_input not in repr(log_context)
    assert "family story" not in repr(log_context)


def test_engine_payload_rejects_unknown_versions_and_field_sources() -> None:
    payload = interpret_story_brief("A valid premise.").to_engine_payload()
    unknown_version = deepcopy(payload)
    unknown_version["schema_version"] = "arc.story-brief/v2"
    unknown_source = deepcopy(payload)
    unknown_source["fields"]["genre"]["source"] = "model_guess"

    with pytest.raises(BriefValidationError, match="schema_version"):
        StoryBrief.from_engine_payload(unknown_version)
    with pytest.raises(BriefValidationError, match="genre.source"):
        StoryBrief.from_engine_payload(unknown_source)


def test_story_brief_cannot_be_constructed_with_invalid_invariants() -> None:
    valid = interpret_story_brief("A valid premise.")

    with pytest.raises(BriefValidationError, match="schema_version"):
        replace(valid, schema_version="arc.story-brief/v2")
    with pytest.raises(BriefValidationError, match="creative_freedom"):
        replace(
            valid,
            creative_freedom=SourcedValue(2.0, FieldSource.EXPLICIT),
        )


def test_field_source_cannot_misrepresent_value_provenance() -> None:
    valid = interpret_story_brief("A valid premise.")

    with pytest.raises(BriefValidationError, match="genre.*default"):
        replace(
            valid,
            genre=SourcedValue("mystery", FieldSource.DEFAULT),
        )
    with pytest.raises(BriefValidationError, match="protagonist.*inferred"):
        replace(
            valid,
            protagonist=SourcedValue(None, FieldSource.INFERRED),
        )
