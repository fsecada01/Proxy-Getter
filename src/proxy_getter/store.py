"""Persistence helpers shared by the proxy sources."""

from pprint import pformat

from sqlmodel import select

from proxy_getter.db import session_maker
from proxy_getter.models import ProxyUrl

try:
    from backend.logging import logger
except ImportError:
    from loguru import logger


def get_existing_urls() -> set[str]:
    """
    Get the proxy addresses (`ip:port`) already in the SQLite database.

    Returns:
        set[str]
    """
    with session_maker() as session:
        rows = session.exec(select(ProxyUrl.url)).all()

    return set(rows)


def save_proxy_urls(instances: list[ProxyUrl]) -> int:
    """
    Write new `ProxyUrl` rows, skipping addresses that are already stored.
    Falls back to row-by-row inserts if the bulk insert fails.

    Args:
        instances: list[ProxyUrl]

    Returns:
        int: the number of rows offered for insert after de-duplication
    """
    existing = get_existing_urls()
    new = []
    for inst in instances:
        if inst.url not in existing:
            existing.add(inst.url)
            new.append(inst)

    if not new:
        return 0

    with session_maker() as session:
        ProxyUrl.set_session(session)
        try:
            ProxyUrl.bulk_create(objs=new)
        except Exception as e:
            logger.debug(f"Bulk create failed. See here: {type(e), e, e.args}")
            logger.info(
                "Going to write rows individually. This will be "
                "slower but more effective."
            )
            failed_insts = []
            session.rollback()
            for inst in new:
                try:
                    session.add(inst)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error(
                        f"Failed to write entry. See here: {type(e), e, e.args}"
                    )
                    failed_insts.append(inst)

            if failed_insts:
                logger.debug(
                    pformat(
                        f"These are the failed instances. Please review: "
                        f"{failed_insts}"
                    )
                )

    return len(new)
