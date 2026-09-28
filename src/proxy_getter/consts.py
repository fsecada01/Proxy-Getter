import os
import warnings
from pathlib import Path

_HOST_MODULES = ("backend", "backend.settings", "backend.settings.consts")


def _default_base_dir() -> Path:
    """
    Where the database goes when PROXY_DB_PATH is unset: the host app's
    ``backend.settings.consts.BASE_DIR`` if it has one, else this package.

    Only a missing ``backend`` module counts as "no host". An error raised
    while the host's settings import (a missing dependency, failed
    validation) propagates, rather than silently moving the database.

    Returns:
        Path: the directory (hosts define BASE_DIR as a str or a Path)
    """
    try:
        from backend.settings.consts import BASE_DIR
    except ModuleNotFoundError as exc:
        if exc.name not in _HOST_MODULES:
            raise
        return Path(__file__).parent.resolve()

    return Path(BASE_DIR)


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
# directory at import, so every process agrees on one file. When it is set,
# the host app's settings are not imported at all.
_env_path = os.environ.get("PROXY_DB_PATH")
DB_PATH = (
    Path(_env_path or _default_base_dir() / "proxy_urls.db")
    .expanduser()
    .resolve()
)

sqlite_address = f"sqlite:///{DB_PATH}"


def __getattr__(name):
    # BASE_DIR was public through 0.1.2.
    if name == "BASE_DIR":
        warnings.warn(
            "proxy_getter.consts.BASE_DIR is deprecated; use DB_PATH",
            DeprecationWarning,
            stacklevel=2,
        )
        return _default_base_dir()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
