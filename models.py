from datetime import UTC, datetime

from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy_mixins import AllFeaturesMixin
from sqlmodel import Field, SQLModel, create_engine, select

from backend import logger
from backend.proxies.consts import sqlite_address
from backend.utils import chunked


class CustomAllFeaturesMixin(AllFeaturesMixin):
    __abstract__ = True
    __repr__ = AllFeaturesMixin.__repr__

    @classmethod
    def bulk_create(cls, objs: list["ProxyUrl"], batch_size: int = 100):
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


class ProxyUrl(CustomAllFeaturesMixin, SQLModel, table=True):
    __tablename__ = "proxy_url"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="proxy_url_pkey"),
        # {"schema": "ranked_jobs"},
    )

    id: int | None = Field(default=None, primary_key=True)
    url: str
    searched: bool = Field(default=False)
    date_searched: datetime | None
    validated: bool = Field(default=False)
    date_created: datetime = Field(default=datetime.now(UTC))
    last_validated: datetime | None


if __name__ == "__main__":
    engine = create_engine(sqlite_address)
    ProxyUrl.__table__.create(engine)
