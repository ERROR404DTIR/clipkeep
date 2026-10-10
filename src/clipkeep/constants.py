APP_NAME = "clipkeep"
APP_ID = "com.clipkeep.Clipkeep"
VERSION = "0.1.0"

MAX_RECENT_ITEMS = 200
MAX_TEXT_LENGTH = 100_000
MAX_IMAGE_SIZE = 2_000_000
DEFAULT_HOTKEY = "Insert"
DB_NAME = "clipkeep.db"


def get_data_dir() -> str:
    import os
    data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    return os.path.join(data_home, APP_NAME)


def get_db_path() -> str:
    import os
    return os.path.join(get_data_dir(), DB_NAME)
