import pytest
import uuid
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from bancobot.routes import router
from bancobot.models import Message, MessageType, MessageCreate
from bancobot.services import BancoBotService


class TestRoutes:
    """Test cases for FastAPI route endpoints"""

    def test_root_endpoint(self, test_client):
        """Test the root endpoint returns correct message"""
        # Act
        response = test_client.get("/")

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "detail": "Root of BancoBotAPI. Check /docs endpoint for available endpoints."
        }

    def test_health_endpoint(self, test_client):
        """Test the health check endpoint"""
        # Act
        response = test_client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"detail": "API is on air."}

    def test_get_sessions_success(self, test_client, override_service_dependency):
        """Test getting all sessions successfully"""
        # Setup
        session_ids = [uuid.uuid4(), uuid.uuid4()]
        override_service_dependency.get_all_sessions.return_value = session_ids

        # Act
        response = test_client.get("/sessions")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        # Convert string UUIDs back to UUID objects for comparison
        assert uuid.UUID(response_data[0]) == session_ids[0]
        assert uuid.UUID(response_data[1]) == session_ids[1]
        override_service_dependency.get_all_sessions.assert_called_once()

    def test_get_sessions_empty(self, test_client, override_service_dependency):
        """Test getting sessions when none exist"""
        # Setup
        override_service_dependency.get_all_sessions.return_value = []

        # Act
        response = test_client.get("/sessions")

        # Assert
        assert response.status_code == 200
        assert response.json() == []
        override_service_dependency.get_all_sessions.assert_called_once()

    def test_get_sessions_service_error(self, test_client, override_service_dependency):
        """Test handling service errors when getting sessions"""
        # Setup
        override_service_dependency.get_all_sessions.side_effect = Exception(
            "Database error"
        )

        # Act
        response = test_client.get("/sessions")

        # Assert
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    def test_fetch_session_success(self, test_client, override_service_dependency):
        """Test fetching a specific session successfully"""
        # Setup
        session_id = uuid.uuid4()
        messages = [
            Message(
                id=1, session_id=session_id, content="Hello", type=MessageType.Human
            ),
            Message(
                id=2, session_id=session_id, content="Hi there!", type=MessageType.AI
            ),
        ]
        override_service_dependency.get_message_by_session.return_value = messages

        # Act
        response = test_client.get(f"/sessions/{session_id}")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert len(response_data) == 2
        assert response_data[0]["content"] == "Hello"
        assert response_data[0]["type"] == "Human"
        assert response_data[1]["content"] == "Hi there!"
        assert response_data[1]["type"] == "ai"
        override_service_dependency.get_message_by_session.assert_called_once_with(
            session_id
        )

    def test_fetch_session_empty(self, test_client, override_service_dependency):
        """Test fetching a session with no messages"""
        # Setup
        session_id = uuid.uuid4()
        override_service_dependency.get_message_by_session.return_value = []

        # Act
        response = test_client.get(f"/sessions/{session_id}")

        # Assert
        assert response.status_code == 200
        assert response.json() == []
        override_service_dependency.get_message_by_session.assert_called_once_with(
            session_id
        )

    def test_fetch_session_invalid_uuid(self, test_client):
        """Test fetching a session with invalid UUID format"""
        # Act
        response = test_client.get("/sessions/invalid-uuid")

        # Assert
        assert response.status_code == 422  # Validation error

    def test_fetch_session_service_error(
        self, test_client, override_service_dependency
    ):
        """Test handling service errors when fetching session"""
        # Setup
        session_id = uuid.uuid4()
        override_service_dependency.get_message_by_session.side_effect = Exception(
            "Session not found"
        )

        # Act
        response = test_client.get(f"/sessions/{session_id}")

        # Assert
        assert response.status_code == 500
        assert "Session not found" in response.json()["detail"]

    def test_delete_session_success(self, test_client, override_service_dependency):
        """Test deleting a session successfully"""
        # Setup
        session_id = uuid.uuid4()
        override_service_dependency.delete_messages_by_session.return_value = 3

        # Act
        response = test_client.delete(f"/sessions/{session_id}")

        # Assert
        assert response.status_code == 200
        # Note: The route returns a tuple (204, count), but the test client gets the response
        override_service_dependency.delete_messages_by_session.assert_called_once_with(
            session_id
        )

    def test_delete_session_not_found(self, test_client, override_service_dependency):
        """Test deleting a non-existent session"""
        # Setup
        session_id = uuid.uuid4()
        override_service_dependency.delete_messages_by_session.return_value = 0

        # Act
        response = test_client.delete(f"/sessions/{session_id}")

        # Assert
        assert response.status_code == 200
        override_service_dependency.delete_messages_by_session.assert_called_once_with(
            session_id
        )

    def test_delete_session_service_error(
        self, test_client, override_service_dependency
    ):
        """Test handling service errors when deleting session"""
        # Setup
        session_id = uuid.uuid4()
        override_service_dependency.delete_messages_by_session.side_effect = Exception(
            "Delete failed"
        )

        # Act
        response = test_client.delete(f"/sessions/{session_id}")

        # Assert
        assert response.status_code == 500
        assert "Delete failed" in response.json()["detail"]

    def test_create_message_success(self, test_client, override_service_dependency):
        """Test creating a new message successfully"""
        # Setup
        session_id = uuid.uuid4()
        message_data = {"session_id": str(session_id), "content": "Hello, I need help"}

        expected_response = Message(
            id=1,
            session_id=session_id,
            content="How can I help you today?",
            type=MessageType.AI,
        )
        override_service_dependency.create_message.return_value = expected_response

        # Act
        response = test_client.post("/messages", json=message_data)

        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["content"] == "How can I help you today?"
        assert response_data["type"] == "ai"
        assert response_data["id"] == 1

        # Verify the service was called with correct data
        override_service_dependency.create_message.assert_called_once()
        call_args = override_service_dependency.create_message.call_args[0][0]
        assert isinstance(call_args, MessageCreate)
        assert call_args.content == "Hello, I need help"
        assert call_args.session_id == session_id

    def test_create_message_without_session_id(
        self, test_client, override_service_dependency
    ):
        """Test creating a message without session_id"""
        # Setup
        message_data = {"content": "Hello without session"}

        generated_session_id = uuid.uuid4()
        expected_response = Message(
            id=1,
            session_id=generated_session_id,
            content="How can I help you?",
            type=MessageType.AI,
        )
        override_service_dependency.create_message.return_value = expected_response

        # Act
        response = test_client.post("/messages", json=message_data)

        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["content"] == "How can I help you?"
        assert response_data["type"] == "ai"

        # Verify the service was called
        override_service_dependency.create_message.assert_called_once()
        call_args = override_service_dependency.create_message.call_args[0][0]
        assert call_args.content == "Hello without session"
        assert call_args.session_id is None

    def test_create_message_missing_content(self, test_client):
        """Test creating a message without required content field"""
        # Setup
        message_data = {
            "session_id": str(uuid.uuid4())
            # Missing content field
        }

        # Act
        response = test_client.post("/messages", json=message_data)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_message_invalid_session_id(self, test_client):
        """Test creating a message with invalid session_id format"""
        # Setup
        message_data = {"session_id": "invalid-uuid", "content": "Hello"}

        # Act
        response = test_client.post("/messages", json=message_data)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_create_message_service_error(
        self, test_client, override_service_dependency
    ):
        """Test handling service errors when creating message"""
        # Setup
        message_data = {"content": "Test message"}
        override_service_dependency.create_message.side_effect = Exception(
            "AI service unavailable"
        )

        # Act
        response = test_client.post("/messages", json=message_data)

        # Assert
        assert response.status_code == 500
        assert "AI service unavailable" in response.json()["detail"]

    def test_create_message_empty_content(
        self, test_client, override_service_dependency
    ):
        """Test creating a message with empty content"""
        # Setup
        message_data = {"content": ""}

        expected_response = Message(
            id=1,
            session_id=uuid.uuid4(),
            content="I didn't understand that.",
            type=MessageType.AI,
        )
        override_service_dependency.create_message.return_value = expected_response

        # Act
        response = test_client.post("/messages", json=message_data)

        # Assert
        assert response.status_code == 201
        # The service should still process empty content
        override_service_dependency.create_message.assert_called_once()

    def test_create_message_very_long_content(
        self, test_client, override_service_dependency
    ):
        """Test creating a message with very long content"""
        # Setup
        long_content = "A" * 10000  # Very long message
        message_data = {"content": long_content}

        expected_response = Message(
            id=1,
            session_id=uuid.uuid4(),
            content="Message processed",
            type=MessageType.AI,
        )
        override_service_dependency.create_message.return_value = expected_response

        # Act
        response = test_client.post("/messages", json=message_data)

        # Assert
        assert response.status_code == 201
        override_service_dependency.create_message.assert_called_once()
        call_args = override_service_dependency.create_message.call_args[0][0]
        assert call_args.content == long_content

    def test_response_models_format(self, test_client, override_service_dependency):
        """Test that response models are properly formatted"""
        # Test sessions endpoint response format
        session_ids = [uuid.uuid4(), uuid.uuid4()]
        override_service_dependency.get_all_sessions.return_value = session_ids

        response = test_client.get("/sessions")
        assert response.status_code == 200
        response_data = response.json()

        # Should be a list of UUID strings
        assert isinstance(response_data, list)
        for session_id in response_data:
            assert isinstance(session_id, str)
            # Should be valid UUID format
            uuid.UUID(session_id)

    def test_cors_and_headers(self, test_client):
        """Test that endpoints return appropriate headers"""
        # Test health endpoint
        response = test_client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

        # Test root endpoint
        response = test_client.get("/")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
