from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import Connection, create_engine

from app.config import DATABASE_URL

# Supabase session pooler; small pool for Render Free (512 MB, single instance).
engine = create_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1),
    pool_size=3,
    max_overflow=2,
    pool_pre_ping=True,
) if DATABASE_URL else None


def get_conn() -> Iterator[Connection]:
    with engine.begin() as conn:
        yield conn


ConnDep = Annotated[Connection, Depends(get_conn)]
