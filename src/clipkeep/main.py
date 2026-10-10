import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import app directly
sys.path.insert(0, str(Path(__file__).parent))

# Import the app module directly
from app import App


def main() -> int:
    return App().exec()


if __name__ == "__main__":
    raise SystemExit(main())