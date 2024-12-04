from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy_mixins import AllFeaturesMixin
from sqlmodel import Field, SQLModel, select

from backend.logging import logger
from backend.utils import chunked


class CustomAllFeaturesMixin(AllFeaturesMixin):
    __abstract__ = True
    __repr__ = AllFeaturesMixin.__repr__

    @classmethod
    def bulk_create(cls, objs: list[Any], batch_size: int = 100):
        for chunk in chunked(objs, batch_size):
            stmnt = insert(cls).values([url.dict() for url in chunk])

            stmnt = stmnt.on_conflict_do_update(
                index_elements=[cls.id],
                set_={
                    k: getattr(stmnt.excluded, k)
                    for k in chunk[0].dict().keys()
                },
            ).returning(cls)
            orm_stmnt = (
                select(cls)
                .from_statement(stmnt)
                .execution_options(populate_existing=True)
            )

            cls.session.execute(orm_stmnt).scalars()

            try:
                cls.session.commit()
            except Exception as e:
                cls.session.rollback()
                logger.error(type(e), e.args, e)

        return cls


proxy_type_enums = StrEnum(
    "ProxyTypeEnums", {x.upper(): x for x in ("http", "https", "socks5")}
)

anon_enums = StrEnum(
    "AnonymityEnums", {x.upper(): x for x in ("anm", "hia", "noa")}
)


class ProxyUrl(CustomAllFeaturesMixin, SQLModel, table=True):
    __tablename__ = "proxy_url"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="proxy_url_pkey"),
        UniqueConstraint("url", "proxy_type"),
        # {"schema": "ranked_jobs"},
    )

    id: int | None = Field(default=None, primary_key=True)
    url: str
    proxy_type: proxy_type_enums
    anonymity: anon_enums
    country_code: str
    searched: bool = Field(default=False)
    date_searched: datetime | None
    validated: bool = Field(default=False)
    date_created: datetime = Field(default=datetime.now(UTC))
    last_validated: datetime | None


class ProxyList(SQLModel):
    proxy_ip_port: str = Field(..., alias="Proxy IP:port")
    proxy_type: proxy_type_enums = Field(..., alias="Type")
    anonymity: anon_enums = Field(..., alias="Anonymity*")
    country_city_region: str = Field(..., alias="Country (city/region)")
    hostname_org: str = Field(..., alias="Hostname/ORG")
    latency: float = Field(..., alias="Latency**")
    speed: Literal[""] = Field(..., alias="Speed***")
    uptime: Literal[""] = Field(..., alias="Uptime")
    checkdate_gmt03: str = Field(..., alias="Check date (GMT+03)")

    def get_proxy_url_instance(self):
        """
        Utility function to convert ProxyList instance into ProxyUrl instance.

        Returns:
            ProxyUrl
        """
        data = self.model_dump(
            include={
                "proxy_ip_port",
                "proxy_type",
                "anonymity",
                "country_city_region",
            }
        )

        data["url"] = data.pop("proxy_ip_port")
        if "sock" in data.get("proxy_type").lower():
            data["proxy_type"] = "socks5"
        elif "http\ns" in data.get("proxy_type").lower():
            data["proxy_type"] = "https"
        else:
            data["proxy_type"] = "http"

        data["anonymity"] = data.pop("anonymity").lower()
        data["country_code"] = data.pop("country_city_region").split("\n")[0]

        instance = ProxyUrl(**data)

        return instance
