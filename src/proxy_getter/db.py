from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from proxy_getter.consts import DB_PATH, sqlite_address

# SQLite creates the file but not its directory.
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(sqlite_address)

session_maker = sessionmaker(
    bind=engine, class_=Session, expire_on_commit=False
)
