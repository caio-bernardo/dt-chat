# Classifier Test Suite

Comprehensive unit tests for the Classifier application.

## Overview

- **Total Tests**: 50+
- **Test Modules**: 5
- **Execution Time**: ~1 second
- **Framework**: pytest with pytest-asyncio

## Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `test_models.py` | 13 | Models and enums |
| `test_agent.py` | 10 | Agent classification |
| `test_services.py` | 12 | Business logic |
| `test_exporter.py` | 13 | CSV export |
| `test_database.py` | 8 | Database setup |

## Running Tests

```bash
# All tests
uv run --package classifier pytest apps/classifier/tests -v

# Specific module
uv run --package classifier pytest apps/classifier/tests/test_models.py -v

# With coverage
uv run --package classifier pytest apps/classifier/tests --cov=classifier
```

## Key Features

✅ In-memory SQLite for isolation  
✅ Async/await support  
✅ Mocked LLM calls  
✅ Fast execution (<1 second)  
✅ Comprehensive coverage  

## Fixtures (conftest.py)

- `db_engine` - In-memory SQLite
- `db_session` - Database session per test
- `mock_agent` - Mocked ClassifierAgent
- `sample_message` - Sample Message from bancobot
- `sample_touchpoint` - Sample Touchpoint
- `classifier_service` - Configured service for tests
- `touchpoint_list` - Available touchpoint categories

## Test Coverage

- Model creation and validation
- Message to ActorType conversion
- Agent initialization and classification
- Touchpoint creation and persistence
- CSV export with multiple sessions
- Database schema and session management
