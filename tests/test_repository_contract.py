from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_declares_apache_2_license() -> None:
    with (ROOT / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    assert pyproject["project"]["license"]["text"] == "Apache-2.0"
    assert (ROOT / "LICENSE").is_file()
    assert (ROOT / "NOTICE").is_file()


def test_repository_policy_checker_accepts_tracked_tree() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_repository_policy.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_dependency_license_inventory_matches_runtime_dependencies() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_license_inventory.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_engine_source_has_no_host_framework_imports() -> None:
    banned_roots = {"fastapi", "flask", "django", "vue", "novelos_cloud_server"}
    imported_roots: set[str] = set()

    for source_path in (ROOT / "src" / "narraiva_arc").rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(banned_roots)
