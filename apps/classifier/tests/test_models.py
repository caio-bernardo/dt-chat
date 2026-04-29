import datetime as dt

from classifier.models import Touchpoint


class TestTouchpoint:
    """Test Touchpoint model."""

    def test_touchpoint_creation(self, sample_message):
        """Test creating a touchpoint with a message."""
        tp = Touchpoint(
            message_id=sample_message.id,
            message=sample_message,
            activity="SALDO_CONSULTA",
        )
        assert tp.message_id == sample_message.id
        assert tp.message == sample_message
        assert tp.activity == "SALDO_CONSULTA"
        assert tp.created_at is not None

    def test_touchpoint_with_custom_created_at(self, sample_message):
        """Test touchpoint with custom created_at timestamp."""
        custom_time = dt.datetime(2024, 1, 15, 10, 30, 0)
        tp = Touchpoint(
            message_id=sample_message.id,
            message=sample_message,
            activity="TRANSFERENCIA",
            created_at=custom_time,
        )
        assert tp.created_at == custom_time

    def test_touchpoint_default_created_at(self, sample_message):
        """Test that created_at defaults to current time."""
        before = dt.datetime.now()
        tp = Touchpoint(
            message_id=sample_message.id,
            message=sample_message,
            activity="TEST",
        )
        after = dt.datetime.now()

        assert before <= tp.created_at <= after

    def test_touchpoint_different_activities(self, sample_message):
        """Test touchpoint with different activity values."""
        activities = ["SALDO_CONSULTA", "TRANSFERENCIA", "PAGAMENTO_BOLETO"]
        for activity in activities:
            tp = Touchpoint(
                message_id=sample_message.id,
                message=sample_message,
                activity=activity,
            )
            assert tp.activity == activity

    def test_touchpoint_fields_required(self, sample_message):
        """Test that required fields are properly set."""
        tp = Touchpoint(
            message_id=sample_message.id,
            message=sample_message,
            activity="TEST_ACTIVITY",
        )
        assert tp.message_id is not None
        assert tp.message is not None
        assert tp.activity is not None
        assert tp.created_at is not None
