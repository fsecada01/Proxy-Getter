"""A proxy caller for Spys proxy service"""

import asyncio

from backend.logging import logger
from backend.proxies.db import session_maker
from backend.proxies.models import ProxyList, ProxyUrl
from backend.proxies.spys_one.utils import get_data_from_rows, get_proxy_request
from backend.utils import set_event_loop, windows_sys_event_loop_check


@logger.catch
async def main():
    """
    The man function that will run a series of commands to call the
    prescribed URL, process the HTML rows and embedded columns, convert them
    into JSON, validate via Pydantic, and save `ProxyUrl` instances.
    Returns:
        list[ProxyList]

    """
    url = "https://spys.one/free-proxy-list/US/"
    resp = await get_proxy_request(url=url)

    rows = resp.html.find("tr[class*='spy1x']")

    header, data = await get_data_from_rows(rows=rows)

    payload = list(map(lambda row: dict(zip(header, row)), data))

    proxy_list = [ProxyList.model_construct(**row) for row in payload]

    instances = list(
        map(lambda inst: inst.get_proxy_url_instance(), proxy_list)
    )

    with session_maker() as session:
        ProxyUrl.set_session(session)
        rows = ProxyUrl.bulk_create(objs=instances)

    return rows if rows else None


if __name__ == "__main__":
    windows_sys_event_loop_check()
    set_event_loop()

    asyncio.run(main())
