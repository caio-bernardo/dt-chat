import datetime as dt
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from bancobot.models import Conversation, Message, MessageType
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from classifier.agent import ClassifierAgent
from classifier.models import Touchpoint
from classifier.services import ClassifierService


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
    """Create a mock ClassifierAgent."""
    agent = MagicMock(spec=ClassifierAgent)
    agent.classify = AsyncMock(return_value="SALDO_CONSULTA")
    return agent


@pytest.fixture
def sample_message():
    """Create a sample Message from bancobot."""
    conversation_id = uuid.uuid4()
    return Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        content="Qual é o meu saldo?",
        type=MessageType.Human,
        timing_metadata={
            "simulated_timestamp": dt.datetime.now().timestamp(),
            "pause_time": 0,
            "typing_time": 0,
            "thinking_time": 0,
        },
        created_at=dt.datetime.now(),
    )


@pytest.fixture
def sample_touchpoint(sample_message):
    """Create a sample Touchpoint."""
    return Touchpoint(
        message_id=sample_message.id,
        message=sample_message,
        activity="SALDO_CONSULTA",
        created_at=dt.datetime.now(),
    )


@pytest.fixture
def classifier_service(mock_agent, db_session):
    """Create a ClassifierService instance for testing."""
    return ClassifierService(agent=mock_agent, storage=db_session)


@pytest.fixture
def touchpoint_list():
    """Create a list of available touchpoints."""
    return [
        "SALDO_CONSULTA",
        "EXTRATO_SOLICITACAO",
        "TRANSFERENCIA",
        "PAGAMENTO_BOLETO",
        "CARTAO_CREDITO",
    ]


@pytest.fixture
def sample_conversation():
    """Create a sample Conversation from bancobot."""
    return Conversation(
        id=uuid.uuid4(),
        meta={},
        created_at=dt.datetime.now(),
    )
