from __future__ import annotations

import subprocess
import sys

import narraiva_arc


def test_public_package_exposes_product_identity() -> None:
    assert narraiva_arc.PRODUCT_NAME == "Narraiva Arc"
    assert narraiva_arc.__version__ == "0.1.0.dev0"


def test_module_entrypoint_reports_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "narraiva_arc", "--version"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "Narraiva Arc 0.1.0.dev0"
