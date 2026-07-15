"""Fail when the repository baseline contains private or generated material."""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = {
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "NOTICE",
    "README.md",
    "SECURITY.md",
    "THIRD_PARTY_LICENSES.md",
    "TRADEMARKS.md",
}
DENIED_NAMES = {
    ".env",
    "id_dsa",
    "id_ed25519",
    "id_rsa",
}
DENIED_PARTS = {
    "exports",
    "generated",
    "logs",
    "manuscripts",
    "stories",
    "user-content",
}
DENIED_GLOBS = (
    "*.db",
    "*.key",
    "*.pem",
    "*.sqlite",
    "*.sqlite3",
    "*.sqlite-*",
    ".env.*",
)
ALLOWED_ENV_FILES = {".env.example", ".env.template"}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line]


def policy_violations(paths: list[str]) -> list[str]:
    violations: list[str] = []
    for raw_path in paths:
        path = PurePosixPath(raw_path)
        lowered_parts = {part.lower() for part in path.parts}
        name = path.name.lower()

        if name in DENIED_NAMES:
            violations.append(raw_path)
            continue
        if lowered_parts & DENIED_PARTS:
            violations.append(raw_path)
            continue
        if name not in ALLOWED_ENV_FILES and any(
            fnmatch.fnmatch(name, pattern) for pattern in DENIED_GLOBS
        ):
            violations.append(raw_path)

    return violations


def main() -> int:
    missing = sorted(name for name in REQUIRED_FILES if not (ROOT / name).is_file())
    violations = policy_violations(tracked_files())

    if missing:
        print("Missing repository baseline files:")
        for name in missing:
            print(f"- {name}")
    if violations:
        print("Tracked private or generated material:")
        for path in violations:
            print(f"- {path}")

    if missing or violations:
        return 1

    print("Repository policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
