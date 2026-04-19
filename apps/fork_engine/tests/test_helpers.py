import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bancobot.database import MessageType
from bancobot.models import Message
from langchain_core.messages import AIMessage, HumanMessage
from userbot import TimeSimulationConfig

from fork_engine.helpers import (
    BancobotProcedureCallSender,
    map_internal_2_langchain_message,
    retrieve_timesim_from_metadata,
    retrieve_userbot_persona_from_metadata,
)


class TestMessageMapping:
    """Test message type mapping."""

    def test_map_human_message(self):
        """Test mapping human message."""
        msg = Message(
            id=1,
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
            id=1,
            conversation_id=uuid.uuid4(),
            type=MessageType.AI,
            content="Hi there",
            timing_metadata={},  # pyright: ignore[reportArgumentType]
        )
        result = map_internal_2_langchain_message(msg)
        assert isinstance(result, AIMessage)
        assert result.content == "Hi there"


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

    def test_service_source_set(self, sender):
        """Test that service source is set to twin_bancobot."""
        assert sender._service.source == "twin_bancobot"

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
        msg = HumanMessage(content="Hello", timing_metadata={"pause": 1})

        with patch.object(
            sender._service, "save_publish_answer_message", new_callable=AsyncMock
        ) as mock_save:
            mock_answer = MagicMock()
            mock_answer.content = "Response"
            mock_answer.timing_metadata = {"pause": 1}
            mock_save.return_value = mock_answer

            result = await sender.send_message(msg)

            assert isinstance(result, AIMessage)
            assert result.content == "Response"
            mock_save.assert_called_once()
