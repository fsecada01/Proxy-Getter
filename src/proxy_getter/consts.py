import os
from pathlib import Path

try:
    from backend.settings.consts import BASE_DIR
except ImportError:
    BASE_DIR = Path(__file__).parent.resolve()

URLs = [  # for testing proxies
    "https://www.google.com",
    "https://www.yahoo.com",
    "https://www.cnn.com",
    "https://barefootcontessa.com",
]

# PROXY_DB_PATH puts the database elsewhere, e.g. in a bind-mounted
# directory: SQLite writes its journal beside the database, so a container
# needs the whole directory mounted, not just the file. It is a file path;
# "~" is expanded and a relative path is made absolute against the working
# directory at import, so every process agrees on one file.
DB_PATH = (
    Path(os.environ.get("PROXY_DB_PATH") or BASE_DIR / "proxy_urls.db")
    .expanduser()
    .resolve()
)

sqlite_address = f"sqlite:///{DB_PATH}"
