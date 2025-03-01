"""
Utilities for scanning and processing spys proxies
"""

from playwright.async_api import async_playwright


async def get_proxy_request(url: str) -> str | None:
    """
    Utility function to call the proxy resource URL and get the response
    object from `htmx_html`.
    Args:
        url: str

    Returns: httpx.Response

    """
    playwright = await async_playwright().start()
    async with await playwright.chromium.launch(headless=False) as browser:
        async with await browser.new_context() as ctx:
            async with await ctx.new_page() as page:
                try:
                    await page.goto(url=url, wait_until="networkidle")
                    await page.wait_for_timeout(600)
                    country = page.locator("select#tldc")
                    await country.select_option("1")
                    await page.wait_for_timeout(600)
                    show_count = page.locator("select#xpp")
                    await show_count.select_option("5")
                    await page.wait_for_timeout(6000)

                    content = await page.content()
                except Exception as e:
                    print(
                        f"Getting page contents failed for {url}. "
                        f"See error messages: {type(e), e, e.args}"
                    )
                    return None
    return content


async def get_data_from_rows(rows):
    """

    Args:
        rows:

    Returns:

    """
    header = None
    data = []
    for i, row in enumerate(rows[1:]):
        data_row = [td.text for td in row.find_all("td")]
        if i == 0:
            header = data_row
        else:
            # raw_ip = data_row[0].split("document")[0].split(".")
            # data_row[0] = f"{'.'.join(raw_ip[:-1])}:{raw_ip[-1]}"
            data.append(data_row)

    return header, data
