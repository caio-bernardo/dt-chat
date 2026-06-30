# Usage Guide

This document provides a comprehensive guide on how to configure, set up, and run the Digital Twin Chat (dt-chat) architecture—either step-by-step (individually) or as an end-to-end orchestrated pipeline.

---

## 1. Pre-requisites

### 1.1 Core Dependencies

- **Python 3.12+**: This codebase is managed using the [uv package manager](https://docs.astral.sh/uv/). Install `uv` on your machine, which will automatically download and isolate the correct Python version.
- **Docker / Docker Compose**: Required to spin up the localized Redis service used as the message broker.
- **Just**: A handy command runner. If you don't have it, install it via `cargo install just`, `brew install just`, or your system packager. (See [Just website](https://just.systems/man/en/) for details).
- **LLM Provider API Key**: An active API Key (such as OpenAI's `OPENAI_API_KEY`) to run the embeddings model and the LLM agent configurations.

### 1.2 Environment Variables Configuration

Copy the example configuration to create your local `.env` file:

```sh
cp .env.example .env
```

Open the newly created `.env` file and fill in or verify the following configuration keys:

```ini
# --- LLM Models Setup ---
OPENAI_API_KEY=your-openai-api-key-here

# Ollama Base URL and API Key (if running local Llama/Qwen models)
OLLAMA_BASE_URL=
OLLAMA_API_KEY=

# --- Observability (Optional) ---
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=

# --- SQLite Databases ---
DB_URL=sqlite:///db/messages.db
TWIN_DATABASE_URL=sqlite:///db/twin.db
TOUCHPOINT_DATABASE_URL=sqlite:///db/touchpoints.db

# --- Redis Message Queue ---
REDIS_PORT=16739
MSG_CHANNEL=msg_channel
TOUCHPOINT_CHANNEL=tp_channel

# --- Service Endpoints ---
BANCOBOT_URL=http://localhost:8000

# --- Python Environment ---
PYTHONUNBUFFERED=1
PYTHONPATH=$PWD
```

### 1.3 Pre-configured Data Folders

The project contains several essential subdirectories within `/data/` which store input parameters:

- **`data/RAG-Cartoes/`**: Markdown and text files describing fictional banking credit card terms. It serves as the knowledge base documents database.
- **`data/touchpoints/`**: Contains touchpoint catalog descriptors `Touchpoint_ai.json` and `Touchpoint_human.json` used by the classifier.
- **`data/personas/`**: Contains various JSON files (`personas-3.json`, `personas-30.json`, `personas-300.json`) defining the behavioral templates of simulated customers.

---

## 2. Step-by-Step Execution Guide

This section describes how to run each layer of the architecture individually, allowing you to test specific parts of the pipeline.

### Step 2.1: Start the Message Broker (Redis)

All inter-process communication flows through Redis queues. Launch Redis inside a Docker container:

```sh
just redis-up
```

Useful broker utilities:

- **Check Queue Size**: `just redis-queue-size msg_channel`
- **Clear Queue Contents**: `just redis-clear msg_channel`
- **Stop Container**: `just redis-down`

### Step 2.2: Generate the Vector Database

Before launching the conversational agent, parse the credit card files and index them into embeddings inside `chroma_db/`:

```sh
uv run scripts/embendder.py
```

_This command reads documentation from `data/RAG-Cartoes/` and saves vectors locally using OpenAI's `text-embedding-3-large` model._

### Step 2.3: Run the Bancobot Chatbot API

Start the core chatbot webserver:

```sh
just bancobot
```

- **Development Auto-Reload**: `just watch-bancobot`
- **Swagger Interactive Docs**: Open `http://localhost:8000/docs` in your browser to inspect or test routes directly.

### Step 2.4: Simulate Client Conversations (User Swarm)

With Bancobot running, generate concurrent client traffic using a persona catalog:

```sh
uv run scripts/swarm.py data/personas/personas-30.json
```

_This starts a multi-threaded swarm (4 threads by default) sending parallel client requests over HTTP to Bancobot. Each conversation is recorded with unique session UUIDs._

### Step 2.5: Start the Touchpoint Classifier Worker

Process and structure the raw conversation messages:

```sh
just classifier
```

_This spawns a worker that subscribes to the Redis raw message stream. For every message, it invokes the LLM to classify it into a business touchpoint (e.g. human greetings, credit card requests, human operator escalation), saves the results to SQLite (`db/touchpoints.db`), and republishes the touchpoints to a secondary Redis stream (`tp_channel`)._

### Step 2.6: Start the Fork Engine (Digital Twin Simulations)

Launch the simulator core to watch for "what-if" branch triggers:

```sh
just forker
```

_This monitors the touchpoint stream. When a catalyst event (such as `"SOLICITAÇÃO DIRETA DE HUMANO"`) is observed, the engine splits the conversation. It creates several alternative Digital Twin agents (e.g., local LLMs, alternative prompt configurations, different RAG models) and runs parallel simulations of the user and chatbot starting from that exact historical state._

### Step 2.7: Export Labeled Event Logs

Export your structured touchpoint timeline into a clean CSV format:

```sh
just exporter output-file="touchpoint_logs.csv" db-path="db/touchpoints.db"
```

_This tool automatically appends synthetic start/end points and reconstructs parent conversation histories for branched forks so that the CSV can be processed directly by process mining algorithms._

---

## 3. End-to-End Orchestrated Walkthrough

To run a complete simulation pipeline from raw generation up to digital twin evaluation, follow this orchestrated sequence.

### Phase 1: Infrastructure & Data Setup

1. **Ensure environment keys are loaded** in `.env`.
2. **Start the Redis broker**:
   ```sh
   just redis-up
   ```
3. **Build the vector database embeddings**:
   ```sh
   uv run scripts/embendder.py
   ```

### Phase 2: Start Active Backend Observers

Open three separate terminal windows or run the processes in the background:

- **Terminal 1 (The Chatbot)**:
  ```sh
  just bancobot
  ```
- **Terminal 2 (The Touchpoint Classifier)**:
  ```sh
  just classifier
  ```
- **Terminal 3 (The Fork Engine)**:
  ```sh
  just forker
  ```

### Phase 3: Initiate Generation & Simulation

With the observer services online and listening, start the dialogue generator in a fourth terminal:

- **Terminal 4 (The Swarm Trigger)**:
  ```sh
  uv run scripts/swarm.py data/personas/personas-30.json
  ```

**What happens behind the scenes:**

1. The **Swarm** initiates multiple concurrent sessions with **Bancobot**.
2. **Bancobot** processes the messages, responds using RAG, and streams each message (human & AI) to Redis (`msg_channel`).
3. The **Classifier** intercepts the raw messages, maps them to touchpoint activities, saves them to SQLite, and streams the touchpoints to Redis (`tp_channel`).
4. The **Fork Engine** intercepts the touchpoint stream. When it detects a trigger condition (like an escalation/direct inquiry), it freezes the state, forks the session, and triggers parallel digital twin runs.
5. All twin activities are channeled back to the **Classifier** and stored cleanly in the touchpoint database.

### Phase 4: Compile and Export Results

Once the swarm terminates and processing is complete, stop the observers (`Ctrl+C`) and execute the exporter to compile the event log:

```sh
just exporter output-file="simulation_event_log.csv"
```

The resulting `simulation_event_log.csv` is now fully ready to be loaded into standard Process Mining software (such as Celonis, Disco, or the Python `PM4Py` library) to evaluate agent behavior, trace path frequencies, and discover performance bottlenecks!
