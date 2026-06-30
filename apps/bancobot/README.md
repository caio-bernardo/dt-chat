# Banco Bot (bancobot)

Banco Bot is a conversational agent package specialized in helping clients of the fictional 'Bank X'. It is built using FastAPI and LangChain and serves as the core system-under-test in this framework.

## What it is

This package acts as an API-accessible banking assistant that uses **Retrieval-Augmented Generation (RAG)** to answer queries grounded in domain-specific documents (located in `/data/RAG-Cartoes/`). It records interactions in a local SQLite database and streams every incoming and outgoing message (Human & AI) to a Redis message queue in real-time.

## For what it can be used for

- Acting as the primary conversation interface during simulated client interactions.
- Stress-testing LLM agents under different model Backends (OpenAI GPT, Ollama, etc.).
- Serving as the primary data producer for downstream event log classification and fork-testing.

---

## Detailed Documentation

For a detailed breakdown of API endpoints, database schemas, and service logic, see the dedicated documentation page:
👉 **[docs/bancobot.md](../../docs/bancobot.md)**

To learn how to configure and run Bancobot within the complete architecture, refer to the:
👉 **[docs/USAGE.md](../../docs/USAGE.md)**
