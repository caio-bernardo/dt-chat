# Classifier Tests - Quick Start

## Run All Tests
```bash
uv run --package classifier pytest apps/classifier/tests -v
```

## Common Commands

| Command | Description |
|---------|-------------|
| `pytest apps/classifier/tests -v` | Verbose output |
| `pytest apps/classifier/tests -q` | Quiet output |
| `pytest apps/classifier/tests/test_models.py` | Single module |
| `pytest apps/classifier/tests -k test_classify` | Match by name |
| `pytest apps/classifier/tests --cov=classifier` | Coverage report |
| `pytest apps/classifier/tests -vv` | Extra verbose |

## Expected Results

- **47 tests passing**
- **~0.34 seconds total**
- **2 deprecation warnings** (from bancobot, not tests)

## Test Files

1. **test_models.py** - Data models and enums (13 tests)
2. **test_agent.py** - Classification agent (8 tests)
3. **test_services.py** - Business logic (12 tests)
4. **test_exporter.py** - CSV export (13 tests)
5. **test_database.py** - Database setup (8 tests)

## Fixtures Available

- `db_engine` - In-memory SQLite
- `db_session` - Database session
- `mock_agent` - Mocked classifier agent
- `sample_message` - Example Message
- `sample_touchpoint` - Example Touchpoint
- `classifier_service` - Configured service
- `touchpoint_list` - Categories

## Debugging

```bash
# Stop on first failure
pytest apps/classifier/tests -x

# Drop into debugger
pytest apps/classifier/tests --pdb

# Show print statements
pytest apps/classifier/tests -s

# Full traceback
pytest apps/classifier/tests -vv --tb=long
```
