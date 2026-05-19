import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bancobot.database import MessageType
from bancobot.models import Message
from chatbot import AIMessage, HumanMessage
from fork_engine.helpers import (
    map_internal_2_langchain_message,
    retrieve_messages_until,
    retrieve_timesim_from_metadata,
    retrieve_userbot_persona_from_metadata,
)
from fork_engine.procedure import BancobotProcedureCallSender
from userbot import TimeSimulationConfig


class TestMessageMapping:
    """Test message type mapping."""

    def test_map_human_message(self):
        """Test mapping human message."""
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            type=MessageType.Human,
            content="Hello",
            timing_metadata={},  # pyright: ignore[reportArgumentType]
        )
        result = map_internal_2_langchain_message(msg)
        assert isinstance(result, HumanMessage)
        assert result.content == "Hello"

    def test_map_ai_message(self):
        """Test mapping AI message."""
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.uuid4(),
            type=MessageType.AI,
            content="Hi there",
            timing_metadata={},  # pyright: ignore[reportArgumentType]
        )
        result = map_internal_2_langchain_message(msg)
        assert isinstance(result, AIMessage)
        assert result.content == "Hi there"


class TestRetrieveMessagesUntil:
    def test_retrieve_messages_until_includes_target_and_orders(self, db_session):
        import datetime as dt

        from bancobot.models import Conversation, Message

        conv = Conversation(id=uuid.uuid4(), meta={})  # pyright: ignore[reportArgumentType]
        db_session.add(conv)
        db_session.flush()

        t0 = dt.datetime(2024, 1, 1, 12, 0, 0)
        m1 = Message(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            type=MessageType.Human,
            content="m1",
            timing_metadata={},  # pyright: ignore[reportArgumentType]
            created_at=t0,
        )
        m2 = Message(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            type=MessageType.Human,
            content="m2",
            timing_metadata={},  # pyright: ignore[reportArgumentType]
            created_at=t0.replace(minute=1),
        )
        m3 = Message(
            id=uuid.uuid4(),
            conversation_id=conv.id,
            type=MessageType.Human,
            content="m3",
            timing_metadata={},  # pyright: ignore[reportArgumentType]
            created_at=t0.replace(minute=2),
        )
        db_session.add(m1)
        db_session.add(m2)
        db_session.add(m3)
        db_session.flush()

        res = retrieve_messages_until(db_session, m2)

        assert [m.content for m in res] == ["m1", "m2"]


class TestMetadataRetrieval:
    """Test metadata extraction functions."""

    def test_retrieve_timesim_from_valid_metadata(self):
        """Test retrieving TimeSimulationConfig from metadata."""
        meta = {
            "timesim": {
                "base_time": 1.0,
                "speed_multiplier": 1.0,
                "pause_seconds": 0.5,
            }
        }
        result = retrieve_timesim_from_metadata(meta)
        assert isinstance(result, TimeSimulationConfig)

    def test_retrieve_timesim_missing_key(self):
        """Test retrieving TimeSimulationConfig with missing key raises error."""
        meta = {"persona": "test"}
        with pytest.raises(AssertionError):
            retrieve_timesim_from_metadata(meta)

    def test_retrieve_persona_from_metadata(self):
        """Test retrieving persona from metadata."""
        meta = {"persona": "friendly banker"}
        result = retrieve_userbot_persona_from_metadata(meta)
        assert result == "friendly banker"

    def test_retrieve_persona_missing_key(self):
        """Test retrieving persona with missing key raises error."""
        meta = {"timesim": {}}
        with pytest.raises(AssertionError):
            retrieve_userbot_persona_from_metadata(meta)


