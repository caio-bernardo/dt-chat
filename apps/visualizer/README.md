# Visualizer

Visualizer for the BancoBot interactions via a web-based interface, allowing to view conversations.

## Features
- UI to view all conversations, split by session
- See AI messages and human messages
- Realtime updates (1 second delay)

## Prerequisites

- Python 3.12
- uv Package Manager

## Install

- Install dependencies

```sh
uv sync --package visualizer
```

## Usage

- Run with BancoBot Server. See [bancobot](apps/bancobot/README.md) for how to.
- Run streamlit application:
```sh
uv run --package visualizer apps/visualizer/src/visualizer
```

Or use one of the tasks:

```sh
uv run task visualizer
```

## Built With
- Python
- uv Package Manager
- StreamLit

## License

This project is licensed under the MIT License -- see the [LICENSE](../../LICENSE) file for details.
