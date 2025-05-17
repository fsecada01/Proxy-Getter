import asyncio
from typing import Any

import httpx
from sqlalchemy import Row, update
from sqlmodel import col, select

try:
    from backend.logging import logger
except ImportError:
    from loguru import logger

from .db import session_maker
from .models import ProxyUrl


async def get_proxy_list(unvalidated: bool = True) -> list[Row]:
    """

    Args:
        unvalidated: bool = True

    Returns:
        Scalars

    """
    stmnt = select(ProxyUrl.url, ProxyUrl.proxy_type)
    if unvalidated:
        stmnt = stmnt.where(ProxyUrl.validated == False)  # noqa

    with session_maker() as session:
        results = session.exec(stmnt)
        rows = results.all()

    return rows


async def update_proxy_urls(urls: list[str], values: dict[str, str | Any]):
    """

    Args:
        values: dict[str, str|Any]
        urls: list[str]
    """
    stmnt = (
        update(ProxyUrl)
        .where(col(ProxyUrl.url).in_(urls))
        .values(**values)
        .returning(ProxyUrl)
    )

    with session_maker() as session:
        results = session.exec(stmnt)
        rows = results.all()
        # session.add_all(rows)
        session.commit()

    return rows if rows else None


async def check_proxy_urls(unvalidated: bool = True):
    """
    Function to check for all unvalidated proxies
    """
    rows = await get_proxy_list(unvalidated=unvalidated)

    proxy_urls = [f"{row.proxy_type.value}://{row.url}" for row in rows]

    def _make_request(url: str, proxy_url: str):
        return_obj = None
        logger.info(
            f"Going to test proxy address {proxy_url} against URL {url} now."
        )
        try:
            proxies = {"any://": httpx.HTTPTransport(proxy=proxy_url)}
            client = httpx.Client(
                mounts=proxies,
                verify=False if "https" not in proxy_url else True,
            )
            r = client.head(
                url=url,
                timeout=60.0,
                follow_redirects=True,
            )
            if r.status_code == 200:
                return_obj = proxy_url

        except Exception as e:
            logger.debug(
                f"There was an error when making a HEAD request. See here: {type(e), e, e.args}"
            )

        return return_obj

    url = "https://www.google.com"
    # url = "https://www.yahoo.com"

    loop = asyncio.get_running_loop()

    tasks = list(
        map(
            lambda proxy: loop.run_in_executor(None, _make_request, url, proxy),
            proxy_urls,
        )
    )

    searched_urls = [row.url for row in rows]

    await update_proxy_urls(urls=searched_urls, values={"searched": True})

    proxy_urls = await asyncio.gather(*tasks)

    urls = [x.split("//")[1] for x in proxy_urls if x]

    rows = await update_proxy_urls(urls=urls, values={"validated": True})

    return rows


if __name__ == "__main__":
    asyncio.run(check_proxy_urls())
