"""A proxy caller for Spys proxy service"""

import asyncio

from httpx_html import AsyncHTMLSession

from backend.proxies.models import ProxyList
from backend.utils import set_event_loop, windows_sys_event_loop_check


async def get_proxy_request(url):
    """
    Utility function to call the proxy resource URL and get the response
    object from `htmx_html`.
    Args:
        url: str

    Returns: httpx.Response

    """
    session = AsyncHTMLSession()
    data = {"xpp": 5}  # fifth parameter that controls page size
    r = session.post(url, data=data)

    return r if r.status_code == 200 else None


async def get_data_from_rows(rows):
    """

    Args:
        rows:

    Returns:

    """
    header = None
    data = []
    for i, row in enumerate(rows[1:]):
        data_row = [td.text for td in row.find("td")]
        if i == 0:
            header = data_row
        else:
            data_row[0] = data_row[0].split("document")[0]
            data.append(data_row)

    return header, data


async def main():
    url = "https://spys.one/free-proxy-list/US/"
    resp = await get_proxy_request(url=url)

    rows = resp.html.find("tr[class*='spy1x']")

    header, data = await get_data_from_rows(rows=rows)

    payload = list(map(lambda row: dict(zip(header, row)), data))

    proxy_list = [ProxyList(**row) for row in payload]

    instances = list(
        map(lambda inst: inst.get_proxy_url_instance(), proxy_list)
    )

    written_rows = ProxyList.bulk_create(objs=instances)

    return written_rows


if __name__ == "__main__":
    windows_sys_event_loop_check()
    set_event_loop()

    asyncio.run(main())
