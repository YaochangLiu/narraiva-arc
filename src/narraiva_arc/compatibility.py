"""Machine-readable package and portable-contract compatibility identity."""

from __future__ import annotations

from narraiva_arc._version import __version__
from narraiva_arc.brief import STORY_BRIEF_VERSION
from narraiva_arc.engine import (
    ENGINE_CHECKPOINT_VERSION,
    GENERATION_REQUEST_VERSION,
    GENERATION_RESULT_VERSION,
    STAGE_EVENT_VERSION,
    STORY_ARTIFACT_VERSION,
)

COMPATIBILITY_MANIFEST_VERSION = "arc.compatibility-manifest/v1"


def compatibility_manifest() -> dict[str, str]:
    """Return the complete public identity a host must pin and validate."""
    return {
        "manifest_version": COMPATIBILITY_MANIFEST_VERSION,
        "package_name": "narraiva-arc",
        "package_version": __version__,
        "story_brief_version": STORY_BRIEF_VERSION,
        "generation_request_version": GENERATION_REQUEST_VERSION,
        "generation_result_version": GENERATION_RESULT_VERSION,
        "stage_event_version": STAGE_EVENT_VERSION,
        "checkpoint_version": ENGINE_CHECKPOINT_VERSION,
        "story_artifact_version": STORY_ARTIFACT_VERSION,
    }
