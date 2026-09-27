"""
A proxy caller for ProxyScrape's free proxy list API.

The API returns JSON with protocol, anonymity and geolocation per proxy, so
no browser is needed. spys.one, the previous source, sits behind
Cloudflare, which challenges headless browsers and its list filter form.
"""

import asyncio

import httpx

from proxy_getter.models import ProxyUrl, anon_enums, proxy_type_enums
from proxy_getter.store import save_proxy_urls

try:
    from backend.logging import logger
except ImportError:
    from loguru import logger

API_URL = "https://api.proxyscrape.com/v4/free-proxy-list/get"
# ProxyUrl only models http/https/socks5, and consumers filter out
# transparent ("noa") proxies, so ask the API for just what is usable.
PROTOCOLS = ("http", "socks5")
ANONYMITY = {"elite": "hia", "anonymous": "anm", "transparent": "noa"}
MAX_PAGES = 5


async def fetch_proxies(
    client: httpx.AsyncClient, countries: list[str] | None = None
) -> list[dict]:
    """
    Page through the ProxyScrape API.

    Args:
        client: httpx.AsyncClient
        countries: optional ISO 3166-1 alpha-2 codes, e.g. ["US", "CA"]

    Returns:
        list[dict]: raw proxy records
    """
    params = {
        "request": "display_proxies",
        "proxy_format": "protocolipport",
        "format": "json",
        "protocol": ",".join(PROTOCOLS),
        "anonymity": "elite,anonymous",
    }
    if countries:
        params["country"] = ",".join(c.lower() for c in countries)

    records = []
    for _ in range(MAX_PAGES):
        r = await client.get(API_URL, params={**params, "skip": len(records)})
        r.raise_for_status()
        body = r.json()
        records.extend(body.get("proxies") or [])
        if not body.get("nextpage"):
            break

    return records


def to_proxy_url(record: dict) -> ProxyUrl | None:
    """
    Convert one API record into a `ProxyUrl`, or None if it is unusable.

    Args:
        record: dict

    Returns:
        ProxyUrl | None
    """
    protocol = record.get("protocol")
    anonymity = ANONYMITY.get(record.get("anonymity"))
    if protocol not in PROTOCOLS or not anonymity or not record.get("alive"):
        return None

    return ProxyUrl(
        url=f"{record['ip']}:{record['port']}",
        proxy_type=proxy_type_enums(protocol),
        anonymity=anon_enums(anonymity),
        country_code=(record.get("ip_data") or {}).get("countryCode") or "",
    )


@logger.catch
async def main(countries: list[str] | None = None) -> int:
    """
    Fetch the current list and save proxies not already stored. Run
    `proxy_getter.core.check_proxy_urls` afterwards to validate them.

    Args:
        countries: optional ISO 3166-1 alpha-2 codes, e.g. ["US", "CA"]

    Returns:
        int: the number of new rows written
    """
    async with httpx.AsyncClient(timeout=60) as client:
        records = await fetch_proxies(client, countries=countries)

    instances = [inst for r in records if (inst := to_proxy_url(r))]
    written = save_proxy_urls(instances)
    logger.info(
        f"Done! {len(records)} records, {len(instances)} usable, "
        f"{written} new."
    )

    return written


if __name__ == "__main__":
    asyncio.run(main())
