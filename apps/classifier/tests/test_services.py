import datetime as dt
import uuid

import pytest
from bancobot.models import Conversation, Message
from sqlmodel import select

from classifier.models import Touchpoint


class TestCreateTouchpoint:
    """Test create_touchpoint method."""

    @pytest.mark.asyncio
    async def test_create_touchpoint_basic(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test creating a touchpoint from a message."""
        result = await classifier_service.create_touchpoint(
            sample_message, "Usuário", touchpoint_list
        )

        assert isinstance(result, Touchpoint)
        assert result.message_id == sample_message.id
        assert result.activity == "SALDO_CONSULTA"
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_touchpoint_calls_agent(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test that create_touchpoint calls the agent with correct params."""
        await classifier_service.create_touchpoint(
            sample_message, "Usuário", touchpoint_list
        )

        classifier_service.agent.classify.assert_called_once_with(
            sample_message.content, "Usuário", touchpoint_list
        )

    @pytest.mark.asyncio
    async def test_create_touchpoint_with_different_actor(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test creating a touchpoint with different actor types."""
        result = await classifier_service.create_touchpoint(
            sample_message, "Bot", touchpoint_list
        )

        assert result.activity == "SALDO_CONSULTA"
        classifier_service.agent.classify.assert_called_with(
            sample_message.content, "Bot", touchpoint_list
        )

    @pytest.mark.asyncio
    async def test_create_touchpoint_with_different_tp_list(
        self, classifier_service, sample_message
    ):
        """Test creating a touchpoint with different touchpoint lists."""
        tp_list = ["ATIVIDADE_A", "ATIVIDADE_B", "ATIVIDADE_C"]
        classifier_service.agent.classify.return_value = "ATIVIDADE_A"

        result = await classifier_service.create_touchpoint(
            sample_message, "Usuário", tp_list
        )

        assert result.activity == "ATIVIDADE_A"
        classifier_service.agent.classify.assert_called_once_with(
            sample_message.content, "Usuário", tp_list
        )


class TestSaveConversation:
    """Test save_conversation method."""

    def test_save_conversation(self, classifier_service, sample_conversation):
        """Test saving a conversation to database."""
        classifier_service.save_conversation(sample_conversation)

        stmt = select(Conversation).where(Conversation.id == sample_conversation.id)
        result = classifier_service.storage.exec(stmt).first()

        assert result is not None
        assert result.id == sample_conversation.id

    def test_save_conversation_persists(self, classifier_service, sample_conversation):
        """Test that saved conversation persists in database."""
        classifier_service.save_conversation(sample_conversation)
        saved_id = sample_conversation.id

        stmt = select(Conversation).where(Conversation.id == saved_id)
        result = classifier_service.storage.exec(stmt).first()

        assert result is not None
        assert result.meta == sample_conversation.meta


class TestSaveMessage:
    """Test save_message method."""

    def test_save_message(self, classifier_service, sample_message):
        """Test saving a message to database."""
        classifier_service.save_message(sample_message)

        stmt = select(Message).where(Message.id == sample_message.id)
        result = classifier_service.storage.exec(stmt).first()

        assert result is not None
        assert result.id == sample_message.id
        assert result.content == sample_message.content

    def test_save_message_persists(self, classifier_service, sample_message):
        """Test that saved message persists in database."""
        classifier_service.save_message(sample_message)
        saved_id = sample_message.id

        stmt = select(Message).where(Message.id == saved_id)
        result = classifier_service.storage.exec(stmt).first()

        assert result is not None
        assert result.content == "Qual é o meu saldo?"


class TestSaveTouchpoint:
    """Test save_touchpoint method."""

    def test_save_touchpoint(self, classifier_service, sample_touchpoint):
        """Test saving a touchpoint to database."""
        classifier_service.save_touchpoint(sample_touchpoint)
        assert sample_touchpoint.id is not None

    def test_save_touchpoint_persists(self, classifier_service, sample_touchpoint):
        """Test that saved touchpoint persists in database."""
        classifier_service.save_touchpoint(sample_touchpoint)
        saved_id = sample_touchpoint.id

        stmt = select(Touchpoint).where(Touchpoint.id == saved_id)
        result = classifier_service.storage.exec(stmt).first()

        assert result is not None
        assert result.activity == sample_touchpoint.activity
        assert result.message_id == sample_touchpoint.message_id


class TestCreateAndSaveTouchpoint:
    """Test create_and_save_touchpoint method."""

    @pytest.mark.asyncio
    async def test_create_and_save_touchpoint(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test creating and saving a touchpoint in one call."""
        result = await classifier_service.create_and_save_touchpoint(
            sample_message, "Usuário", touchpoint_list
        )

        assert result.id is not None
        assert result.activity == "SALDO_CONSULTA"
        assert result.message_id == sample_message.id

    @pytest.mark.asyncio
    async def test_create_and_save_returns_saved_touchpoint(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test that returned touchpoint is the saved instance."""
        result = await classifier_service.create_and_save_touchpoint(
            sample_message, "Usuário", touchpoint_list
        )

        stmt = select(Touchpoint).where(Touchpoint.id == result.id)
        db_result = classifier_service.storage.exec(stmt).first()

        assert db_result is not None
        assert db_result.id == result.id
        assert db_result.activity == result.activity

    @pytest.mark.asyncio
    async def test_create_and_save_multiple_touchpoints(
        self, classifier_service, sample_conversation, touchpoint_list
    ):
        """Test creating and saving multiple touchpoints."""
        # Create messages for the same conversation
        from bancobot.models import MessageType

        messages = []
        for i in range(3):
            msg_type = MessageType.Human if i % 2 == 0 else MessageType.AI
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=sample_conversation.id,
                content=f"Message {i}",
                type=msg_type,
                timing_metadata={
                    "simulated_timestamp": dt.datetime.now().timestamp(),
                    "pause_time": 0,
                    "typing_time": 0,
                    "thinking_time": 0,
                },
                created_at=dt.datetime.now(),
            )
            messages.append(msg)
            classifier_service.save_message(msg)

        # Create touchpoints for each message
        touchpoints = []
        for msg in messages:
            tp = await classifier_service.create_and_save_touchpoint(
                msg, "Usuário", touchpoint_list
            )
            touchpoints.append(tp)

        # Verify all touchpoints were saved
        assert len(touchpoints) == 3
        for tp in touchpoints:
            assert tp.id is not None
