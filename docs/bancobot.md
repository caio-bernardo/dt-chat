# Bancobot

Banco Bot is a conversational agent package specialized in assisting clients of the fictional 'Bank X'. Built with FastAPI and LangChain, it serves as the primary system-under-test and conversation generator for this Digital Twin framework.

## Purpose

The package is designed to act as a financial assistant, answering queries related to bank services (such as credit cards). It integrates Retrieval-Augmented Generation (RAG) to ground its responses in domain-specific knowledge and publishes all interaction messages to a shared Redis stream so downstream services can monitor, classify, and simulate actions based on them.

## Key Features

1. **FastAPI Webserver**: Exposes clean JSON endpoints for interacting with the assistant, fetching session histories, and monitoring status.
2. **Retrieval-Augmented Generation (RAG)**: Integrates Chroma DB vector database, querying credit card knowledge from `/data/RAG-Cartoes`.
3. **Session Management**: Automatically saves, structures, and retrieves multi-turn dialogue histories under unique UUID-based sessions in a SQLite database.
4. **Realtime Pub/Sub Streaming**: Publishes every incoming and outgoing message (Human and AI) in real-time to a Redis queue (`msg_channel`) using the `pubsub` library.
5. **Interactive Swagger Docs**: Exposes automatic Interactive OpenAPI documentation at `http://localhost:8000/docs` (when running locally).

## Package Structure

```
apps/bancobot/
├── src/
│   └── bancobot/
│       ├── __init__.py
│       ├── config.py      # App configurations & environment parsing
│       ├── main.py        # FastAPI app initialization and route definitions
│       ├── models.py      # SQLModel definitions for Conversations & Messages
│       └── service.py     # Business logic for RAG querying, prompt loading, & Pub/Sub
├── tests/                 # Unit and integration tests for Bancobot
├── pyproject.toml
└── README.md
```

## API Specification

### 1. Health Check
* **Endpoint**: `GET /health`
* **Description**: Verifies the status of the server.
* **Response**: `{"status": "ok"}`

### 2. Send Message
* **Endpoint**: `POST /message`
* **Request Body**:
  ```json
  {
    "content": "Como posso solicitar a segunda via do meu cartão de crédito?",
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"  // Optional. If omitted, a new session is created.
  }
  ```
* **Response**:
  ```json
  {
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "content": "Para solicitar a segunda via, você pode acessar nosso aplicativo...",
    "type": "AI",
    "created_at": "2026-06-30T12:00:00"
  }
  ```

### 3. List All Sessions
* **Endpoint**: `GET /sessions`
* **Description**: Lists all active conversation session UUIDs.
* **Response**: `["3fa85f64-5717-4562-b3fc-2c963f66afa6", "7c9e6679-7425-40de-944b-e07fc1f90ae7"]`

### 4. Retrieve Session History
* **Endpoint**: `GET /sessions/{session_id}`
* **Description**: Retrieves all messages associated with a specific session, ordered chronologically.
* **Response**:
  ```json
  [
    {
      "id": "e30f146e-939e-4ebf-80be-4ca19be20fc9",
      "content": "Olá, preciso de ajuda com meu cartão.",
      "type": "Human",
      "created_at": "2026-06-30T11:59:00",
      "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    },
    {
      "id": "fa9f1708-ec47-49f6-a36c-dfc53ecbe833",
      "content": "Olá Alberto! Como posso ajudar você hoje?",
      "type": "AI",
      "created_at": "2026-06-30T12:00:00",
      "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
    }
  ]
  ```

### 5. Delete Session
* **Endpoint**: `DELETE /sessions/{session_id}`
* **Description**: Removes all messages and session logs for the given UUID from the SQLite database.
* **Response**: HTTP 204 No Content

## Configuration

Bancobot behavior is governed by the following environment variables (defined in your `.env` file):
* `DB_URL`: Connection string for the SQLite message database (e.g., `sqlite:///db/messages.db`).
* `REDIS_PORT`: Port where the Redis instance is running (e.g., `16739`).
* `MSG_CHANNEL`: Redis channel to publish messages (e.g., `msg_channel`).
* `OPENAI_API_KEY`: API key used to generate agent responses and embeddings.

For detailed run commands, refer to the [USAGE Guide](USAGE.md).
