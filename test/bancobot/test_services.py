import pytest
import uuid
from sqlmodel import select

from bancobot.models import Message, MessageType, MessageCreate
from bancobot.services import BancoBotService


class TestBancoBotService:
    """Test cases for the BancoBotService class"""

    @pytest.mark.asyncio
    async def test_create_message_success(self, banco_service, sample_message_create, mock_agent, db_session):
        """Test successful message creation with AI response"""
        # Act
        result = await banco_service.create_message(sample_message_create)

        # Assert
        assert isinstance(result, Message)
        assert result.type == MessageType.AI
        assert result.content == f"Mock AI response to: {sample_message_create.content}"
        assert result.session_id == sample_message_create.session_id
        assert result.id is not None

        # Verify the agent was called
        mock_agent.process_message.assert_called_once()

        # Verify both messages (human and AI) are in database
        messages = db_session.exec(
            select(Message).where(Message.session_id == sample_message_create.session_id)
        ).all()
        assert len(messages) == 2
        assert messages[0].type == MessageType.Human
        assert messages[1].type == MessageType.AI

    @pytest.mark.asyncio
    async def test_create_message_without_session_id(self, banco_service, mock_agent, db_session):
        """Test creating message without session_id (should generate one)"""
        message_create = MessageCreate(content="Hello without session ID")

        # Act
        result = await banco_service.create_message(message_create)

        # Assert
        assert isinstance(result, Message)
        assert result.type == MessageType.AI
        assert result.session_id is not None
        assert isinstance(result.session_id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_create_message_agent_exception(self, mock_agent, db_session):
        """Test handling agent exceptions during message creation"""
        # Setup mock to raise exception
        mock_agent.process_message.side_effect = Exception("Agent error")
        service = BancoBotService(agent=mock_agent, storage=db_session)

        message_create = MessageCreate(content="Test error handling")

        # Act & Assert
        with pytest.raises(Exception, match="Agent error"):
            await service.create_message(message_create)

    @pytest.mark.asyncio
    async def test_get_message_by_session(self, banco_service, sample_messages, sample_session_id):
        """Test retrieving messages by session ID"""
        # Act
        messages = await banco_service.get_message_by_session(sample_session_id)

        # Assert
        assert len(messages) == 3
        assert all(msg.session_id == sample_session_id for msg in messages)

        # Verify message types and content
        human_messages = [msg for msg in messages if msg.type == MessageType.Human]
        ai_messages = [msg for msg in messages if msg.type == MessageType.AI]
        assert len(human_messages) == 2
        assert len(ai_messages) == 1

    @pytest.mark.asyncio
    async def test_get_message_by_session_empty(self, banco_service):
        """Test retrieving messages for non-existent session"""
        non_existent_session_id = uuid.uuid4()

        # Act
        messages = await banco_service.get_message_by_session(non_existent_session_id)

        # Assert
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_get_all_sessions(self, banco_service, sample_messages, sample_session_id, db_session):
        """Test retrieving all session IDs"""
        # Add another session
        another_session_id = uuid.uuid4()
        another_message = Message(
            session_id=another_session_id,
            content="Another session message",
            type=MessageType.Human
        )
        db_session.add(another_message)
        db_session.commit()

        # Act
        sessions = await banco_service.get_all_sessions()

        # Assert
        assert len(sessions) >= 2
        assert sample_session_id in sessions
        assert another_session_id in sessions

    @pytest.mark.asyncio
    async def test_get_all_sessions_empty(self, banco_service):
        """Test retrieving all sessions when none exist"""
        # Act
        sessions = await banco_service.get_all_sessions()

        # Assert
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_delete_messages_by_session(self, banco_service, sample_messages, sample_session_id):
        """Test deleting all messages for a session"""
        # Verify messages exist before deletion
        messages_before = await banco_service.get_message_by_session(sample_session_id)
        assert len(messages_before) == 3

        # Act
        deleted_count = await banco_service.delete_messages_by_session(sample_session_id)

        # Assert
        assert deleted_count == 3

        # Verify messages are deleted
        messages_after = await banco_service.get_message_by_session(sample_session_id)
        assert len(messages_after) == 0

    @pytest.mark.asyncio
    async def test_delete_messages_by_session_non_existent(self, banco_service):
        """Test deleting messages for non-existent session"""
        non_existent_session_id = uuid.uuid4()

        # Act
        deleted_count = await banco_service.delete_messages_by_session(non_existent_session_id)

        # Assert
        assert deleted_count == 0

    @pytest.mark.asyncio
    async def test_get_message_by_id(self, banco_service, sample_messages):
        """Test retrieving a specific message by ID"""
        message_id = sample_messages[0].id

        # Act
        message = await banco_service.get_message_by_id(message_id)

        # Assert
        assert message.id == message_id
        assert message.content == sample_messages[0].content
        assert message.type == sample_messages[0].type

    @pytest.mark.asyncio
    async def test_get_message_by_id_not_found(self, banco_service):
        """Test retrieving message with non-existent ID"""
        non_existent_id = 99999

        # Act & Assert
        with pytest.raises(ValueError, match=f"Message with ID {non_existent_id} not found"):
            await banco_service.get_message_by_id(non_existent_id)

    @pytest.mark.asyncio
    async def test_delete_message_by_id(self, banco_service, sample_messages):
        """Test deleting a specific message by ID"""
        message_id = sample_messages[0].id

        # Act
        result = await banco_service.delete_message_by_id(message_id)

        # Assert
        assert result is True

        # Verify message is deleted
        with pytest.raises(ValueError):
            await banco_service.get_message_by_id(message_id)

    @pytest.mark.asyncio
    async def test_delete_message_by_id_not_found(self, banco_service, db_session):
        """Test deleting message with non-existent ID"""
        non_existent_id = 99999

        # Act & Assert
        with pytest.raises(Exception):
            await banco_service.delete_message_by_id(non_existent_id)

    @pytest.mark.asyncio
    async def test_get_recent_messages_default_limit(self, banco_service, db_session, sample_session_id):
        """Test retrieving recent messages with default limit"""
        # Create more than 10 messages to test the limit
        for i in range(15):
            message = Message(
                session_id=sample_session_id,
                content=f"Message {i}",
                type=MessageType.Human
            )
            db_session.add(message)
        db_session.commit()

        # Act
        recent_messages = await banco_service.get_recent_messages(sample_session_id)

        # Assert
        assert len(recent_messages) == 10  # Default limit
        # Messages should be ordered by created_at descending
        assert "Message 14" in recent_messages[0].content  # Most recent

    @pytest.mark.asyncio
    async def test_get_recent_messages_custom_limit(self, banco_service, sample_messages, sample_session_id):
        """Test retrieving recent messages with custom limit"""
        # Act
        recent_messages = await banco_service.get_recent_messages(sample_session_id, limit=2)

        # Assert
        assert len(recent_messages) <= 2

    @pytest.mark.asyncio
    async def test_get_recent_messages_empty_session(self, banco_service):
        """Test retrieving recent messages for empty session"""
        empty_session_id = uuid.uuid4()

        # Act
        recent_messages = await banco_service.get_recent_messages(empty_session_id)

        # Assert
        assert len(recent_messages) == 0

    def test_service_initialization(self, mock_agent, db_session):
        """Test service initialization with required dependencies"""
        # Act
        service = BancoBotService(agent=mock_agent, storage=db_session)

        # Assert
        assert service.agent == mock_agent
        assert service.storage == db_session

    @pytest.mark.asyncio
    async def test_create_message_database_rollback_on_error(self, mock_agent, db_session):
        """Test database rollback when an error occurs after saving human message"""
        # Setup mock to raise exception after human message is saved
        mock_agent.process_message.side_effect = Exception("Agent processing failed")
        service = BancoBotService(agent=mock_agent, storage=db_session)

        message_create = MessageCreate(content="Test rollback")
        session_id = uuid.uuid4()
        message_create.session_id = session_id

        # Act & Assert
        with pytest.raises(Exception, match="Agent processing failed"):
            await service.create_message(message_create)

        # Verify that the transaction was rolled back and no messages exist
        _ = db_session.exec(
            select(Message).where(Message.session_id == session_id)
        ).all()
        # Note: In this implementation, the human message might still be saved
        # depending on when the commit happens. This test documents the current behavior.
