from sqlalchemy import inspect
from sqlmodel import Session

from classifier.database import create_db_and_tables, get_session


class TestCreateDbAndTables:
    """Test database initialization."""

    def test_create_db_and_tables_returns_engine(self):
        """Test that function returns a database engine."""
        engine = create_db_and_tables("sqlite:///:memory:")
        assert engine is not None

    def test_create_db_and_tables_creates_touchpoint_table(self):
        """Test that Touchpoint table is created."""
        engine = create_db_and_tables("sqlite:///:memory:")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        assert "touchpoint" in tables

    def test_touchpoint_table_has_required_columns(self):
        """Test that Touchpoint table has required columns."""
        engine = create_db_and_tables("sqlite:///:memory:")
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("touchpoint")}

        assert "id" in columns
        assert "message_id" in columns
        assert "activity" in columns
        assert "created_at" in columns

    def test_touchpoint_table_has_message_relationship(self):
        """Test that Touchpoint table has foreign key to Message."""
        engine = create_db_and_tables("sqlite:///:memory:")
        inspector = inspect(engine)

        # Check foreign keys
        fks = inspector.get_foreign_keys("touchpoint")
        assert len(fks) > 0

        # Check that message_id is a foreign key to message.id
        message_fk = [fk for fk in fks if fk["constrained_columns"] == ["message_id"]]
        assert len(message_fk) > 0
        assert message_fk[0]["referred_table"] == "message"

    def test_create_db_and_tables_idempotent(self):
        """Test that creating tables multiple times is safe."""
        engine1 = create_db_and_tables("sqlite:///:memory:")
        engine2 = create_db_and_tables("sqlite:///:memory:")
        assert engine1 is not None
        assert engine2 is not None


class TestGetSession:
    """Test session management."""

    def test_get_session_yields_session(self):
        """Test that get_session yields a Session instance."""
        engine = create_db_and_tables("sqlite:///:memory:")
        session_gen = get_session(engine)
        session = next(session_gen)
        assert isinstance(session, Session)

    def test_get_session_yields_valid_session(self):
        """Test that yielded session is valid and usable."""
        engine = create_db_and_tables("sqlite:///:memory:")
        for session in get_session(engine):
            assert session is not None
            assert hasattr(session, "exec")
            break

    def test_get_session_is_generator(self):
        """Test that get_session returns a generator."""
        engine = create_db_and_tables("sqlite:///:memory:")
        session_gen = get_session(engine)
        assert hasattr(session_gen, "__iter__")
        assert hasattr(session_gen, "__next__")
