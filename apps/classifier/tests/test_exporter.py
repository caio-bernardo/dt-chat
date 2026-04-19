import datetime as dt
import uuid
from io import StringIO

from classifier.exporter import TouchpointExporter
from classifier.models import ActorType, Touchpoint


class TestTouchpointExporterInit:
    """Test TouchpointExporter initialization."""

    def test_exporter_initialization(self, db_session):
        """Test exporter initialization with session."""
        exporter = TouchpointExporter(db_session)
        assert exporter is not None
        assert exporter.storage == db_session


class TestExportCsvStr:
    """Test CSV export functionality."""

    def test_export_empty_touchpoints(self, db_session):
        """Test exporting when no touchpoints exist."""
        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        assert isinstance(result, StringIO)
        content = result.getvalue()
        lines = content.strip().split("\n")
        assert len(lines) == 1  # Only headers
        assert "event_id" in lines[0]

    def test_export_single_touchpoint(self, db_session, sample_touchpoint):
        """Test exporting a single touchpoint."""
        db_session.add(sample_touchpoint)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Header + START + 1 touchpoint + END
        assert len(lines) == 4
        assert "START-DIALOGUE-SYSTEM" in content

    def test_export_csv_headers(self, db_session, sample_touchpoint):
        """Test that CSV has correct headers."""
        db_session.add(sample_touchpoint)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        headers = content.split("\n")[0]
        assert "event_id" in headers
        assert "case_id" in headers
        assert "internal_id" in headers
        assert "actor" in headers
        assert "activity" in headers
        assert "timestamp" in headers

    def test_export_multiple_touchpoints_same_session(self, db_session, sample_message):
        """Test exporting multiple touchpoints in same session."""
        session_id = sample_message.conversation_id
        now = dt.datetime.now()

        for i in range(3):
            tp = Touchpoint(
                session_id=session_id,
                internal_id=i,
                actor=ActorType.HUMAN if i % 2 == 0 else ActorType.AI,
                message_id=i,
                message=f"Message {i}",
                timestamp=now + dt.timedelta(seconds=i),
                activity="TEST_ACTIVITY",
            )
            db_session.add(tp)

        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Header + START + 3 touchpoints + END
        assert len(lines) == 6

    def test_export_multiple_sessions(self, db_session):
        """Test exporting touchpoints from multiple sessions."""
        now = dt.datetime.now()

        for session_num in range(2):
            session_id = uuid.uuid4()
            for msg_num in range(2):
                tp = Touchpoint(
                    session_id=session_id,
                    internal_id=msg_num,
                    actor=ActorType.HUMAN,
                    message_id=msg_num,
                    message=f"Message {msg_num}",
                    timestamp=now + dt.timedelta(seconds=msg_num),
                    activity="TEST",
                )
                db_session.add(tp)

        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Header + (START + 2 touchpoints + END) * 2 sessions = 1 + (4 * 2) = 9
        assert len(lines) == 9

    def test_export_includes_start_marker(self, db_session, sample_touchpoint):
        """Test that export includes START marker for each session."""
        db_session.add(sample_touchpoint)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "START-DIALOGUE-SYSTEM" in content

    def test_export_includes_end_marker(self, db_session, sample_touchpoint):
        """Test that export includes END marker for each session."""
        db_session.add(sample_touchpoint)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "END - DIALOGUE - SYSTEM" in content

    def test_export_preserves_actor_type(self, db_session, sample_message):
        """Test that actor type is preserved in export."""
        session_id = sample_message.conversation_id

        tp_human = Touchpoint(
            session_id=session_id,
            internal_id=1,
            actor=ActorType.HUMAN,
            message_id=1,
            message="Human message",
            timestamp=dt.datetime.now(),
            activity="TEST",
        )
        tp_ai = Touchpoint(
            session_id=session_id,
            internal_id=2,
            actor=ActorType.AI,
            message_id=2,
            message="AI message",
            timestamp=dt.datetime.now(),
            activity="TEST",
        )

        db_session.add(tp_human)
        db_session.add(tp_ai)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "Human" in content
        assert "AI" in content

    def test_export_preserves_activity(self, db_session, sample_message):
        """Test that activity is preserved in export."""
        session_id = sample_message.conversation_id

        tp = Touchpoint(
            session_id=session_id,
            internal_id=1,
            actor=ActorType.HUMAN,
            message_id=1,
            message="Test",
            timestamp=dt.datetime.now(),
            activity="SALDO_CONSULTA",
        )

        db_session.add(tp)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        assert "SALDO_CONSULTA" in content

    def test_export_timestamp_in_isoformat(self, db_session, sample_touchpoint):
        """Test that timestamps are exported in ISO format."""
        db_session.add(sample_touchpoint)
        db_session.commit()

        exporter = TouchpointExporter(db_session)
        result = exporter.export_csv_str()

        content = result.getvalue()
        lines = content.strip().split("\n")
        # Check last line before END contains timestamp
        data_lines = [
            line for line in lines if "DIALOGUE" not in line and "event_id" not in line
        ]
        assert len(data_lines) > 0
        # Timestamp should contain 'T' for ISO format
        last_data_line = data_lines[-1]
        assert "T" in last_data_line
