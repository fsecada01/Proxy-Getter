from consts import sqlite_address
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

engine = create_engine(sqlite_address)

session_maker = sessionmaker(
    bind=engine, class_=Session, expire_on_commit=False
)
