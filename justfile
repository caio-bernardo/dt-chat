set dotenv-load

### Bancobot ###

# Runs Bancobot webserver
bancobot:
    uv run --package bancobot bancobot

# Watch for changes (run bancobot on dev mode)
watch-bancobot:
    uv run --package bancobot fastapi dev apps/bancobot

# Run Bancobot tests
bancobot-test:
    uv run --package bancobot pytest apps/bancobot/tests

# Run bancobot tests with coverage
bancobot-test-cov:
    uv run --package bancobot pytest apps/bancobot/tests --cov=bancobot --cov-report=term-missing

### Classifier ###

# Run Classifier app
classifier AI_TP="data/touchpoints/Touchpoint_ai.json" HUMAN_TP="data/touchpoints/Touchpoint_human.json": redis-up
    uv run --package classifier classifier run --stream {{ AI_TP }} {{ HUMAN_TP }}

# Run Classifier tests
classifier-test:
    uv run --package classifier pytest apps/classifier/tests

# Run Classifier tests with coverage
classifer-test-cov:
    uv run --package classifier pytest apps/classifier/tests --cov=classifier --cov-report=term-missing

# Run Classifier export function
exporter:
    uv run --package classifier classifier export

### Fork Engine ###

# Run Fork Engine
forker:
    uv run --package fork-engine fork-engine

# Run Fork Engine tests
forker-test:
    uv run --package fork-engine pytest apps/fork_engine/tests

# Run Fork Engine tests with coverage
forker-test-cov:
    uv run --package fork-engine pytest apps/fork-engine/tests --cov=fork-engine --cov-report=term-missing

### Redis Cache ###

# Starts Redis Container
redis-up:
    docker compose up redis -d
    @echo Redis image up on port: $REDIS_PORT

# Drops Redis Container
redis-down:
    docker compose down redis
    @echo Redis image down

# Iterates over a directory importing each json file to conversations database, also publish them to classification
import-dir DIR:
    #!/usr/bin/env sh
    set -e
    for file in {{ DIR }}/*.json; do
        echo Processing $file
        scripts/importer.py $file --quiet --publish --redis-queue-key=$MSG_CHANNEL --redis-url=redis://localhost:$REDIS_PORT
        echo Finished $file
    done
