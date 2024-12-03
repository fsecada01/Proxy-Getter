import random

import httpx
from httpx import HTTPTransport

from backend.proxies.consts import URLs


async def get_req_client(proxy_mounts: dict[str, HTTPTransport] | None = None):
    if proxy_mounts is None:
        proxy_mounts = {}
    async with httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
        mounts=proxy_mounts,
    ) as client:
        return client


async def test_proxy_url(url: str):
    """

    Args:
        url: str

    Returns:

    """
    proxy_url = f"http://{url}"
    proxy_mounts = {
        f"{x}://": httpx.HTTPTransport(proxy=proxy_url)
        for x in ("http", "https")
    }

    try:
        client = await get_req_client(proxy_mounts=proxy_mounts)
        req = client.get(random.choice(URLs))
        resp = await req
        if resp.status_code == 200:
            print("Passed proxy test!")
            return url
            # approved_proxy_addresses.append(url)
    except Exception:
        return None
