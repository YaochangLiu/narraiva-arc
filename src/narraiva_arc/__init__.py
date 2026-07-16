"""Public package identity for Narraiva Arc."""

from narraiva_arc._version import __version__
from narraiva_arc.compatibility import compatibility_manifest
from narraiva_arc.engine import (
    ArcEngine,
    CheckpointNotFoundError,
    CheckpointStore,
    DeterministicStoryProvider,
    EngineStage,
    GenerationContractError,
    GenerationRequest,
    GenerationResult,
    GenerationStatus,
    InMemoryCheckpointStore,
    JsonFileCheckpointStore,
    KeywordSafetyGate,
    SafetyGate,
    StageEvent,
    StoryArtifact,
    StoryProvider,
)

PRODUCT_NAME = "Narraiva Arc"
__all__ = [
    "PRODUCT_NAME",
    "ArcEngine",
    "CheckpointNotFoundError",
    "CheckpointStore",
    "DeterministicStoryProvider",
    "EngineStage",
    "GenerationContractError",
    "GenerationRequest",
    "GenerationResult",
    "GenerationStatus",
    "InMemoryCheckpointStore",
    "JsonFileCheckpointStore",
    "KeywordSafetyGate",
    "SafetyGate",
    "StageEvent",
    "StoryArtifact",
    "StoryProvider",
    "__version__",
    "compatibility_manifest",
]
