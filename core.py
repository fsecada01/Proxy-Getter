import asyncio

import httpx
from sqlalchemy import Row, update
from sqlmodel import col, select

from backend.proxies.db import session_maker
from backend.proxies.models import ProxyUrl
from backend.utils import set_event_loop, windows_sys_event_loop_check


async def get_proxy_list(unvalidated: bool = True) -> list[Row]:
    """

    Args:
        unvalidated: bool = True

    Returns:
        Scalars

    """
    stmnt = select(ProxyUrl.url)
    if unvalidated:
        stmnt = stmnt.where(ProxyUrl.validated == False)  # noqa

    with session_maker() as session:
        results = session.exec(stmnt)
        rows = results.all()

    return rows


async def update_proxy_urls(urls: list[str]):
    """

    Args:
        urls: list[str]
    """
    stmnt = (
        update(ProxyUrl)
        .where(col(ProxyUrl.url).in_(urls))
        .values(validated=True)
    )

    with session_maker() as session:
        results = session.exec(stmnt)
        rows = results.all()

    return rows if rows else None


async def check_proxy_urls(unvalidated: bool = True):
    """
    Function to check for all unvalidated proxies
    """
    rows = await get_proxy_list(unvalidated=unvalidated)

    def _make_request(url: str, proxy_url: str):
        r = httpx.head(url=url, proxy=f"https://{proxy_url}")

        return proxy_url if r.status_code == 200 else None

    url = "https://www.google.com"

    windows_sys_event_loop_check()
    loop = asyncio.get_running_loop()

    tasks = list(
        map(
            lambda proxy: loop.run_in_executor(None, _make_request, url, proxy),
            [row.url for row in rows],
        )
    )

    proxy_urls = await asyncio.gather(*tasks)

    rows = await update_proxy_urls(urls=proxy_urls)

    return rows


if __name__ == "__main__":
    windows_sys_event_loop_check()
    set_event_loop()

    asyncio.run(check_proxy_urls())
