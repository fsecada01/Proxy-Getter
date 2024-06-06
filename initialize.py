import asyncio

from free_verify_proxy.proxy import proxyLists
from sqlalchemy import create_engine
from sqlmodel import Session

from backend.proxies.consts import sqlite_address
from backend.proxies.models import ProxyUrl
from backend.utils import set_event_loop, windows_sys_event_loop_check


async def initialize():
    proxy_obj = proxyLists()
    proxy_list = proxy_obj.get_free_proxy_lists()

    ProxyUrl.set_session(Session(create_engine(sqlite_address)))

    model_insts = list(
        map(
            lambda url: ProxyUrl.create(url=url),
            proxy_list,
        )
    )

    return model_insts


if __name__ == "__main__":
    windows_sys_event_loop_check()
    set_event_loop()

    asyncio.run(initialize())
