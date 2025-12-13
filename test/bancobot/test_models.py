import uuid
import datetime as dt
from sqlmodel import SQLModel, create_engine, Session

from bancobot.models import Message, MessageType, MessageCreate


class TestMessage:
    """Test cases for the Message model"""

    def test_message_creation_with_defaults(self):
        """Test creating a message with default values"""
        message = Message(content="Hello world")

        assert message.content == "Hello world"
        assert message.type == MessageType.Human
        assert message.id is None
        assert isinstance(message.session_id, uuid.UUID)
        assert isinstance(message.created_at, dt.datetime)

    def test_message_creation_with_all_fields(self):
        """Test creating a message with all fields specified"""
        session_id = uuid.uuid4()
        created_at = dt.datetime.now()

        message = Message(
            id=1,
            session_id=session_id,
            content="Test message",
            type=MessageType.AI,
            created_at=created_at,
        )

        assert message.id == 1
        assert message.session_id == session_id
        assert message.content == "Test message"
        assert message.type == MessageType.AI
        assert message.created_at == created_at

    def test_message_type_enum_values(self):
        """Test that MessageType enum has correct values"""
        assert MessageType.AI == "ai"
        assert MessageType.Human == "Human"

    def test_message_with_ai_type(self):
        """Test creating a message with AI type"""
        message = Message(content="AI response", type=MessageType.AI)

        assert message.type == MessageType.AI
        assert message.content == "AI response"

    def test_message_database_persistence(self):
        """Test that messages can be persisted to and retrieved from database"""
        # Create in-memory database
        engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(engine)

        session_id = uuid.uuid4()

        with Session(engine) as session:
            # Create and save message
            message = Message(
                session_id=session_id,
                content="Test persistence",
                type=MessageType.Human,
            )
            session.add(message)
            session.commit()
            session.refresh(message)

            # Verify message was saved
            assert message.id is not None

            # Retrieve message from database
            retrieved_message = session.get(Message, message.id)
            assert retrieved_message is not None
            assert retrieved_message.content == "Test persistence"
            assert retrieved_message.session_id == session_id
            assert retrieved_message.type == MessageType.Human


class TestMessageCreate:
    """Test cases for the MessageCreate model"""

    def test_message_create_with_session_id(self):
        """Test creating MessageCreate with session_id"""
        session_id = uuid.uuid4()
        message_create = MessageCreate(session_id=session_id, content="Hello world")

        assert message_create.session_id == session_id
        assert message_create.content == "Hello world"

    def test_message_create_without_session_id(self):
        """Test creating MessageCreate without session_id (optional field)"""
        message_create = MessageCreate(content="Hello without session")

        assert message_create.session_id is None
        assert message_create.content == "Hello without session"

    def test_message_create_model_dump(self):
        """Test that MessageCreate can be dumped to dict"""
        session_id = uuid.uuid4()
        message_create = MessageCreate(session_id=session_id, content="Test content")

        dumped = message_create.model_dump()

        assert dumped["session_id"] == session_id
        assert dumped["content"] == "Test content"

    def test_message_create_without_session_id_model_dump(self):
        """Test model_dump when session_id is None"""
        message_create = MessageCreate(content="Test content")

        dumped = message_create.model_dump()

        assert dumped["session_id"] is None
        assert dumped["content"] == "Test content"

    def test_message_create_to_message_conversion(self):
        """Test converting MessageCreate to Message"""
        session_id = uuid.uuid4()
        message_create = MessageCreate(session_id=session_id, content="Test conversion")

        # This simulates what happens in the service
        message = Message(**message_create.model_dump())

        assert message.session_id == session_id
        assert message.content == "Test conversion"
        assert message.type == MessageType.Human  # Default value
        assert isinstance(message.created_at, dt.datetime)


class TestMessageTypeEnum:
    """Test cases for the MessageType enum"""

    def test_enum_values(self):
        """Test that enum values are correctly defined"""
        assert MessageType.AI.value == "ai"
        assert MessageType.Human.value == "Human"

    def test_enum_comparison(self):
        """Test enum comparison operations"""
        assert MessageType.AI == "ai"
        assert MessageType.Human == "Human"
        assert MessageType.AI != MessageType.Human

    def test_enum_string_representation(self):
        """Test string representation of enum values"""
        assert str(MessageType.AI) == "MessageType.AI"
        assert str(MessageType.Human) == "MessageType.Human"
