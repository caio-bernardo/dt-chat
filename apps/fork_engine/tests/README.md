# Fork Engine Test Suite

Comprehensive unit tests for the Fork Engine application, which creates Digital Twins of conversation agents and users from message streams.

## Overview

The Fork Engine test suite covers:
- **ForkEngine initialization and condition management** (`test_engine.py`)
- **Helper utilities for agent builders and message senders** (`test_helpers.py`)
- **Async fork spawning and execution** 
- **Message format conversion and metadata retrieval**

**Total Tests:** 29 test cases
**Framework:** pytest with pytest-asyncio
**Async Support:** Full async/await testing with `asyncio_mode = "auto"`

## Test Structure

### conftest.py
Shared pytest fixtures for all tests:
- `db_engine` - In-memory SQLite database
- `db_session` - Database session for tests
- `mock_queue` / `mock_queue_prod` - Mock pub/sub queue interfaces
- `mock_bancobot_agent` / `mock_bancobot_builder` - Mocked BancoBot components
- `mock_userbot_builder` - Mocked UserBot builder
- `fork_engine` - ForkEngine instance with mocks
- `fork_config` - Sample ForkConfig for testing
- `touchpoint` - Sample Touchpoint event

### test_engine.py (13 tests)
Tests for the ForkEngine class and condition system:

**TestForkEngineInit:**
- `test_init` - Verifies ForkEngine initializes with queue and producer

**TestConditionManagement:**
- `test_create_condition` - Single condition registration
- `test_create_multiple_conditions` - Multiple condition callbacks
- `test_condition_callback_invocation` - Callback execution with touchpoint

**TestForkExecution:**
- `test_fork_builds_agents` - Verifies both builders are called
- `test_fork_runs_userbot` - Async fork spawning with correct parameters
- `test_fork_config_with_defaults` - Default TimeSimulationConfig validation

**TestWatcherBasics:**
- `test_watch_exception_handling` - Watcher method availability
- `test_fork_method_exists` - Fork method callable

### test_helpers.py (16 tests)
Tests for utility functions and BancobotProcedureCallSender:

**TestMessageMapping:**
- `test_map_human_message` - Convert Human messages
- `test_map_ai_message` - Convert AI messages

**TestMetadataRetrieval:**
- `test_retrieve_timesim_from_valid_metadata` - Extract TimeSimulationConfig
- `test_retrieve_timesim_missing_key` - Error handling for missing data
- `test_retrieve_persona_from_metadata` - Extract persona string
- `test_retrieve_persona_missing_key` - Error handling for missing persona

**TestBancobotProcedureCallSender:**
- `test_init` - Initialization and conversation_id setup
- `test_service_source_set` - Service source is "twin_bancobot"
- `test_create_channel` - Async channel creation with metadata
- `test_create_channel_no_data` - Channel creation without data
- `test_send_message_without_channel` - Error if message sent before channel
- `test_send_message_success` - Successful message sending and response

## Running Tests

### Run all Fork Engine tests:
```bash
uv run --package fork_engine pytest apps/fork_engine/tests -v
```

### Run specific test file:
```bash
uv run --package fork_engine pytest apps/fork_engine/tests/test_engine.py -v
```

### Run specific test class:
```bash
uv run --package fork_engine pytest apps/fork_engine/tests/test_engine.py::TestConditionManagement -v
```

### Run with coverage:
```bash
uv run --package fork_engine pytest apps/fork_engine/tests --cov=fork_engine --cov-report=term-missing
```

## Key Design Patterns

### 1. Mocking External Dependencies
- Queue subscribers and publishers mocked to avoid Redis connections
- BancoBot and UserBot builders mocked to control behavior
- Agents and services mocked to prevent LLM calls

### 2. In-Memory Database
- SQLite with StaticPool for isolated test runs
- No shared state between tests
- Full table schema created fresh for each test

### 3. Async Testing
- pytest-asyncio enables `@pytest.mark.asyncio` decorator
- AsyncMock for mocking async methods
- Fixtures support both sync and async tests

### 4. Reusable Fixtures
- Fixtures in `conftest.py` shared across all test files
- Clear fixture naming for readability
- Parameterizable fixtures for different scenarios

## Test Coverage

| Module | Coverage | Key Tests |
|--------|----------|-----------|
| `engine.py` | Initialization, conditions, fork spawning | 13 tests |
| `helpers.py` | Message mapping, sender, metadata | 16 tests |

## Dependencies

Test dependencies are specified in `pyproject.toml`:
- `pytest>=9.0.3` - Test framework
- `pytest-asyncio>=0.23.0` - Async support

## Maintenance Notes

1. **Adding new tests**: Use existing fixtures from `conftest.py`; avoid creating duplicate fixtures.
2. **Async operations**: Always use `@pytest.mark.asyncio` for async test functions.
3. **Mocking best practices**: Mock pub/sub and external services; test real logic locally.
4. **Database tests**: Use `db_session` fixture for any DB operations.

## Next Steps (Optional)

- Add property-based tests with Hypothesis for edge cases
- Add performance benchmarks for fork execution
- Add E2E integration tests with real message flows (using mock agents)
- Monitor test execution time and optimize slow tests
