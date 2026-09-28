import asyncio

from proxy_getter.db import engine
from proxy_getter.models import ProxyUrl


async def main():
    """
    The main function to initialize the whole `proxies` application. The
    function writes the SQL tables to the SQLite instance, leaving an
    existing table alone.
    """
    ProxyUrl.__table__.create(engine, checkfirst=True)


if __name__ == "__main__":
    asyncio.run(main())
