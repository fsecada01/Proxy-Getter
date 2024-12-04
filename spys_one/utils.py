"""
Utilities for scanning and processing spys proxies
"""

from httpx_html import AsyncHTMLSession, HTMLResponse


async def get_proxy_request(
    url: str, data: dict | None = None
) -> HTMLResponse | None:
    """
    Utility function to call the proxy resource URL and get the response
    object from `htmx_html`.
    Args:
        data: dict | None = None
        url: str

    Returns: httpx.Response

    """
    session = AsyncHTMLSession()
    r = await session.post(url, data=data)  # noqa

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
            raw_ip = data_row[0].split("document")[0].split(".")
            data_row[0] = f"{'.'.join(raw_ip[:-1])}:{raw_ip[-1]}"
            data.append(data_row)

    return header, data
