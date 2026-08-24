import os

from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)


# ==================================================
# LOAD ENV
# ==================================================

load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise RuntimeError(
        "DATABASE_URL is not configured. "
        "Create a .env file in project root."
    )


# ==================================================
# SQLALCHEMY ENGINE
# ==================================================

engine = create_engine(

    DATABASE_URL,

    pool_pre_ping=True,

    future=True,
)


# ==================================================
# SESSION
# ==================================================

SessionLocal = sessionmaker(

    bind=engine,

    autoflush=False,

    autocommit=False,

    expire_on_commit=False,
)


# ==================================================
# BASE MODEL
# ==================================================

Base = declarative_base()


# ==================================================
# FASTAPI DB DEPENDENCY
# ==================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()