class TestBancobotProcedureCallSender:
    """Test BancobotProcedureCallSender class."""

    @pytest.fixture
    def sender(self, mock_bancobot_agent, db_session, mock_queue_prod):
        """Create a BancobotProcedureCallSender instance."""
        return BancobotProcedureCallSender(
            parent_id=uuid.uuid4(),
            agent=mock_bancobot_agent,
            storage=db_session,
            producer=mock_queue_prod,
        )

    def test_init(self, sender):
        """Test BancobotProcedureCallSender initialization."""
        assert sender.parent_conversation_id is not None
        assert sender.conversation_id is None
        assert sender._service is not None
        assert sender._metadata is None

    def test_init_with_metadata(self, mock_bancobot_agent, db_session, mock_queue_prod):
        """Test BancobotProcedureCallSender initialization with metadata."""
        metadata = {"branched_message_id": "123", "twinbot_type": "test"}
        sender = BancobotProcedureCallSender(
            parent_id=uuid.uuid4(),
            agent=mock_bancobot_agent,
            storage=db_session,
            producer=mock_queue_prod,
            metadata=metadata,
        )
        assert sender._metadata == metadata

    def test_service_source_set(self, sender):
        """Test that service source is set to twin_bancobot."""
        assert sender._service.source == "twin_bancobot"

    @pytest.mark.asyncio
    async def test_create_channel_merges_metadata(
        self, mock_bancobot_agent, db_session, mock_queue_prod
    ):
        """Test that create_channel merges metadata with data."""
        metadata = {"branched_message_id": "123", "twinbot_type": "test"}
        sender = BancobotProcedureCallSender(
            parent_id=uuid.uuid4(),
            agent=mock_bancobot_agent,
            storage=db_session,
            producer=mock_queue_prod,
            metadata=metadata,
        )
        data = {"custom_field": "value"}

        with patch.object(
            sender._service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_conv = MagicMock()
            mock_conv.id = uuid.uuid4()
            mock_create.return_value = mock_conv

            await sender.create_channel(data)

            # Verify metadata was merged into the call
            call_args = mock_create.call_args
            props = call_args[0][0]
            assert props.meta["branched_message_id"] == "123"
            assert props.meta["twinbot_type"] == "test"
            assert props.meta["custom_field"] == "value"

    @pytest.mark.asyncio
    async def test_create_channel(self, sender, db_session):
        """Test creating a channel."""
        data = {"custom_field": "value"}

        with patch.object(
            sender._service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_conv = MagicMock()
            mock_conv.id = uuid.uuid4()
            mock_create.return_value = mock_conv

            await sender.create_channel(data)

            assert sender.conversation_id == mock_conv.id
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_channel_no_data(self, sender):
        """Test creating a channel without data."""
        with patch.object(
            sender._service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_conv = MagicMock()
            mock_conv.id = uuid.uuid4()
            mock_create.return_value = mock_conv

            await sender.create_channel()

            assert sender.conversation_id == mock_conv.id

    @pytest.mark.asyncio
    async def test_send_message_without_channel(self, sender):
        """Test sending message without creating channel raises error."""
        msg = HumanMessage(content="Hello")

        with pytest.raises(ValueError, match="Conversation not created yet"):
            await sender.send_message(msg)

    @pytest.mark.asyncio
    async def test_send_message_success(self, sender):
        """Test sending message successfully."""
        # Setup conversation
        sender.conversation_id = uuid.uuid4()
        timing_metadata = {
            "simulated_timestamp": 1.0,
            "typing_time": 0.1,
            "thinking_time": 0.2,
            "pause_time": 0.3,
        }
        msg = HumanMessage(content="Hello", timing_metadata=timing_metadata)

        with patch.object(
            sender._service, "save_publish_answer_message", new_callable=AsyncMock
        ) as mock_save:
            mock_answer = MagicMock()
            mock_answer.content = "Response"
            mock_answer.timing_metadata = timing_metadata
            mock_save.return_value = mock_answer

            result = await sender.send_message(msg)

            assert isinstance(result, AIMessage)
            assert result.content == "Response"
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_channel_without_metadata(
        self, mock_bancobot_agent, db_session, mock_queue_prod
    ):
        """Test creating a channel without metadata."""
        sender = BancobotProcedureCallSender(
            parent_id=uuid.uuid4(),
            agent=mock_bancobot_agent,
            storage=db_session,
            producer=mock_queue_prod,
        )
        data = {"custom_field": "value"}

        with patch.object(
            sender._service, "create_session", new_callable=AsyncMock
        ) as mock_create:
            mock_conv = MagicMock()
            mock_conv.id = uuid.uuid4()
            mock_create.return_value = mock_conv

            await sender.create_channel(data)

            assert sender.conversation_id == mock_conv.id
            # Verify data was passed correctly
            call_args = mock_create.call_args
            props = call_args[0][0]
            assert props.meta["custom_field"] == "value"
