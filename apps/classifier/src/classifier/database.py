from typing import Any, Generator

from sqlmodel import Session, SQLModel, create_engine


def create_db_and_tables(db: str):
    from classifier.models import Touchpoint  # noqa: F401

    """Initialize SQLModel with database and tables"""
    engine = create_engine(db)
    SQLModel.metadata.create_all(engine)
    return engine


def get_session(engine) -> Generator[Session, Any, Any]:
    with Session(engine) as session:
        yield session
