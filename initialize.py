import asyncio

from backend.proxies.db import engine
from backend.proxies.models import ProxyUrl
from backend.utils import set_event_loop, windows_sys_event_loop_check


async def main():
    """
    The main function to initialize the whole `proxies` application. The
    function writes the SQL tables to the SQLite instance.
    """
    ProxyUrl.__table__.create(engine)


if __name__ == "__main__":
    windows_sys_event_loop_check()
    set_event_loop()

    asyncio.run(main())
