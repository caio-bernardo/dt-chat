import datetime as dt
import uuid

import pytest
from sqlmodel import select

from classifier.models import ActorType, Touchpoint


class TestGetLastInternalId:
    """Test _get_last_internal_id method."""

    def test_get_last_internal_id_empty_session(self, classifier_service):
        """Test getting internal ID when no touchpoints exist."""
        session_id = uuid.uuid4()
        result = classifier_service._get_last_internal_id(session_id)
        assert result == 0

    def test_get_last_internal_id_with_touchpoints(
        self, classifier_service, sample_touchpoint
    ):
        """Test getting internal ID with existing touchpoints."""
        classifier_service.storage.add(sample_touchpoint)
        classifier_service.storage.commit()

        result = classifier_service._get_last_internal_id(sample_touchpoint.session_id)
        assert result == 1

    def test_get_last_internal_id_multiple_touchpoints(
        self, classifier_service, sample_message
    ):
        """Test getting internal ID with multiple touchpoints."""
        session_id = sample_message.conversation_id

        for i in range(3):
            tp = Touchpoint(
                session_id=session_id,
                internal_id=i,
                actor=ActorType.HUMAN,
                message_id=i,
                message=f"Message {i}",
                timestamp=dt.datetime.now(),
                activity="TEST",
            )
            classifier_service.storage.add(tp)

        classifier_service.storage.commit()
        result = classifier_service._get_last_internal_id(session_id)
        assert result == 3


class TestCreateTouchpoint:
    """Test create_touchpoint method."""

    @pytest.mark.asyncio
    async def test_create_touchpoint_with_timing_metadata(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test creating a touchpoint from a message with timing metadata."""
        result = await classifier_service.create_touchpoint(
            sample_message, "Human", touchpoint_list
        )

        assert result.session_id == sample_message.conversation_id
        assert result.internal_id == 1
        assert result.actor == ActorType.HUMAN
        assert result.message_id == sample_message.id
        assert result.message == sample_message.content
        assert result.activity == "SALDO_CONSULTA"

    @pytest.mark.asyncio
    async def test_create_touchpoint_increments_id(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test that internal_id increments correctly."""
        tp1 = Touchpoint(
            session_id=sample_message.conversation_id,
            internal_id=1,
            actor=ActorType.HUMAN,
            message_id=1,
            message="First",
            timestamp=dt.datetime.now(),
            activity="TEST",
        )
        classifier_service.storage.add(tp1)
        classifier_service.storage.commit()

        result = await classifier_service.create_touchpoint(
            sample_message, "Human", touchpoint_list
        )

        assert result.internal_id == 2

    @pytest.mark.asyncio
    async def test_create_touchpoint_calls_agent(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test that create_touchpoint calls the agent."""
        await classifier_service.create_touchpoint(
            sample_message, "Human", touchpoint_list
        )

        classifier_service.agent.classify.assert_called_once_with(
            sample_message.content, "Human", touchpoint_list
        )


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


class TestCreateAndSaveTouchpoint:
    """Test create_and_save_touchpoint method."""

    @pytest.mark.asyncio
    async def test_create_and_save_touchpoint(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test creating and saving a touchpoint in one call."""
        result = await classifier_service.create_and_save_touchpoint(
            sample_message, "Human", touchpoint_list
        )

        assert result.id is not None
        assert result.activity == "SALDO_CONSULTA"
        assert result.session_id == sample_message.conversation_id

    @pytest.mark.asyncio
    async def test_create_and_save_returns_saved_touchpoint(
        self, classifier_service, sample_message, touchpoint_list
    ):
        """Test that returned touchpoint is the saved instance."""
        result = await classifier_service.create_and_save_touchpoint(
            sample_message, "Human", touchpoint_list
        )

        stmt = select(Touchpoint).where(Touchpoint.id == result.id)
        db_result = classifier_service.storage.exec(stmt).first()

        assert db_result is not None
        assert db_result.id == result.id
