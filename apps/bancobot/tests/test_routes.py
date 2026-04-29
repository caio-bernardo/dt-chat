import datetime as dt
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from timesim import TimingMetadata

from bancobot.models import (
    Conversation,
    ConversationPublic,
    MessageType,
)
from bancobot.routes import router
from bancobot.services import BancoBotService


def create_test_timing_metadata() -> TimingMetadata:
    """Helper to create valid timing metadata."""
    return {
        "simulated_timestamp": dt.datetime.now().timestamp(),
        "pause_time": 0,
        "typing_time": 0,
        "thinking_time": 0,
    }


def create_message_response(
    conversation: Conversation, msg_id: int, content: str, msg_type: MessageType
):
    """Helper to create a MessagePublicComplete for API responses."""
    from bancobot.models import MessagePublicComplete

    conv_public = ConversationPublic(
        id=conversation.id,
        meta=conversation.meta,
        created_at=conversation.created_at,
    )
    return MessagePublicComplete(
        id=msg_id,
        conversation_id=conversation.id,
        conversation=conv_public,
        content=content,
        type=msg_type,
        timing_metadata=create_test_timing_metadata(),
        parent_message_id=None,
        parent=None,
        created_at=dt.datetime.now(),
    )


@pytest.fixture
def app():
    """Create a FastAPI app with the router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_returns_info(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "BancoBotAPI" in response.json()["detail"]


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_ok(self, client):
        """Test health endpoint returns OK status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["detail"] == "API is on air."


class TestCreateSessionEndpoint:
    """Test session creation endpoint."""

    def test_create_session_success(self, app, conversation):
        """Test creating a new session."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.create_session = AsyncMock(return_value=conversation)

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.post("/sessions", json={"meta": {"test": "data"}})

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["meta"] == conversation.meta

    def test_create_session_empty_meta(self, app, conversation):
        """Test creating a session with empty metadata."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.create_session = AsyncMock(return_value=conversation)

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.post("/sessions", json={})
        assert response.status_code == 201


class TestGetSessionsEndpoint:
    """Test get all sessions endpoint."""

    def test_get_sessions_empty(self, app):
        """Test retrieving sessions when none exist."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.get_all_sessions = AsyncMock(return_value=[])

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.get("/sessions")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_sessions_multiple(self, app, conversation):
        """Test retrieving multiple sessions."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.get_all_sessions = AsyncMock(
            return_value=[conversation, conversation]
        )

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.get("/sessions")
        assert response.status_code == 200
        sessions = response.json()
        assert len(sessions) == 2


class TestFetchSessionEndpoint:
    """Test fetch session endpoint."""

    def test_fetch_session_success(self, app, conversation):
        """Test fetching a specific session."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.fetch_session = AsyncMock(return_value=conversation)

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.get(f"/sessions/{conversation.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(conversation.id)

    def test_fetch_session_not_found(self, app):
        """Test fetching a non-existent session."""
        from fastapi import HTTPException

        mock_service = MagicMock(spec=BancoBotService)
        mock_service.fetch_session = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Session not found")
        )

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        fake_id = uuid.uuid4()
        response = client.get(f"/sessions/{fake_id}")
        assert response.status_code == 404


class TestDeleteSessionEndpoint:
    """Test delete session endpoint."""

    def test_delete_session_success(self, app, conversation):
        """Test deleting a session."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.delete_session = AsyncMock(return_value=None)

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.delete(f"/sessions/{conversation.id}")
        assert response.status_code == 204

    def test_delete_session_not_found(self, app):
        """Test deleting a non-existent session."""
        from fastapi import HTTPException

        mock_service = MagicMock(spec=BancoBotService)
        mock_service.delete_session = AsyncMock(
            side_effect=HTTPException(status_code=404, detail="Session not found")
        )

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        fake_id = uuid.uuid4()
        response = client.delete(f"/sessions/{fake_id}")
        assert response.status_code == 404


class TestCreateMessageEndpoint:
    """Test message creation endpoint."""

    def test_create_message_success(self, app, conversation):
        """Test creating a new message."""
        msg_response = create_message_response(
            conversation, 1, "Test response", MessageType.AI
        )

        mock_service = MagicMock(spec=BancoBotService)
        mock_service.save_publish_answer_message = AsyncMock(return_value=msg_response)

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.post(
            "/messages",
            json={
                "conversation_id": str(conversation.id),
                "content": "Hello",
                "type": "human",
                "timing_metadata": create_test_timing_metadata(),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test response"
        assert data["type"] == "ai"

    def test_create_message_error(self, app, conversation):
        """Test creating a message with an error."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.save_publish_answer_message = AsyncMock(
            side_effect=Exception("Processing error")
        )

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.post(
            "/messages",
            json={
                "conversation_id": str(conversation.id),
                "content": "Hello",
            },
        )

        assert response.status_code == 500


class TestFetchMessagesEndpoint:
    """Test fetch messages endpoint."""

    def test_fetch_messages_empty(self, app, conversation):
        """Test fetching messages when none exist."""
        mock_service = MagicMock(spec=BancoBotService)
        mock_service.get_messages_by_conversation = AsyncMock(return_value=[])

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.get(f"/sessions/{conversation.id}/messages")
        assert response.status_code == 200
        assert response.json() == []

    def test_fetch_messages_multiple(self, app, conversation):
        """Test fetching multiple messages."""
        messages = [
            create_message_response(conversation, 1, "Message 1", MessageType.Human),
            create_message_response(conversation, 2, "Message 2", MessageType.AI),
        ]

        mock_service = MagicMock(spec=BancoBotService)
        mock_service.get_messages_by_conversation = AsyncMock(return_value=messages)

        from bancobot.dependecies import get_bbchat_service

        app.dependency_overrides[get_bbchat_service] = lambda: mock_service
        client = TestClient(app)

        response = client.get(f"/sessions/{conversation.id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] == "Message 1"
        assert data[1]["content"] == "Message 2"
