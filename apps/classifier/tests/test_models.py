import datetime as dt
import uuid

import pytest
from bancobot.models import MessageType

from classifier.models import ActorType, Touchpoint, from_message_type


class TestActorType:
    """Test ActorType enum."""

    def test_actor_type_system(self):
        assert ActorType.SYSTEM == "System"

    def test_actor_type_ai(self):
        assert ActorType.AI == "AI"

    def test_actor_type_human(self):
        assert ActorType.HUMAN == "Human"

    def test_actor_type_count(self):
        assert len(ActorType) == 3


class TestFromMessageType:
    """Test from_message_type conversion function."""

    def test_convert_human_message_type(self):
        result = from_message_type(MessageType.Human)
        assert result == ActorType.HUMAN

    def test_convert_ai_message_type(self):
        result = from_message_type(MessageType.AI)
        assert result == ActorType.AI

    def test_invalid_message_type_raises_error(self):
        with pytest.raises(ValueError):
            from_message_type("invalid_type")  # pyright: ignore[reportArgumentType]


class TestTouchpoint:
    """Test Touchpoint model."""

    def test_touchpoint_creation(self):
        session_id = uuid.uuid4()
        tp = Touchpoint(
            session_id=session_id,
            internal_id=1,
            actor=ActorType.HUMAN,
            message_id=1,
            message="Test message",
            timestamp=dt.datetime.now(),
            activity="SALDO_CONSULTA",
        )
        assert tp.session_id == session_id
        assert tp.internal_id == 1
        assert tp.actor == ActorType.HUMAN
        assert tp.message_id == 1
        assert tp.created_at is not None

    def test_touchpoint_defaults(self):
        tp = Touchpoint(
            session_id=uuid.uuid4(),
            internal_id=1,
            message_id=1,
            message="Test",
            timestamp=dt.datetime.now(),
            activity="TEST",
        )
        assert tp.actor == ActorType.SYSTEM
        assert isinstance(tp.created_at, dt.datetime)

    def test_touchpoint_with_different_actors(self):
        session_id = uuid.uuid4()
        for actor in [ActorType.HUMAN, ActorType.AI, ActorType.SYSTEM]:
            tp = Touchpoint(
                session_id=session_id,
                internal_id=1,
                actor=actor,
                message_id=1,
                message="Test",
                timestamp=dt.datetime.now(),
                activity="TEST",
            )
            assert tp.actor == actor

    def test_touchpoint_fields_not_null(self):
        tp = Touchpoint(
            session_id=uuid.uuid4(),
            internal_id=5,
            actor=ActorType.AI,
            message_id=42,
            message="Important message",
            timestamp=dt.datetime.now(),
            activity="TRANSFERENCIA",
        )
        assert tp.session_id is not None
        assert tp.internal_id == 5
        assert tp.message_id == 42
        assert tp.message == "Important message"
        assert tp.activity == "TRANSFERENCIA"
