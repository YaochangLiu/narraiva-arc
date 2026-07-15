"""Verify that runtime dependency declarations match the license inventory."""

from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with (ROOT / "pyproject.toml").open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file)["project"]

    runtime_dependencies = project.get("dependencies", [])
    inventory = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")

    if runtime_dependencies:
        print("Runtime dependencies require explicit license inventory review:")
        for dependency in runtime_dependencies:
            print(f"- {dependency}")
        return 1
    if "no runtime dependencies" not in inventory.lower():
        print("THIRD_PARTY_LICENSES.md must record the empty runtime dependency baseline.")
        return 1

    print("Dependency license inventory check passed: no runtime dependencies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
