import asyncio
from typing import Any

import httpx
from sqlalchemy import Row, update
from sqlmodel import col, select

try:
    from backend.logging import logger
except ImportError:
    from loguru import logger

from proxy_getter.db import session_maker
from proxy_getter.models import ProxyUrl

CHECK_CONCURRENCY = 200
CHECK_TIMEOUT = 10.0  # per connect/read/write phase
CHECK_DEADLINE = 20.0  # whole check, seconds


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

    url = "https://www.google.com"
    # url = "https://www.yahoo.com"

    # Most free proxies are dead or crawl. httpx's timeout is per phase, so
    # a proxy that trickles bytes can run for minutes; wait_for enforces a
    # wall-clock deadline per check, and the semaphore caps sockets in use.
    sem = asyncio.Semaphore(CHECK_CONCURRENCY)

    async def _make_request(proxy_url: str) -> str | None:
        async with sem:
            logger.debug(f"Testing proxy {proxy_url} against {url}")
            try:
                # `proxy=` routes every request through the proxy; the old
                # "any://" mount matched nothing, so requests went direct
                # and every proxy "validated".
                async with httpx.AsyncClient(
                    proxy=proxy_url, timeout=CHECK_TIMEOUT
                ) as client:
                    r = await asyncio.wait_for(
                        client.head(url=url, follow_redirects=True),
                        CHECK_DEADLINE,
                    )
                if r.status_code == 200:
                    return proxy_url
            except Exception as e:
                logger.debug(f"Proxy {proxy_url} failed: {type(e), e}")

        return None

    searched_urls = [row.url for row in rows]

    await update_proxy_urls(urls=searched_urls, values={"searched": True})

    proxy_urls = await asyncio.gather(*map(_make_request, proxy_urls))

    urls = [x.split("//")[1] for x in proxy_urls if x]

    rows = await update_proxy_urls(urls=urls, values={"validated": True})

    return rows


if __name__ == "__main__":
    asyncio.run(check_proxy_urls())
