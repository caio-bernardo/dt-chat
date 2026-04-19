import datetime as dt
import uuid

from bancobot.models import (
    Conversation,
    ConversationCreate,
    ConversationPublic,
    ConversationPublicWithMessages,
    Message,
    MessageCreate,
    MessagePublic,
    MessagePublicWithoutConversation,
    MessageType,
)


class TestMessageType:
    """Test MessageType enum."""

    def test_message_type_ai(self):
        assert MessageType.AI == "ai"

    def test_message_type_human(self):
        assert MessageType.Human == "human"

    def test_message_type_values(self):
        assert len(MessageType) == 2


class TestConversationCreate:
    """Test ConversationCreate model."""

    def test_conversation_create_minimal(self):
        conv = ConversationCreate()
        assert conv.meta == {}

    def test_conversation_create_with_meta(self):
        meta = {"persona": "test_user", "lang": "pt-BR"}
        conv = ConversationCreate(meta=meta)
        assert conv.meta == meta

    def test_conversation_create_with_parent(self):
        parent_id = uuid.uuid4()
        conv = ConversationCreate(parent_conversation_id=parent_id)
        assert conv.parent_conversation_id == parent_id


class TestConversation:
    """Test Conversation model."""

    def test_conversation_creation(self):
        conv = Conversation(meta={"test": "data"})
        assert conv.id is not None
        assert conv.created_at is not None
        assert conv.meta == {"test": "data"}

    def test_conversation_defaults(self):
        conv = Conversation()
        assert isinstance(conv.id, uuid.UUID)
        assert isinstance(conv.created_at, dt.datetime)
        assert conv.meta == {}
        assert conv.parent_conversation_id is None

    def test_conversation_with_parent_id(self):
        parent_id = uuid.uuid4()
        conv = Conversation(parent_conversation_id=parent_id)
        assert conv.parent_conversation_id == parent_id


class TestConversationPublic:
    """Test ConversationPublic model."""

    def test_conversation_public_creation(self):
        conv_id = uuid.uuid4()
        conv = ConversationPublic(
            id=conv_id, meta={}, children_conversations=[], created_at=dt.datetime.now()
        )
        assert conv.id == conv_id
        assert conv.children_conversations == []

    def test_conversation_public_with_meta(self):
        meta = {"persona": "user1"}
        conv = ConversationPublic(
            id=uuid.uuid4(),
            meta=meta,
            children_conversations=[],
            created_at=dt.datetime.now(),
        )
        assert conv.meta == meta


class TestConversationPublicWithMessages:
    """Test ConversationPublicWithMessages model."""

    def test_conversation_public_with_messages(self):
        conv = ConversationPublicWithMessages(
            id=uuid.uuid4(),
            meta={},
            children_conversations=[],
            created_at=dt.datetime.now(),
            messages=[],
        )
        assert conv.messages == []
        assert isinstance(conv.id, uuid.UUID)


class TestMessageCreate:
    """Test MessageCreate model."""

    def test_message_create_minimal(self, conversation):
        msg = MessageCreate(
            conversation_id=conversation.id,
            content="Hello",
        )
        assert msg.conversation_id == conversation.id
        assert msg.content == "Hello"
        assert msg.type == MessageType.Human
        assert msg.timing_metadata == {}

    def test_message_create_with_ai_type(self, conversation):
        msg = MessageCreate(
            conversation_id=conversation.id,
            content="Response",
            type=MessageType.AI,
        )
        assert msg.type == MessageType.AI

    def test_message_create_with_timing_metadata(self, conversation, timing_metadata):
        msg = MessageCreate(
            conversation_id=conversation.id,
            content="Test",
            timing_metadata=timing_metadata,
        )
        assert msg.timing_metadata == timing_metadata


class TestMessage:
    """Test Message model."""

    def test_message_creation(self, conversation):
        msg = Message(
            conversation_id=conversation.id,
            content="Test message",
            type=MessageType.Human,
        )
        assert msg.conversation_id == conversation.id
        assert msg.content == "Test message"
        assert msg.type == MessageType.Human
        assert msg.created_at is not None

    def test_message_defaults(self, conversation):
        msg = Message(
            conversation_id=conversation.id,
            content="Test",
        )
        assert msg.type == MessageType.Human
        assert msg.timing_metadata == {}

    def test_message_with_timing_metadata(self, conversation, timing_metadata):
        msg = Message(
            conversation_id=conversation.id,
            content="Test",
            timing_metadata=timing_metadata,
        )
        assert msg.timing_metadata == timing_metadata


class TestMessagePublic:
    """Test MessagePublic model."""

    def test_message_public_creation(self, conversation):
        msg = MessagePublic(
            id=1,
            conversation_id=conversation.id,
            content="Public message",
            type=MessageType.AI,
            conversation=ConversationPublic(
                id=conversation.id,
                meta=conversation.meta,
                children_conversations=[],
                created_at=conversation.created_at,
            ),
            created_at=dt.datetime.now(),
        )
        assert msg.id == 1
        assert msg.content == "Public message"
        assert msg.type == MessageType.AI


class TestMessagePublicWithoutConversation:
    """Test MessagePublicWithoutConversation model."""

    def test_message_public_without_conversation(self, conversation):
        msg = MessagePublicWithoutConversation(
            id=1,
            conversation_id=conversation.id,
            content="Test",
            type=MessageType.Human,
            created_at=dt.datetime.now(),
        )
        assert msg.id == 1
        assert msg.conversation_id == conversation.id
        assert not hasattr(msg, "conversation")
