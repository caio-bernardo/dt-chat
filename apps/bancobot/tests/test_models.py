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
    MessagePublicComplete,
    MessagePublicWithConversation,
    MessagePublicWithParent,
    MessageType,
)


class TestMessageType:
    """Test MessageType enum."""

    def test_message_type_ai(self):
        assert MessageType.AI == "ai"

    def test_message_type_human(self):
        assert MessageType.Human == "human"

    def test_message_type_system(self):
        assert MessageType.System == "System"

    def test_message_type_values(self):
        assert len(MessageType) == 3


class TestConversationCreate:
    """Test ConversationCreate model."""

    def test_conversation_create_minimal(self):
        conv = ConversationCreate()
        assert conv.meta == {}

    def test_conversation_create_with_meta(self):
        meta = {"persona": "test_user", "lang": "pt-BR"}
        conv = ConversationCreate(meta=meta)
        assert conv.meta == meta


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


class TestConversationPublic:
    """Test ConversationPublic model."""

    def test_conversation_public_creation(self):
        conv_id = uuid.uuid4()
        conv = ConversationPublic(id=conv_id, meta={}, created_at=dt.datetime.now())
        assert conv.id == conv_id
        assert conv.meta == {}

    def test_conversation_public_with_meta(self):
        meta = {"persona": "user1"}
        conv = ConversationPublic(
            id=uuid.uuid4(),
            meta=meta,
            created_at=dt.datetime.now(),
        )
        assert conv.meta == meta


class TestConversationPublicWithMessages:
    """Test ConversationPublicWithMessages model."""

    def test_conversation_public_with_messages(self):
        conv = ConversationPublicWithMessages(
            id=uuid.uuid4(),
            meta={},
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

    def test_message_create_with_parent_message_id(self, conversation):
        parent_id = uuid.uuid4()
        msg = MessageCreate(
            conversation_id=conversation.id,
            content="Reply message",
            parent_message_id=parent_id,
        )
        assert msg.parent_message_id == parent_id


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

    def test_message_with_parent_message_id(self, conversation):
        parent_id = uuid.uuid4()
        msg = Message(
            conversation_id=conversation.id,
            content="Reply to parent",
            parent_message_id=parent_id,
        )
        assert msg.parent_message_id == parent_id
        assert msg.created_at is not None


class TestMessagePublic:
    """Test MessagePublic model."""

    def test_message_public_creation(self, conversation):
        msg = MessagePublic(
            id=1,
            conversation_id=conversation.id,
            content="Public message",
            type=MessageType.AI,
            created_at=dt.datetime.now(),
        )
        assert msg.id == 1
        assert msg.content == "Public message"
        assert msg.type == MessageType.AI

    def test_message_public_with_parent_message_id(self, conversation):
        parent_id = uuid.uuid4()
        msg = MessagePublic(
            id=1,
            conversation_id=conversation.id,
            content="Public message with parent",
            type=MessageType.Human,
            parent_message_id=parent_id,
            created_at=dt.datetime.now(),
        )
        assert msg.parent_message_id == parent_id


class TestMessagePublicWithConversation:
    """Test MessagePublicWithConversation model."""

    def test_message_public_with_conversation(self, conversation):
        msg = MessagePublicWithConversation(
            id=1,
            conversation_id=conversation.id,
            content="Test",
            type=MessageType.Human,
            created_at=dt.datetime.now(),
            conversation=ConversationPublic(
                id=conversation.id,
                meta=conversation.meta,
                created_at=conversation.created_at,
            ),
        )
        assert msg.id == 1
        assert msg.conversation_id == conversation.id
        assert hasattr(msg, "conversation")


class TestMessagePublicWithParent:
    """Test MessagePublicWithParent model."""

    def test_message_public_with_parent_no_parent(self, conversation):
        msg = MessagePublicWithParent(
            id=1,
            conversation_id=conversation.id,
            content="First message",
            type=MessageType.Human,
            created_at=dt.datetime.now(),
            parent=None,
        )
        assert msg.id == 1
        assert msg.parent is None

    def test_message_public_with_parent_with_parent(self, conversation):
        parent_msg = MessagePublicWithConversation(
            id=1,
            conversation_id=conversation.id,
            content="Parent message",
            type=MessageType.Human,
            created_at=dt.datetime.now(),
            conversation=ConversationPublic(
                id=conversation.id,
                meta=conversation.meta,
                created_at=conversation.created_at,
            ),
        )
        msg = MessagePublicWithParent(
            id=2,
            conversation_id=conversation.id,
            content="Child message",
            type=MessageType.AI,
            created_at=dt.datetime.now(),
            parent=parent_msg,
        )
        assert msg.id == 2
        assert msg.parent is not None
        assert msg.parent.id == 1


class TestMessagePublicComplete:
    """Test MessagePublicComplete model."""

    def test_message_public_complete_creation(self, conversation):
        msg = MessagePublicComplete(
            id=1,
            conversation_id=conversation.id,
            content="Complete message",
            type=MessageType.Human,
            created_at=dt.datetime.now(),
            conversation=ConversationPublic(
                id=conversation.id,
                meta=conversation.meta,
                created_at=conversation.created_at,
            ),
            parent=None,
        )
        assert msg.id == 1
        assert msg.conversation_id == conversation.id
        assert msg.type == MessageType.Human
        assert hasattr(msg, "conversation")
        assert hasattr(msg, "parent")

    def test_message_public_complete_with_parent(self, conversation, timing_metadata):
        parent_msg = MessagePublicWithConversation(
            id=1,
            conversation_id=conversation.id,
            content="Parent",
            type=MessageType.Human,
            timing_metadata=timing_metadata,
            created_at=dt.datetime.now(),
            conversation=ConversationPublic(
                id=conversation.id,
                meta=conversation.meta,
                created_at=conversation.created_at,
            ),
        )
        msg = MessagePublicComplete(
            id=2,
            conversation_id=conversation.id,
            content="Child message",
            type=MessageType.AI,
            timing_metadata=timing_metadata,
            created_at=dt.datetime.now(),
            conversation=ConversationPublic(
                id=conversation.id,
                meta=conversation.meta,
                created_at=conversation.created_at,
            ),
            parent=parent_msg,
        )
        assert msg.parent is not None
        assert msg.parent.content == "Parent"
