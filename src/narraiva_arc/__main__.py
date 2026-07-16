from __future__ import annotations

import argparse
import json

from narraiva_arc import PRODUCT_NAME, __version__, compatibility_manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="narraiva-arc",
        description="Inspect the Narraiva Arc package baseline.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="show the installed package version",
    )
    parser.add_argument(
        "--compatibility",
        action="store_true",
        help="show the installed package and contract identity as JSON",
    )
    args = parser.parse_args()

    if args.version:
        print(f"{PRODUCT_NAME} {__version__}")
        return 0
    if args.compatibility:
        print(json.dumps(compatibility_manifest(), sort_keys=True))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
