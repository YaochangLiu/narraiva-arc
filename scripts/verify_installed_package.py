"""Verify a built Arc wheel through only its installed public interface."""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

from narraiva_arc import (
    ArcEngine,
    EngineStage,
    GenerationRequest,
    GenerationStatus,
    JsonFileCheckpointStore,
    __version__,
    compatibility_manifest,
)


def main() -> int:
    manifest = compatibility_manifest()
    if version("narraiva-arc") != __version__ or manifest["package_version"] != __version__:
        raise RuntimeError("Arc wheel metadata and runtime package versions differ")

    with TemporaryDirectory(prefix="narraiva-arc-compat-") as directory:
        checkpoint_dir = Path(directory) / "checkpoints"
        paused = ArcEngine.offline(JsonFileCheckpointStore(checkpoint_dir)).run(
            GenerationRequest.from_input(
                "A lighthouse keeper discovers that the fog remembers names.",
                pause_after=EngineStage.PLANNED,
            )
        )
        if paused.status is not GenerationStatus.PAUSED or paused.checkpoint_id is None:
            raise RuntimeError("Arc wheel did not create a resumable planned checkpoint")

        resumed = ArcEngine.offline(JsonFileCheckpointStore(checkpoint_dir)).resume(
            paused.checkpoint_id
        )

    if resumed.status is not GenerationStatus.COMPLETED or resumed.artifact is None:
        raise RuntimeError("Arc wheel did not complete deterministic offline generation")
    expected_stages = tuple(stage.value for stage in EngineStage)
    if tuple(event.stage.value for event in resumed.events) != expected_stages:
        raise RuntimeError("Arc wheel emitted an incompatible stage sequence")
    if not resumed.artifact.markdown.startswith("# "):
        raise RuntimeError("Arc wheel did not produce a Markdown story artifact")
    if resumed.artifact.version != manifest["story_artifact_version"]:
        raise RuntimeError("Arc wheel artifact version differs from its compatibility manifest")

    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
