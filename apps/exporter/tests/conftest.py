import datetime as dt
import uuid

import pytest
from bancobot.models import Conversation, Message, MessageType
from classifier.models import Touchpoint
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database for exporter tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Ensure models are imported/registered in the global SQLModel metadata.
    _ = (Conversation, Message, Touchpoint)
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session for each test."""
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def fixed_dt():
    """A deterministic base datetime for tests."""
    return dt.datetime(2025, 1, 1, 12, 0, 0)


@pytest.fixture
def make_message(fixed_dt):
    """Factory for messages with simulated timestamps."""

    def _make(
        *,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        content: str,
        msg_type: MessageType,
        seconds_offset: int,
        parent_message_id: uuid.UUID | None = None,
    ) -> Message:
        ts = (fixed_dt + dt.timedelta(seconds=seconds_offset)).timestamp()
        return Message(
            id=message_id,
            conversation_id=conversation_id,
            content=content,
            type=msg_type,
            timing_metadata={
                "simulated_timestamp": ts,
                "pause_time": 0,
                "typing_time": 0,
                "thinking_time": 0,
            },
            created_at=fixed_dt + dt.timedelta(seconds=seconds_offset),
            parent_message_id=parent_message_id,
        )

    return _make
