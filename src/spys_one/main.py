"""A proxy caller for Spys proxy service"""

import asyncio
from pprint import pformat

from sqlmodel import select

from db import session_maker
from models import ProxyList, ProxyUrl

try:
    from backend.logging import logger
except ImportError:
    from loguru import logger

from utils import get_data_from_rows, get_proxy_request

from .consts import url_field


async def get_existing_urls():
    """
    Quick utility function to get existing URLs from the SQLite database.
    Returns:

    """
    with session_maker() as session:
        results = session.exec(select(ProxyUrl.url))
        rows = results.all()

    return set(rows) if rows else set()


@logger.catch
async def main():
    """
    The man function that will run a series of commands to call the
    prescribed URL, process the HTML rows and embedded columns, convert them
    into JSON, validate via Pydantic, and save `ProxyUrl` instances.
    Returns:
        list[ProxyList]

    """
    url = "https://spys.one/north-america-proxy/"
    data = {
        "xx00": "cbc05e084c6f04e0f75750f9b5a4b83a",
        "xpp": 5,
        "tldc": 1,
        "xf1": 0,
        "xf2": 0,
        "xf5": 0,
    }  # fifth parameter that controls page size
    resp = await get_proxy_request(url=url, data=data)

    rows = resp.html.find("tr[class*='spy1x']")

    logger.debug(len(rows))

    header, data = await get_data_from_rows(rows=rows)

    payload = list(map(lambda row: dict(zip(header, row)), data))

    data = []
    exist_urls = await get_existing_urls()
    for row in payload:
        if row.get(url_field) not in exist_urls:
            data.append(row)
            exist_urls.add(row.get(url_field))

    proxy_list = [ProxyList.model_construct(**row) for row in data]

    instances = list(
        map(lambda inst: inst.get_proxy_url_instance(), proxy_list)
    )

    with session_maker() as session:
        ProxyUrl.set_session(session)
        try:
            ProxyUrl.bulk_create(objs=instances)
        except Exception as e:
            logger.debug(f"Bulk create failed. See here: {type(e), e, e.args}")
            logger.info(
                "Going to write rows individually. This will be "
                "slower but more effective."
            )
            failed_insts = []
            for inst in instances:
                try:
                    ProxyUrl.create(inst)
                except Exception as e:
                    logger.error(
                        f"Failed to write entry. See here: "
                        f"{type(e), e, e.args}"
                    )
                    failed_insts.append(inst)

            logger.debug(
                pformat(
                    f"These are the failed instances. Please review: "
                    f"{failed_insts}"
                )
            )

    logger.info(f"Done! Processed {len(instances)} rows.")


if __name__ == "__main__":

    asyncio.run(main())
