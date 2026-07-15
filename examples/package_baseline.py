"""Verify that the Narraiva Arc package can be imported after local installation."""

from narraiva_arc import PRODUCT_NAME, __version__


def main() -> None:
    print(f"{PRODUCT_NAME} {__version__}: package baseline ready; engine not migrated")


if __name__ == "__main__":
    main()
