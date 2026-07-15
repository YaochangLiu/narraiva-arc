from __future__ import annotations

import argparse

from narraiva_arc import PRODUCT_NAME, __version__


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
    args = parser.parse_args()

    if args.version:
        print(f"{PRODUCT_NAME} {__version__}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
