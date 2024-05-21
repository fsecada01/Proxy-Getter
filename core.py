import asyncio
from datetime import UTC, datetime
from pprint import pformat

from sqlalchemy import create_engine
from sqlmodel import Session

from backend.logging import logger
from backend.proxies.consts import sqlite_address
from backend.proxies.models import ProxyUrl
from backend.proxies.utils import test_proxy_url
from backend.utils import chunked


async def check_url(url_model: ProxyUrl):
    logger.info(f"Checking URL {url_model.url} now.")
    date_now = datetime.now(UTC)
    validated_url = await test_proxy_url(url_model.url)
    kwargs = {
        "searched": True,
        "date_searched": date_now,
        "commit": False,
        "id": url_model.id,
        "url": url_model.url,
    }
    if url_model.url == validated_url:
        kwargs.update({"validated": True, "last_validated": date_now})

    url_model.update(**kwargs)
    return url_model


async def proxy_job(proxy_list: list[ProxyUrl], chunk_size: int = 250):
    return_models = []

    for i, chunk in enumerate(chunked(proxy_list, 250)):
        logger.info(f"Starting Chunk {i} with {len(chunk)} results.")

        tasks = [asyncio.ensure_future(check_url(url)) for url in chunk]

        results = await asyncio.gather(*tasks)

        model_insts = [x for x in results if x is not None]

        if model_insts:
            ProxyUrl.bulk_create(
                objs=model_insts, batch_size=chunk_size
            )  # noqa

            return_models.extend(model_insts)

    return return_models


if __name__ == "__main__":
    import sys

    ProxyUrl.set_session(Session(create_engine(sqlite_address)))

    urls_to_test = ProxyUrl.query.filter(
        ProxyUrl.validated == False, ProxyUrl.searched == False  # noqa E712
    ).all()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    results = asyncio.run(proxy_job(proxy_list=urls_to_test))

    print(pformat(results))
