import datetime as dt
from unittest.mock import AsyncMock, MagicMock

import pytest
from chatbot import HumanMessage
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from bancobot.agent import BancoAgent
from bancobot.models import (
    Conversation,
    ConversationCreate,
    MessageCreate,
    MessageType,
)
from bancobot.services import BancoBotService


@pytest.fixture
def db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session for each test."""
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def mock_agent():
    """Create a mock BancoAgent."""
    agent = MagicMock(spec=BancoAgent)
    agent.process_message = MagicMock(
        return_value=HumanMessage(content="Mock response")
    )
    return agent


@pytest.fixture
def mock_publisher():
    """Create a mock message publisher."""
    publisher = MagicMock()
    publisher.publish = AsyncMock()
    return publisher


@pytest.fixture
def conversation_create_data():
    """Sample ConversationCreate data."""
    return ConversationCreate(meta={"persona": "test_user"})


@pytest.fixture
def conversation(db_session, conversation_create_data):
    """Create a sample conversation in the database."""
    conversation = Conversation.model_validate(conversation_create_data)
    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)
    return conversation


@pytest.fixture
def message_create_data(conversation, timing_metadata):
    """Sample MessageCreate data."""
    return MessageCreate(
        conversation_id=conversation.id,
        content="Hello, how can I help?",
        type=MessageType.Human,
        timing_metadata=timing_metadata,
    )


@pytest.fixture
def bancobot_service(mock_agent, db_session, mock_publisher):
    """Create a BancoBotService instance for testing."""
    return BancoBotService(
        agent=mock_agent, storage=db_session, producer_service=mock_publisher
    )


@pytest.fixture
def timing_metadata():
    """Sample timing metadata."""
    return {
        "simulated_timestamp": dt.datetime.now().timestamp(),
        "pause_time": 0,
        "typing_time": 0,
        "thinking_time": 0,
    }
