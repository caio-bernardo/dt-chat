# Touchpoint Classifier

The `classifier` package is a key observation module within the framework. It listens to raw conversational messages from Redis, parses their intent using an LLM, maps them to predefined system-agnostic labels called **touchpoints**, and stores them for further analysis or simulation triggering.

## Purpose

To evaluate chatbot interactions mathematically (e.g., using process mining), unstructured conversation transcripts must be mapped to structured event logs. This application reads raw dialogue strings in real-time, classifies both human and chatbot utterances according to a business-defined taxonomy, and broadcasts these events back to the framework.

## Key Features

1. **Real-time Event Streaming**: Subscribes to the raw message Redis queue (`msg_channel`) using the `pubsub` library.
2. **Context-Aware Classification**: Uses structured touchpoint definitions and descriptions (JSON configurations) along with LLM prompting to label messages accurately.
3. **Dual Storage & Re-Publishing**: Saves labeled touchpoints to an SQLite database (for analytical exports) and publishes them to a Redis stream (`tp_channel`) for downstream services (like the Fork Engine).
4. **Export Capabilities**: Includes a dedicated command-line interface to export processed databases into clean event logs.

## Package Structure

```
apps/classifier/
├── src/
│   └── classifier/
│       ├── __init__.py
│       ├── cli.py         # Typer CLI application structure
│       ├── database.py    # SQLModel database schemas & initializers
│       ├── models.py      # Data models for Touchpoints (both SQLite and Redis)
│       └── service.py     # Worker execution, LLM-based classification logic, & queue streams
├── tests/                 # Unit and validation tests for the classifier
├── pyproject.toml
└── README.md
```

## Touchpoint Definitions

The classification is split between AI agent touchpoints and Human client touchpoints. These are defined in JSON configurations:

* **AI Touchpoints (`data/touchpoints/Touchpoint_ai.json`)**: Identifies responses from the bot, such as greetings, account explanation, card offer, redirection, or technical issue.
* **Human Touchpoints (`data/touchpoints/Touchpoint_human.json`)**: Identifies requests from the customer, such as a greeting, request for card rules, card acquisition requests, human operator escalation, or transaction details.

If a message does not fit any configured categories, it is designated as `INVALID-TOUCHPOINT-SYSTEM`.

## CLI Usage

The classifier is exposed as a command-line utility via `just` or `uv run`.

### 1. Run the Classifier Worker
Start listening for Redis events and classifying messages:
```sh
uv run --package classifier classifier run data/touchpoints/Touchpoint_ai.json data/touchpoints/Touchpoint_human.json
```
* **Options**:
  * `--stream-name TEXT`: Redis stream to subscribe to (defaults to environment `MSG_CHANNEL` or `msg_channel`).
  * `--db-path TEXT`: Target database URL to save touchpoints (defaults to environment `TOUCHPOINT_DATABASE_URL` or `sqlite:///db/touchpoints.db`).
  * `--max-in-flight INTEGER`: Maximum number of parallel workers processing messages (defaults to `16`).

### 2. Export Database to CSV
Export classified touchpoints to a standard CSV for process mining or analytical ingestion:
```sh
uv run --package classifier classifier export --file-output output.csv --db-path sqlite:///db/touchpoints.db
```

For comprehensive orchestration details, refer to the [USAGE Guide](USAGE.md).
