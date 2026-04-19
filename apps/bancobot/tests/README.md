# BancoBot Test Suite

This directory contains comprehensive unit tests for the BancoBot application.

## Overview

The test suite is organized by module and uses **pytest** with the following testing patterns:
- Unit tests for models, services, and utilities
- Async test support with `pytest-asyncio`
- Fixtures for database and service mocking
- In-memory SQLite for database tests

## Project Structure

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── test_models.py        # Tests for data models
├── test_services.py      # Tests for business logic services
├── test_agent.py         # Tests for the BancoAgent and builder
├── test_database.py      # Tests for database initialization
└── README.md            # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_models.py
```

### Run specific test class
```bash
pytest tests/test_services.py::TestCreateSession
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage
```bash
pytest --cov=bancobot
```

### Run async tests
```bash
pytest -v -m asyncio
```

## Test Modules

### test_models.py
Tests for SQLModel data models:
- `MessageType` enum validation
- `Conversation` creation and relationships
- `ConversationCreate` validation
- `Message` creation with timing metadata
- Public view models (`ConversationPublic`, `MessagePublic`, etc.)

### test_services.py
Tests for `BancoBotService` business logic:
- Session (conversation) CRUD operations
- Message saving and publishing
- Agent message answering workflow
- Error handling and HTTP exceptions
- Message retrieval with filtering and limits

### test_agent.py
Tests for agent initialization and tool creation:
- `BancoAgent` initialization with custom parameters
- `BancoAgentBuilder` pattern implementation
- `make_search_documentation_tool` function
- System prompt configuration

### test_database.py
Tests for database initialization:
- Engine creation
- Table creation and validation
- Redis client initialization
- Idempotent database setup

## Key Fixtures (conftest.py)

- `db_engine`: In-memory SQLite database
- `db_session`: Database session for tests
- `mock_agent`: Mocked BancoAgent
- `mock_publisher`: Mocked message publisher
- `conversation`: Sample conversation instance
- `bancobot_service`: Configured BancoBotService for testing
- `timing_metadata`: Sample timing metadata dictionary

## Dependencies

Tests require these additional packages:
- `pytest>=7.0.0`
- `pytest-asyncio`
- `sqlmodel`

These should be installed in your development environment.

## Test Coverage

The test suite focuses on critical functionality:
- **Models**: All model creation and validation
- **Services**: CRUD operations, message handling, publishing
- **Agent**: Initialization and configuration
- **Database**: Schema creation and connections

## Notes

- Database tests use in-memory SQLite for isolation and speed
- Service tests use mock agents and publishers to avoid external dependencies
- Async tests are marked with `@pytest.mark.asyncio`
- HTTP exception handling is tested with `pytest.raises(HTTPException)`
