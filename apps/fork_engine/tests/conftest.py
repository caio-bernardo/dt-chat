import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from bancobot.agent import BancoAgent, BancoAgentBuilder
from classifier.models import Touchpoint
from langchain_core.messages import AIMessage
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from userbot import TimeSimulationConfig, UserBotBuilder

from fork_engine.engine import ForkConfig, ForkEngine


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
def mock_queue():
    """Create a mock ISubscriber queue."""
    queue = MagicMock()
    queue.subscribe = AsyncMock()
    return queue


@pytest.fixture
def mock_queue_prod():
    """Create a mock IPublisher queue producer."""
    producer = MagicMock()
    producer.publish = AsyncMock()
    return producer


@pytest.fixture
def mock_bancobot_agent():
    """Create a mock BancoAgent."""
    agent = MagicMock(spec=BancoAgent)
    agent.process_message = MagicMock(return_value=AIMessage(content="Mock response"))
    return agent


@pytest.fixture
def mock_bancobot_builder():
    """Create a mock BancoAgentBuilder."""
    builder = MagicMock(spec=BancoAgentBuilder)
    builder.build_with_default = MagicMock()
    return builder


@pytest.fixture
def mock_userbot_builder():
    """Create a mock UserBotBuilder."""
    builder = MagicMock(spec=UserBotBuilder)
    builder.build_with_default = MagicMock()
    return builder


@pytest.fixture
def fork_engine(mock_queue, mock_queue_prod):
    """Create a ForkEngine instance for testing."""
    return ForkEngine(mock_queue, mock_queue_prod, db_url="sqlite:///:memory:")


@pytest.fixture
def fork_config(mock_bancobot_builder, mock_userbot_builder):
    """Create a sample ForkConfig."""
    return ForkConfig(
        parent_conversation=uuid.uuid4(),
        bancobot_builder=mock_bancobot_builder,
        userbot_builder=mock_userbot_builder,
        next_msg="Test message",
        timesim=TimeSimulationConfig(),
        iterations=5,
    )


@pytest.fixture
def touchpoint():
    """Create a sample Touchpoint."""
    return Touchpoint(  # pyright: ignore[reportCallIssue]
        id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        activity="SOLICITAÇÃO DIRETA DE HUMANO",
        timestamp=datetime.now().isoformat(),
        metadata={},  # pyright: ignore[reportCallIssue]
    )
