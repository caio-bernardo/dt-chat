import pytest
import uuid
from unittest.mock import Mock, AsyncMock
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from bancobot.models import Message, MessageType, MessageCreate
from bancobot.services import BancoBotService
from bancobot.agent import BancoAgent
from bancobot.routes import router


@pytest.fixture(scope="function")
def in_memory_engine():
    """Create an in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(in_memory_engine):
    """Create a database session for testing"""
    with Session(in_memory_engine) as session:
        yield session


@pytest.fixture
def mock_agent():
    """Create a mock BancoAgent for testing"""
    agent = Mock(spec=BancoAgent)

    # Mock the process_message method to return a predictable AI response
    agent.process_message = Mock(return_value=Mock(content="Mock AI response"))

    def mock_process_message_side_effect(thread_id: uuid.UUID, message: HumanMessage) -> AIMessage:
        return AIMessage(content=f"Mock AI response to: {message.content}")

    agent.process_message.side_effect = mock_process_message_side_effect
    return agent


@pytest.fixture
def banco_service(mock_agent, db_session):
    """Create a BancoBotService instance with mocked dependencies"""
    return BancoBotService(agent=mock_agent, storage=db_session)


@pytest.fixture
def sample_session_id():
    """Generate a sample UUID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_message_create(sample_session_id):
    """Create a sample MessageCreate object"""
    return MessageCreate(
        session_id=sample_session_id, content="Hello, I need help with my account"
    )


@pytest.fixture
def sample_messages(db_session, sample_session_id):
    """Create sample messages in the database"""
    messages = [
        Message(
            session_id=sample_session_id,
            content="Hello, I need help",
            type=MessageType.Human,
        ),
        Message(
            session_id=sample_session_id,
            content="How can I help you today?",
            type=MessageType.AI,
        ),
        Message(
            session_id=sample_session_id,
            content="I want to check my balance",
            type=MessageType.Human,
        ),
    ]

    for message in messages:
        db_session.add(message)

    db_session.commit()

    for message in messages:
        db_session.refresh(message)

    return messages


@pytest.fixture
def mock_service_dependency():
    """Mock the service dependency for route testing"""
    mock_service = Mock(spec=BancoBotService)

    # Setup async mock methods
    mock_service.create_message = AsyncMock()
    mock_service.get_message_by_session = AsyncMock()
    mock_service.get_all_sessions = AsyncMock()
    mock_service.delete_messages_by_session = AsyncMock()
    mock_service.get_message_by_id = AsyncMock()
    mock_service.delete_message_by_id = AsyncMock()
    mock_service.get_recent_messages = AsyncMock()

    return mock_service


@pytest.fixture
def test_client(mock_service_dependency):
    """Create a test client for FastAPI routes with dependency overrides"""
    from fastapi import FastAPI
    from bancobot.routes import router
    from bancobot.dependecies import get_bbchat_service

    app = FastAPI()
    app.include_router(router)

    def get_mock_service():
        return mock_service_dependency

    app.dependency_overrides[get_bbchat_service] = get_mock_service

    return TestClient(app)


@pytest.fixture
def override_service_dependency(test_client, mock_service_dependency):
    """Provide the mock service dependency for test configuration"""
    yield mock_service_dependency
