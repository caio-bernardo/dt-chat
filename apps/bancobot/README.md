# Banco Bot

Banco Bot is a conversational agent specialized in helping clients from the _fictional_ 'X Bank'. It's used for evaluating the touch-point processing tool and simulation capabilities of this project.

## Features
- Json API to interact with LLM Model
- Agent can use **Retrieval Augmentanted Generation** (RAG) to answer user's questions
- Save and retrieve conversations through a session system.
- Follow messages creations through a endpoint stream or Redis.
- Swagger Documentation at `BASE_URL/docs`.

## Prerequisites
- Python 3.12+
- [uv Package Manager](https://docs.astral.sh/uv/)
- OpenAI API Key
- LangSmith API Key (optional, only if you want tracing for your llm model) 
- Redis Database

## Install

1. Clone the repository

```sh
git clone https://github.com/caio-bernardo/dt-chat.git
```

2. Install Dependencies

```sh
uv sync --package bancobot
```

3. Enviroment Setup

```sh
cp .env.example .env
```

Update the `.env` with your configuration:
- OpenAI API Key
- LangSmith API Key (optional)
- Database URL (or use default: `sqlite:///messages.db`)

4. Vector Database

The agent uses a vector database to retrieve content and give better responses. 

Create a folder called `RAG-Cartoes` at the root of the project.

```sh
mkdir RAG-Cartoes
```

Put all files you want to be retrieved by the agent.

 Use `embendder.py` script to create the vector store.

```sh
uv run scripts/embendder.py
```

> See [embendder.py](../../scripts/embendder.py) to more information and how to configure it.

5. Install Redis

See this link: https://redis.io/docs/latest/operate/oss_and_stack/install/archive/install-redis/. On how to install and start Redis on your machine.

## Usage

> Always make sure Redis is running when the application starts!

1. Development

```sh
uv run --package bancobot fastapi dev apps/bancobot
```

Visit: http://localhost:8000

2. Production

```sh
uv run --package bancobot bancobot
```
Visit: http://localhost:8080

Make http requests to the server. You can see all endpoints and test then at `http://localhost:8000/docs`.

### API Endpoints

**Health endpoint**: check for status of the server.

```sh
curl http://localhost:8000/health
```

**Create a message**: send a message to the agent, you may pass a session id, so the model remembers previous conversations, if none is passed, a new session is created.

```sh
curl http://localhost:8000/message -X POST -d '{"content": "Hello"}'
```
Returns a JSON object with the agent's answer, a session UUID, datetime of creation and type of message (HTTP 200). Example response:
```json
{ "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "content": "Hello, from AI", "type": "AI", "created_at": "2025-12-12 00:00:00" }
```

**List all sessions**:

```sh
curl http://localhost:8000/sessions
```
Returns a JSON array of session UUIDs (HTTP 200). Example response:
```json
["3fa85f64-5717-4562-b3fc-2c963f66afa6", "7c9e6679-7425-40de-944b-e07fc1f90ae7"]
```

**Retrieve a session**: returns messages for a given session id
```sh
curl http://localhost:8000/sessions/<SESSION_UUID>
```
Replace `<SESSION_UUID>` with the session id. Returns a JSON array of Message objects (HTTP 200). Each Message contains fields defined by the Message model (e.g. id, content, type, session_id, created_at).

- **Delete a session**: remove all messages for a given session id
```sh
curl -X DELETE http://localhost:8000/sessions/<SESSION_UUID>
```
Returns HTTP 204 No Content on success. If an error occurs, the API will return an appropriate error status and detail message (HTTP 4xx/5xx).

## Built With

- Python
- uv Package Manager
- [LangChain](https://python.langchain.com/docs/get_started/introduction)
- Chroma DB
- Redis

## License

This project is licensed under the MIT License -- see the [LICENSE](../../LICENSE) file for details.
