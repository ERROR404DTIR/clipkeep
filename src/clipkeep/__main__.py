import sys
from app import App


def main() -> int:
    return App().exec()


if __name__ == "__main__":
    raise SystemExit(main())
