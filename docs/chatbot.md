# Chatbot Library

`chatbot` is a foundational library in the `libs/` directory. It acts as an abstraction wrapper around the **LangChain** library to simplify, standardize, and accelerate the creation of conversational agents across this repository.

## Purpose

Different components (such as `bancobot`, `fork_engine`, and some of the standalone scripts) require chatbot agents with varying capabilities (some use RAG, others use local models, and others are single/multi-tool setups). This library provides reusable components, unified base classes, and default agent prompt definitions to initialize conversational bots cleanly without duplicating LLM setup boilerplate.

## Key Features

1. **Unified Initialization**: Standard interfaces to create model instances (Ollama, OpenAI GPT, Qwen, etc.) using a simple unified configuration interface.
2. **Tools Binding**: Seamless bindings for custom analytical tools, search retrieval functions, or RAG components.
3. **Structured Response Formatting**: Standard helpers to handle streaming outputs, error handling, and structured JSON structures.

## Library Structure

```
libs/chatbot/
├── chatbot/
│   ├── __init__.py
│   ├── agents.py      # Base Agent definitions and custom LangChain prompt helpers
│   ├── models.py      # Supported LLM backend structures & factory initializers
│   └── tools.py       # Base tool declarations and definitions (e.g. database search)
├── pyproject.toml
└── README.md
```

## Basic Usage

The library is designed to be imported directly by other packages or scripts. For example:

```python
from chatbot.models import ChatModelFactory, ModelConfig
from chatbot.agents import create_financial_agent

# 1. Configure the model
config = ModelConfig(
    provider="openai",
    model_name="gpt-4o-mini",
    temperature=0.0
)
llm = ChatModelFactory.build(config)

# 2. Build the agent with tools
agent = create_financial_agent(llm, tools=[my_rag_retriever_tool])

# 3. Invoke
response = agent.invoke({"input": "Como posso pagar a fatura?"})
print(response["output"])
```

For higher-level application integrations, consult the [Bancobot Documentation](bancobot.md) or [Fork Engine Documentation](fork_engine.md).
