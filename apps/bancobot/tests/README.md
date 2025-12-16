# BancoBot Tests

This directory contains comprehensive tests for the BancoBot application, including unit tests, integration tests, and end-to-end tests.

## Test Structure

```
test/
├── conftest.py                 # Pytest fixtures and test configuration
├── pytest.ini                 # Pytest configuration
├── requirements-test.txt       # Test dependencies
├── README.md                   # This file
└── bancobot/
    ├── __init__.py
    ├── test_models.py          # Tests for database models
    ├── test_services.py        # Tests for service layer
    ├── test_routes.py          # Tests for API routes
    ├── test_agent.py           # Tests for AI agent functionality
    └── test_integration.py     # Integration tests
```

## Test Categories

### Unit Tests
- **test_models.py**: Tests for SQLModel database models (Message, MessageCreate, MessageType)
- **test_services.py**: Tests for the BancoBotService class with mocked dependencies
- **test_routes.py**: Tests for FastAPI route endpoints with mocked services
- **test_agent.py**: Tests for the BancoAgent class with mocked AI components

### Integration Tests
- **test_integration.py**: End-to-end tests that test the complete application flow

## Setup

## 1. Install all test Dependencies

```bash
uv sync
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Tests with Coverage
```bash
pytest --cov=bancobot --cov-report=html --cov-report=term
```

### Run Specific Test Categories

#### Unit Tests Only
```bash
pytest test/bancobot/test_models.py test/bancobot/test_services.py test/bancobot/test_routes.py test/bancobot/test_agent.py
```

#### Integration Tests Only
```bash
pytest test/bancobot/test_integration.py
```

#### Async Tests Only
```bash
pytest -m asyncio
```

### Run Tests with Different Verbosity
```bash
# Quiet mode
pytest -q

# Verbose mode
pytest -v

# Very verbose mode
pytest -vv
```

### Run Specific Tests
```bash
# Run a specific test file
pytest test/bancobot/test_services.py

# Run a specific test class
pytest test/bancobot/test_services.py::TestBancoBotService

# Run a specific test method
pytest test/bancobot/test_services.py::TestBancoBotService::test_create_message_success
```

## Test Features

### Mocking Strategy
- **Database**: Uses in-memory SQLite databases for fast, isolated tests
- **AI Agent**: Mocks the BancoAgent to return predictable responses
- **External Dependencies**: All external services are mocked to ensure tests are deterministic

### Fixtures
The tests use pytest fixtures defined in `conftest.py`:

- `in_memory_engine`: Creates an in-memory SQLite database
- `db_session`: Provides a database session for tests
- `mock_agent`: Creates a mocked BancoAgent
- `banco_service`: Creates a BancoBotService with mocked dependencies
- `sample_session_id`: Generates sample UUIDs for testing
- `sample_message_create`: Creates sample MessageCreate objects
- `sample_messages`: Creates sample messages in the database
- `test_client`: FastAPI test client
- `mock_service_dependency`: Mocks service dependencies for route testing

### Test Data
Tests use realistic data that mimics actual usage:
- Portuguese banking terms and phrases
- Valid UUID formats for session IDs
- Proper message types and structures
- Edge cases like empty messages, very long content, special characters

## Test Coverage

The tests aim to cover:

1. **Model Layer**
   - Database model creation and validation
   - Enum functionality
   - Model serialization/deserialization

2. **Service Layer**
   - Message creation and AI response generation
   - Session management (create, read, delete)
   - Error handling and edge cases
   - Database transactions and rollbacks

3. **Route Layer**
   - All API endpoints
   - Request/response validation
   - Error handling and HTTP status codes
   - Dependency injection

4. **Agent Layer**
   - AI agent initialization and configuration
   - Message processing (sync and async)
   - Tool integration
   - Error handling

5. **Integration**
   - Complete conversation flows
   - Multi-session handling
   - Concurrent operations
   - Data persistence

## Best Practices

### Writing New Tests

1. **Follow the AAA Pattern**: Arrange, Act, Assert
2. **Use Descriptive Test Names**: Test names should clearly describe what is being tested
3. **Test One Thing at a Time**: Each test should focus on a single functionality
4. **Use Fixtures**: Leverage existing fixtures for common setup
5. **Mock External Dependencies**: Don't make real API calls or use real databases in unit tests

### Example Test Structure

```python
def test_create_message_success(self, banco_service, sample_message_create):
    """Test successful message creation with AI response"""
    # Arrange
    # (Setup is done via fixtures)
    
    # Act
    result = await banco_service.create_message(sample_message_create)
    
    # Assert
    assert isinstance(result, Message)
    assert result.type == MessageType.AI
    assert result.content == f"Mock AI response to: {sample_message_create.content}"
```

## Debugging Tests

### Running Tests in Debug Mode
```bash
pytest -s --pdb  # Drop into debugger on failures
```

### Viewing Test Output
```bash
pytest -s  # Show print statements and logs
```

### Testing with Different Log Levels
```bash
pytest --log-cli-level=DEBUG
```

## Continuous Integration

These tests are designed to run in CI environments. They:
- Don't require external services
- Use in-memory databases
- Have predictable, deterministic behavior
- Include proper cleanup

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure the main application is properly installed
2. **Database Errors**: Ensure SQLModel is properly configured
3. **Async Test Issues**: Make sure `pytest-asyncio` is installed and configured

### Getting Help

If tests fail:
1. Read the error message carefully
2. Check that all dependencies are installed
3. Verify environment variables are set correctly
4. Run tests with `-v` for more detailed output
5. Use `--pdb` to debug failing tests

## Contributing

When adding new features:
1. Write tests for new functionality
2. Update existing tests if behavior changes
3. Ensure all tests pass before submitting
4. Aim for high test coverage (>90%)
5. Follow existing test patterns and conventions
