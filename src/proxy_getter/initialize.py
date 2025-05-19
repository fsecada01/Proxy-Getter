import asyncio

from models import ProxyUrl

from proxy_getter.db import engine


async def main():
    """
    The main function to initialize the whole `proxies` application. The
    function writes the SQL tables to the SQLite instance.
    """
    ProxyUrl.__table__.create(engine)


if __name__ == "__main__":
    asyncio.run(main())
