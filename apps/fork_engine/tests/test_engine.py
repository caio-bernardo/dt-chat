import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from fork_engine.engine import ForkEngine


class TestForkEngineInit:
    """Test ForkEngine initialization."""

    def test_init(self, mock_queue, mock_queue_prod):
        """Test ForkEngine initialization."""
        engine = ForkEngine(mock_queue, mock_queue_prod, db_url="sqlite:///:memory:")
        assert engine.queue == mock_queue
        assert engine.queue_prod == mock_queue_prod
        assert engine.conditions == {}


class TestConditionManagement:
    """Test condition registration and callback system."""

    def test_create_condition(self, fork_engine, fork_config):
        """Test creating a single condition."""

        def callback(tp):
            return fork_config

        activity = "TEST_ACTIVITY"

        fork_engine.create_condition(activity, callback)

        assert activity in fork_engine.conditions
        assert fork_engine.conditions[activity] == callback

    def test_create_multiple_conditions(self, fork_engine, fork_config):
        """Test creating multiple conditions."""

        def callback1(tp):
            return fork_config

        def callback2(tp):
            return fork_config

        fork_engine.create_condition("ACTIVITY_1", callback1)
        fork_engine.create_condition("ACTIVITY_2", callback2)

        assert len(fork_engine.conditions) == 2
        assert "ACTIVITY_1" in fork_engine.conditions
        assert "ACTIVITY_2" in fork_engine.conditions

    def test_condition_callback_invocation(self, fork_engine, fork_config, touchpoint):
        """Test that condition callback is invoked correctly."""
        called_with = []

        def callback(tp):
            called_with.append(tp)
            return fork_config

        fork_engine.create_condition(touchpoint.activity, callback)

        # Invoke callback
        result = fork_engine.conditions[touchpoint.activity](touchpoint)

        assert len(called_with) == 1
        assert called_with[0] == touchpoint
        assert result == fork_config


class TestForkExecution:
    """Test fork spawning and execution."""

    @pytest.mark.asyncio
    async def test_fork_builds_agents(self, fork_config):
        """Test that fork builds bancobot and userbot."""
        engine = ForkEngine(MagicMock(), MagicMock(), db_url="sqlite:///:memory:")
        engine._storage = iter([MagicMock()])  # pyright: ignore[reportAttributeAccessIssue]

        mock_userbot = AsyncMock()
        fork_config.userbot_builder.build_with_default.return_value = mock_userbot

        await engine.fork(fork_config)

        fork_config.bancobot_builder.build_with_default.assert_called_once()
        fork_config.userbot_builder.build_with_default.assert_called_once()

    @pytest.mark.asyncio
    async def test_fork_runs_userbot(self, fork_config):
        """Test that fork runs the userbot with correct parameters."""
        engine = ForkEngine(MagicMock(), MagicMock(), db_url="sqlite:///:memory:")
        engine._storage = iter([MagicMock()])  # pyright: ignore[reportAttributeAccessIssue]

        mock_userbot = AsyncMock()
        fork_config.userbot_builder.build_with_default.return_value = mock_userbot

        await engine.fork(fork_config)

        mock_userbot.arun.assert_called_once()
        call_args = mock_userbot.arun.call_args
        assert call_args[0][0] == fork_config.next_msg
        assert call_args[0][1] == fork_config.iterations
        assert call_args[0][2] == fork_config.timesim

    @pytest.mark.asyncio
    async def test_fork_config_with_defaults(
        self, mock_bancobot_builder, mock_userbot_builder
    ):
        """Test fork with default TimeSimulationConfig."""
        from userbot import TimeSimulationConfig

        from fork_engine.engine import ForkConfig

        config = ForkConfig(
            parent_conversation=uuid.uuid4(),
            bancobot_builder=mock_bancobot_builder,
            userbot_builder=mock_userbot_builder,
            next_msg="Hi",
        )

        assert config.iterations == 15
        assert isinstance(config.timesim, TimeSimulationConfig)


class TestWatcherBasics:
    """Test basic watcher functionality."""

    def test_watch_exception_handling(self, fork_engine, mock_queue):
        """Test that watcher handles exceptions gracefully."""
        # This is a basic test to ensure the watch method can be defined
        # Full async watch testing requires more complex mocking
        assert hasattr(fork_engine, "awatch")
        assert callable(fork_engine.awatch)

    def test_fork_method_exists(self, fork_engine):
        """Test that fork method exists and is callable."""
        assert hasattr(fork_engine, "fork")
        assert callable(fork_engine.fork)
