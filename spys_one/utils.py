"""
Utilities for scanning and processing spys proxies
"""

from httpx_html import AsyncHTMLSession, HTMLResponse


async def get_proxy_request(url: str) -> HTMLResponse | None:
    """
    Utility function to call the proxy resource URL and get the response
    object from `htmx_html`.
    Args:
        url: str

    Returns: httpx.Response

    """
    session = AsyncHTMLSession()
    data = {"xpp": 5}  # fifth parameter that controls page size
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
        if row:
            data_row = [td.text for td in row.find("td")]
            if i == 0:
                header = data_row
            else:
                data_row[0] = data_row[0].split("document")[0]
                data.append(data_row)

    return header, data
