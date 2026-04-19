import os
from unittest.mock import patch

from sqlmodel import create_engine


class TestDatabaseInitialization:
    """Test database module initialization."""

    def test_engine_creation(self):
        """Test that database engine is created."""
        with patch.dict(os.environ, {"DB_URL": "sqlite:///test.db"}):
            from bancobot.database import engine

            assert engine is not None

    def test_create_db_and_tables(self):
        """Test creating database tables."""
        # Create an in-memory SQLite engine for testing
        test_engine = create_engine("sqlite:///:memory:")

        with patch("bancobot.database.engine", test_engine):
            from bancobot.database import create_db_and_tables

            create_db_and_tables()

            # Verify tables were created by checking inspector
            from sqlalchemy import inspect

            inspector = inspect(test_engine)
            tables = inspector.get_table_names()

            # Should have conversation and message tables
            assert "conversation" in tables
            assert "message" in tables

    def test_create_db_and_tables_idempotent(self):
        """Test that create_db_and_tables can be called multiple times safely."""
        test_engine = create_engine("sqlite:///:memory:")

        with patch("bancobot.database.engine", test_engine):
            from bancobot.database import create_db_and_tables

            # Should not raise error when called twice
            create_db_and_tables()
            create_db_and_tables()


class TestRedisClient:
    """Test Redis client initialization."""

    def test_redis_client_initialization(self):
        """Test that Redis client is initialized."""
        # Import the module to ensure redis_client is created
        from bancobot import database

        assert hasattr(database, "redis_client")

    def test_redis_client_is_initialized(self):
        """Test Redis client is available in the module."""
        from bancobot.database import redis_client

        assert redis_client is not None
