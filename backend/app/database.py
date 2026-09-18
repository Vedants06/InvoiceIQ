"""SQLAlchemy database setup.

Works with SQLite (default, zero-setup local dev) and PostgreSQL
(via DATABASE_URL). Models use portable column types (e.g. JSON) so the
same code runs on both.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)
engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=not settings.database_url.startswith("sqlite"),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables. Imported models register themselves on Base.metadata."""
    from app import models  # noqa: F401  (ensure models are imported)

    Base.metadata.create_all(bind=engine)
