# Usage

This document guides the user in how to setup the running architecture.

## 1. Pre-requisites

### 1.1 Dependecies

- Python 3.12 (preferebly through _uv_)
- Docker 29.4
- [Just](https://just.systems/man/en/)
- OpenAI API Key or Other models Keys

### 1.2 Environment Variables

To run various prograns in this architecture you need to setup some environment variables, copy the file `.env.example`.

```sh
cp .env.example .env
```

Fill out the following variables.

```sh
# Your OPENAI API Key if using GPT models.
OPENAI_API_KEY=

# If using llama models
OLLAMA_BASE_URL=
OLLAMA_API_KEY=

# LangSmith tracing
LANGSMITH_TRACING=true # Change to true if you want this functionality.
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=

# Databases setups
DB_URL=sqlite:///db/messages.db
TWIN_DATABASE_URL=sqlite:///db/twin.db
TOUCHPOINT_DATABASE_URL=sqlite:///db/touchpoints.db

# Redis Queue
# Queue for messages & touchpoints
MSG_CHANNEL=msg_channel
TOUCHPOINT_CHANNEL=tp_channel
REDIS_PORT=16739

# URL for the Bancobot package
BANCOBOT_URL=http://localhost:8000

PYTHONUNBUFFERED=1
PYTHONPATH=$PWD
```

### 1.3 Necessary files

The `data` folder contains the needed files to run this project. This includes:

- Documents database to build a _RAG_ agent (in `RAG-Cartoes`).
- List of allowed activities, with descriptions (in `touchpoints`).
- Prompts and metadata that allows the simulations to happed (in `personas`).

There are also output examples stored in `data/output`.

> **Disclaimer**: all datasets and results in this folder are protected under the [CC-BY-SA-4.0](../data/LICENSE).

## 2. Packages

This section explains how to setup in order all packages (inside the `apps` folder), in the end, we'll explain how to run them together.

### 2.1 Bancobot API

This package executes a webserver exposing a single chatbot capable of answering questions about the

### 2.2 Classifier

### 2.3 Fork Engine

### 2.4 Exporter

### 2.5 Sticking Pieces Together

## 3. Scripts

### 3.1 Embendder.py

### 3.2 Swarm.py

### 3.3 Importer.py

### 3.2 Injector.py
