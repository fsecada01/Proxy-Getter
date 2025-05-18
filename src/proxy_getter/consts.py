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

sqlite_address = f"sqlite:///{BASE_DIR}/proxy_urls.db"
