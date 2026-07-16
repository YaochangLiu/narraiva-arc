from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import narraiva_arc

ROOT = Path(__file__).resolve().parents[1]


def test_public_package_exposes_product_identity() -> None:
    assert narraiva_arc.PRODUCT_NAME == "Narraiva Arc"
    assert narraiva_arc.__version__ == "0.1.0.dev0"


def test_package_metadata_and_runtime_version_have_one_release_identity() -> None:
    with (ROOT / "pyproject.toml").open("rb") as stream:
        pyproject = tomllib.load(stream)

    project = pyproject["project"]
    assert project["name"] == "narraiva-arc"
    assert project["dynamic"] == ["version"]
    assert pyproject["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "narraiva_arc._version.__version__"
    }


def test_public_compatibility_manifest_covers_every_portable_contract() -> None:
    assert narraiva_arc.compatibility_manifest() == {
        "manifest_version": "arc.compatibility-manifest/v1",
        "package_name": "narraiva-arc",
        "package_version": "0.1.0.dev0",
        "story_brief_version": "arc.story-brief/v1",
        "generation_request_version": "arc.generation-request/v1",
        "generation_result_version": "arc.generation-result/v1",
        "stage_event_version": "arc.stage-event/v1",
        "checkpoint_version": "arc.engine-checkpoint/v1",
        "story_artifact_version": "arc.story-artifact/v1",
    }


def test_module_entrypoint_reports_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "narraiva_arc", "--version"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )

    assert result.stdout.strip() == "Narraiva Arc 0.1.0.dev0"


def test_module_entrypoint_reports_machine_readable_compatibility() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "narraiva_arc", "--compatibility"],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
    )

    assert json.loads(result.stdout) == narraiva_arc.compatibility_manifest()
