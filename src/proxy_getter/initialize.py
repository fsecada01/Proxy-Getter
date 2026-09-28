import asyncio

from sqlalchemy.exc import OperationalError

from proxy_getter.db import engine
from proxy_getter.models import ProxyUrl


async def main():
    """
    The main function to initialize the whole `proxies` application. The
    function writes the SQL tables to the SQLite instance, leaving an
    existing table alone.
    """
    try:
        ProxyUrl.__table__.create(engine, checkfirst=True)
    except OperationalError as exc:
        # Another process sharing the file created it between the check
        # and the CREATE.
        if "already exists" not in str(exc):
            raise


if __name__ == "__main__":
    asyncio.run(main())
