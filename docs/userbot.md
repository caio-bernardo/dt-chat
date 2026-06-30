# Userbot Library

The `userbot` library is a robust simulation library inside the `libs/` directory. It is designed to act as a human simulator, mimicking bank clients interacting with conversational agents.

## Purpose

To evaluate conversational AI at scale, we need active participants. The `userbot` library leverages LangChain to create simulated clients. Each user is endowed with a highly distinct financial profile, a behavioral persona, and a specific conversational goal. Furthermore, the library incorporates timing behaviors (via the `timesim` library) to simulate realistic writing speeds, thinking breaks, and long pauses, making it an excellent utility for stress testing and pathway monitoring.

## Key Features

1. **Persona-Based Prompting**: Supports parsing structured instructions like `[[como agir]]` (how to act - e.g. aggressive, anxious, patient) and `[[missão]]` (mission - e.g. activate a card, contest an unknown transaction).
2. **Behavioral Realism**: Simulates realistic conversational endpoints (e.g., quitting if frustrated, expressing confusion, or finalizing the dialogue when the goal is achieved).
3. **Realistic Chat Dynamics**: Integrates with `timesim` to attach calculated typing times, thinking times, and pause durations to messages.
4. **Flexible Senders**: Exposes abstract sender interfaces (`IMessageSender`) to allow UserBots to talk to APIs over HTTP (like `bancobot`) or internal memory channels.

## Library Structure

```
libs/userbot/
├── userbot/
│   ├── __init__.py
│   ├── bot.py         # Main UserBot class (LangChain initialization & prompt handling)
│   ├── config.py      # Personality prompt templates & regex parsers
│   ├── message.py     # Base message representations
│   └── sender.py      # Abstract interfaces for sending messages (e.g. HTTP, memory)
├── tests/
│   └── run_test.py    # Local test suite to run a sample Userbot-Chatbot dialogue loop
├── pyproject.toml
└── README.md
```

## Creating a Personas Configuration

To spin up users, you configure a personality profile (typically defined in a JSON file under `/data/personas/`). Here is an example:

```json
{
  "1": {
    "persona": "Você é Marcos, 32 anos. [[como agir]] Fale de forma ansiosa e impaciente. Exija explicações rápidas. [[missão]] Seu objetivo é contestar uma cobrança indevida no seu cartão de crédito de R$ 500,00. Encerre mandando 'quit' se o assistente se recusar a estornar.",
    "duração": "curta",
    "offset": "horario-comercial"
  }
}
```

## How to Test Individually

The library includes a self-contained test script that starts a simple in-memory dialogue between a mock user and a mock agent to prove everything functions:
```sh
uv run --package userbot libs/userbot/tests/run_test.py
```

To run high-volume concurrent swarms of simulated users against the live Bancobot API, check the [Scripts Documentation](scripts.md#3-swarmpy-user-swarm-simulator) and [USAGE Guide](USAGE.md).
