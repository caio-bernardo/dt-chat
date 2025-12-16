import pytest
import uuid
from unittest.mock import Mock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine, Session

from bancobot.agent import BancoAgent
from bancobot.routes import router
from bancobot.dependecies import get_session, get_banco_agent

# Needed, so SQLModel can create them
from bancobot.models import *  # noqa: F403  # pyright: ignore[reportWildcardImportFromLibrary]


@pytest.fixture(scope="function")
def integration_engine() -> Engine:
    """Create a shared in-memory database for integration tests.

    Use StaticPool so the same in-memory SQLite database is reused across threads
    (FastAPI TestClient runs the app in a different thread). Keep
    check_same_thread=False to ensure connections may be used from other threads.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def integration_session(integration_engine: Engine):
    """Create a database session for integration tests"""
    session = Session(integration_engine)
    yield session
    session.close()


@pytest.fixture
def mock_agent():
    """Create a mock agent for integration tests"""
    agent = Mock(spec=BancoAgent)
    agent.process_message = Mock(
        side_effect=lambda thread_id, message: Mock(
            content=f"AI response to: {message.content}"
        )
    )
    return agent


@pytest.fixture(scope="function")
def integration_app(integration_engine: Engine, mock_agent: Mock):
    """Create a FastAPI app for integration testing.

    Use per-request sessions (via overriding `get_session`) so each request gets
    a fresh Session bound to the same in-memory engine. This avoids sharing a
    single Session object across threads while still keeping the same in-memory
    database (StaticPool is configured on the engine).
    """
    app = FastAPI()
    app.include_router(router)

    # Provide a per-request session that uses the shared in-memory engine
    def get_test_session():
        with Session(integration_engine) as s:
            yield s

    # Provide the mock agent whenever the app asks for a BancoAgent
    def get_test_agent():
        return mock_agent

    # Override the dependencies used by get_bbchat_service:
    # - get_session -> yields a fresh session per request
    # - get_banco_agent -> returns our mock agent
    app.dependency_overrides[get_session] = get_test_session
    app.dependency_overrides[get_banco_agent] = get_test_agent

    # We don't override get_bbchat_service itself; the real dependency will be
    # constructed using the overridden session and agent, producing a
    # BancoBotService that uses a request-scoped Session.
    return app


@pytest.fixture
def integration_client(integration_app: FastAPI) -> TestClient:
    """Create a test client for integration tests"""
    return TestClient(integration_app)


class TestIntegration:
    """Integration tests that test the full flow of the application"""

    def test_full_conversation_flow(self, integration_client: TestClient):
        """Test a complete conversation flow from start to finish"""
        # Step 1: Create first message (should generate new session)
        message_data = {
            "content": "Hello, I need help with my account"
        }

        response = integration_client.post("/messages", json=message_data)
        assert response.status_code == 201, response.json()

        first_response = response.json()
        session_id = first_response["session_id"]
        assert first_response["type"] == "ai"
        assert "AI response to: Hello, I need help with my account" in first_response["content"]

        # Step 2: Continue conversation with same session
        message_data = {
            "session_id": session_id,
            "content": "What's my balance?"
        }

        response = integration_client.post("/messages", json=message_data)
        assert response.status_code == 201

        second_response = response.json()
        assert second_response["session_id"] == session_id
        assert "AI response to: What's my balance?" in second_response["content"]

        # Step 3: Get all sessions (should include our session)
        response = integration_client.get("/sessions")
        assert response.status_code == 200
        sessions = response.json()
        assert session_id in sessions

        # Step 4: Get all messages for the session
        response = integration_client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        messages = response.json()

        # Should have 4 messages: 2 human, 2 AI
        assert len(messages) == 4
        human_messages = [msg for msg in messages if msg["type"] == "Human"]
        ai_messages = [msg for msg in messages if msg["type"] == "ai"]
        assert len(human_messages) == 2
        assert len(ai_messages) == 2

        # Step 5: Delete the session
        response = integration_client.delete(f"/sessions/{session_id}")
        assert response.status_code == 200

        # Step 6: Verify session is empty after deletion
        response = integration_client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 0

    def test_multiple_concurrent_sessions(self, integration_client):
        """Test handling multiple concurrent sessions"""
        # Create messages for multiple sessions
        sessions_data = []

        for i in range(3):
            message_data = {
                "content": f"Hello from session {i}"
            }

            response = integration_client.post("/messages", json=message_data)
            assert response.status_code == 201

            response_data = response.json()
            sessions_data.append({
                "session_id": response_data["session_id"],
                "message_content": f"Hello from session {i}"
            })

        # Verify all sessions are created
        response = integration_client.get("/sessions")
        assert response.status_code == 200
        all_sessions = response.json()
        assert len(all_sessions) >= 3

        # Verify each session has correct messages
        for session_data in sessions_data:
            session_id = session_data["session_id"]
            response = integration_client.get(f"/sessions/{session_id}")
            assert response.status_code == 200

            messages = response.json()
            assert len(messages) == 2  # Human + AI response

            # Find the human message
            human_message = next(msg for msg in messages if msg["type"] == "Human")
            assert human_message["content"] == session_data["message_content"]

    def test_error_handling_integration(self, integration_client):
        """Test error handling in the full integration flow"""
        # Test with invalid session UUID
        response = integration_client.get("/sessions/invalid-uuid")
        assert response.status_code == 422

        # Test creating message with invalid session UUID
        message_data = {
            "session_id": "invalid-uuid",
            "content": "Test message"
        }
        response = integration_client.post("/messages", json=message_data)
        assert response.status_code == 422

        # Test getting non-existent session
        non_existent_session = str(uuid.uuid4())
        response = integration_client.get(f"/sessions/{non_existent_session}")
        assert response.status_code == 200
        assert response.json() == []

        # Test deleting non-existent session
        response = integration_client.delete(f"/sessions/{non_existent_session}")
        assert response.status_code == 200

    def test_api_endpoints_health_check(self, integration_client):
        """Test all basic API endpoints are working"""
        # Test root endpoint
        response = integration_client.get("/")
        assert response.status_code == 200
        assert "Root of BancoBotAPI" in response.json()["detail"]

        # Test health endpoint
        response = integration_client.get("/health")
        assert response.status_code == 200
        assert response.json()["detail"] == "API is on air."

        # Test sessions endpoint (empty initially)
        response = integration_client.get("/sessions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_message_persistence_and_retrieval(self, integration_client):
        """Test that messages are properly persisted and can be retrieved"""
        # Create a message
        message_data = {
            "content": "Test persistence message"
        }

        response = integration_client.post("/messages", json=message_data)
        assert response.status_code == 201

        ai_response = response.json()
        session_id = ai_response["session_id"]

        # Get messages immediately after creation
        response = integration_client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 2

        # Verify content is preserved
        human_message = next(msg for msg in messages if msg["type"] == "Human")
        ai_message = next(msg for msg in messages if msg["type"] == "ai")

        assert human_message["content"] == "Test persistence message"
        assert "AI response to: Test persistence message" in ai_message["content"]
        assert human_message["session_id"] == session_id
        assert ai_message["session_id"] == session_id

    def test_session_isolation(self, integration_client):
        """Test that different sessions are properly isolated"""
        # Create two different sessions
        session1_response = integration_client.post("/messages", json={
            "content": "Message for session 1"
        })
        assert session1_response.status_code == 201
        session1_id = session1_response.json()["session_id"]

        session2_response = integration_client.post("/messages", json={
            "content": "Message for session 2"
        })
        assert session2_response.status_code == 201
        session2_id = session2_response.json()["session_id"]

        # Verify they have different session IDs
        assert session1_id != session2_id

        # Add more messages to each session
        integration_client.post("/messages", json={
            "session_id": session1_id,
            "content": "Second message for session 1"
        })

        integration_client.post("/messages", json={
            "session_id": session2_id,
            "content": "Second message for session 2"
        })

        # Verify session 1 messages
        response = integration_client.get(f"/sessions/{session1_id}")
        assert response.status_code == 200
        session1_messages = response.json()

        session1_human_messages = [msg for msg in session1_messages if msg["type"] == "Human"]
        assert len(session1_human_messages) == 2
        assert any("session 1" in msg["content"] for msg in session1_human_messages)
        assert not any("session 2" in msg["content"] for msg in session1_human_messages)

        # Verify session 2 messages
        response = integration_client.get(f"/sessions/{session2_id}")
        assert response.status_code == 200
        session2_messages = response.json()

        session2_human_messages = [msg for msg in session2_messages if msg["type"] == "Human"]
        assert len(session2_human_messages) == 2
        assert any("session 2" in msg["content"] for msg in session2_human_messages)
        assert not any("session 1" in msg["content"] for msg in session2_human_messages)

    def test_content_validation_edge_cases(self, integration_client):
        """Test edge cases for content validation"""
        # Test with very long content
        long_content = "A" * 5000
        response = integration_client.post("/messages", json={
            "content": long_content
        })
        assert response.status_code == 201

        # Test with special characters
        special_content = "Hello! @#$%^&*()_+ 中文 🚀 \n\t\r"
        response = integration_client.post("/messages", json={
            "content": special_content
        })
        assert response.status_code == 201

        # Test with empty string (if allowed)
        response = integration_client.post("/messages", json={
            "content": ""
        })
        assert response.status_code == 201

        # Test with only whitespace
        response = integration_client.post("/messages", json={
            "content": "   \n\t   "
        })
        assert response.status_code == 201

    def test_concurrent_operations_same_session(self, integration_client):
        """Test concurrent operations on the same session"""
        # Create initial message
        response = integration_client.post("/messages", json={
            "content": "Initial message"
        })
        assert response.status_code == 201
        session_id = response.json()["session_id"]

        # Simulate concurrent operations by rapidly adding messages
        responses = []
        for i in range(5):
            response = integration_client.post("/messages", json={
                "session_id": session_id,
                "content": f"Concurrent message {i}"
            })
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 201

        # Verify all messages are in the session
        response = integration_client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        messages = response.json()

        # Should have 12 messages: 6 human (initial + 5 concurrent) + 6 AI responses
        assert len(messages) == 12

        human_messages = [msg for msg in messages if msg["type"] == "Human"]
        assert len(human_messages) == 6

    def test_message_creation_without_session_id(self, integration_client):
        """Test creating messages without providing session_id"""
        # Create message without session_id - should auto-generate one
        response = integration_client.post("/messages", json={
            "content": "Message without session ID"
        })
        assert response.status_code == 201

        response_data = response.json()
        session_id = response_data["session_id"]
        assert session_id is not None

        # Verify the session was created and contains the messages
        response = integration_client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) == 2  # Human + AI response

    def test_database_transaction_handling(self, integration_client, mock_agent):
        """Test that database transactions are handled correctly"""
        # This test ensures that if something fails, the database state remains consistent
        # Create a successful message first
        response = integration_client.post("/messages", json={
            "content": "Successful message"
        })
        assert response.status_code == 201
        session_id = response.json()["session_id"]

        # Verify we have 2 messages (human + AI)
        response = integration_client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # The mock agent should continue to work for subsequent requests
        response = integration_client.post("/messages", json={
            "session_id": session_id,
            "content": "Another message"
        })
        assert response.status_code == 201

        # Verify we now have 4 messages
        response = integration_client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        assert len(response.json()) == 4
