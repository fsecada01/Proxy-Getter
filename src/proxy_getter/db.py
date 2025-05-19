from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from proxy_getter.consts import sqlite_address

engine = create_engine(sqlite_address)

session_maker = sessionmaker(
    bind=engine, class_=Session, expire_on_commit=False
)
