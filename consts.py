from backend.settings.consts import BASE_DIR

URLs = [  # for testing proxies
    "https://www.google.com",
    "https://www.yahoo.com",
    "https://www.cnn.com",
    "https://barefootcontessa.com",
]

sqlite_address = f"sqlite:///{BASE_DIR}/proxy_urls.db"
