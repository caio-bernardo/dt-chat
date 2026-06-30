# Utility Scripts

The `scripts/` directory contains standard, self-contained Python scripts designed to configure, pre-populate, simulate, or post-process data in the Digital Twin framework.

---

## 1. `embendder.py` (Knowledge Base Embedder)

* **Purpose**: Parses raw Markdown and text documents in the `data/RAG-Cartoes` directory and generates dense vector embeddings. It indexes them into a Chroma DB collection located in `./chroma_db`. This is a crucial prerequisite for the RAG-enabled Bancobot.
* **Requirements**: Access to an OpenAI Embeddings model (via `OPENAI_API_KEY`).
* **Command Syntax**:
  ```sh
  uv run scripts/embendder.py [OPTIONS]
  ```
* **Options**:
  * `--target-dir TEXT`: Directory to scan for documents (defaults to `RAG-Cartoes`).
  * `--embedding-model TEXT`: Model used to generate vectors (defaults to `text-embedding-3-large`).
  * `--persist-dir TEXT`: Directory where Chroma DB stores its sqlite-backed indexes (defaults to `./chroma_db`).
  * `--collection-name TEXT`: Name of the collection in Chroma DB (defaults to `banco_collection`).

---

## 2. `swarm.py` (User Swarm Simulator)

* **Purpose**: Simulates high-volume concurrent client traffic. It reads user persona definitions from a JSON file, spins up a pool of worker threads, and initiates parallel human-simulated sessions (`UserBots`) that send HTTP requests to a running `bancobot` server.
* **Command Syntax**:
  ```sh
  uv run scripts/swarm.py [OPTIONS] PROMPTS_FILE
  ```
* **Arguments**:
  * `PROMPTS_FILE` (Required): Path to the JSON file containing the prompt engineering / personas configurations (e.g. `data/personas/personas-30.json`).
* **Options**:
  * `--api-url TEXT`: HTTP URL of the target Bancobot API (defaults to `http://localhost:8000`).
  * `--workers INTEGER`: Number of concurrent client worker threads to use (defaults to `4`).
  * `--sequential / --no-sequential`: If enabled, runs users sequentially (overriding workers).
  * `--times INTEGER`: Number of times to run each persona sequence (defaults to `1`).
  * `--pause-probability FLOAT`: Probability of a long pause between messages (defaults to `0.05`).
  * `--pause-min FLOAT` / `--pause-max FLOAT`: Range of duration for simulated pauses in seconds.
  * `--simulate-delays / --no-simulate-delays`: If enabled, sleeps threads to simulate actual typing delays in real-time (Warning: slows execution down considerably).

---

## 3. `importer.py` (Dialogue Data Importer)

* **Purpose**: Takes raw historical or exported conversation transcripts (in JSON format) and imports them into the framework's native SQLite message database. It registers the messages under correct conversation parents and generates simulated timing configurations.
* **Command Syntax**:
  ```sh
  uv run scripts/importer.py [OPTIONS] INPUT_FILE_PATH
  ```
* **Arguments**:
  * `INPUT_FILE_PATH` (Required): Path to the conversation json file.
* **Options**:
  * `--db-conn TEXT`: Database connection URL (defaults to `sqlite:///db/messages.db`).
  * `--quiet / --no-quiet`: Suppresses logging output (defaults to `no-quiet`).
  * `--save / --no-save`: Toggle database persistence saving (defaults to `save`).

---

## 4. `ensembler.py` (Touchpoint Ensembler)

* **Purpose**: Post-processing tool that merges the touchpoint classification outputs of multiple different models (or multiple classification runs) into a single master SQLite database using a voting algorithm. This is particularly useful for establishing consensus (ground truth) classifications across different evaluation cycles.
* **Algorithm**: For every message, it reads the classified touchpoint from each provided database. It counts occurrences and selects the majority. In case of ties, the classification from the first database in the arguments list serves as the tiebreaker. Touchpoints labeled `INVALID-TOUCHPOINT-SYSTEM` are discounted.
* **Command Syntax**:
  ```sh
  uv run scripts/ensembler.py [OPTIONS] DATABASES...
  ```
* **Arguments**:
  * `DATABASES...` (Required): Space-separated list of database paths to ensemble.
* **Options**:
  * `--output-name TEXT`: Filename of the compiled output database (defaults to `output.db`).

---

## 5. `injector.py` (Bulk Database Event Injector)

* **Purpose**: Reads conversations or messages from an existing SQLite database and streams them as mock live events into a Redis channel. This allows developers to test down-stream components (like the `classifier` or `fork_engine`) on pre-recorded dataset logs as if they were occurring in real-time.
* **Command Syntax**:
  ```sh
  uv run scripts/injector.py [OPTIONS] DB_URL STREAM_NAME
  ```
* **Arguments**:
  * `DB_URL` (Required): Connection string of the source database.
  * `STREAM_NAME` (Required): Redis channel to publish events to.
* **Options**:
  * `--qnt INTEGER`: Number of items to read and stream (defaults to `100`).
  * `--offset INTEGER`: Starting database offset (defaults to `0`).
  * `--type TEXT`: Type of data structure to publish (`message` or `conversation`, defaults to `conversation`).
  * `--redis-port INTEGER`: Redis connection port (defaults to `16739`).

---

## 6. `injector-by-id.py` (Targeted Event Injector)

* **Purpose**: Injects a single specific message or conversation from the database into a Redis queue using its unique primary key ID.
* **Command Syntax**:
  ```sh
  uv run scripts/injector-by-id.py [OPTIONS] ID STREAM_NAME
  ```
* **Arguments**:
  * `ID` (Required): The UUID of the conversation or message.
  * `STREAM_NAME` (Required): Target Redis queue.
* **Options**:
  * `--db-url TEXT`: Source database URL.
  * `--type TEXT`: Event payload type (`message` or `conversation`).
  * `--redis-port INTEGER`: Redis port.

---

For instructions on configuring files or running these scripts inside a complete workflow, please see the [USAGE Guide](USAGE.md).
