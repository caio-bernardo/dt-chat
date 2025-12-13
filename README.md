# dtchat
Framework for Digital Twins of conversational agents.

## Features
- Banco Bot, a conversational agent specialized at assisting client from X bank.


## Pre-requisites
- Python +3.12
- uv package manager

## Getting Started

### 1. Install all dependencies

Make sure you have uv and Python installed.

```bash
uv sync
```

> Note: a `.venv` folder will be created at the root of the project, you can enable it at your shell with `source .venv/bin/activate` and drop the `uv run ` prefix.

### 2. Set enviroment variables

Create a new file called `.env` with the same variables of `.env.example`. Configure your API keys from language models, a database url to store data, and _optionally_ LangSmith for tracing.

### 3. Build embeddings 

First of all, our agent needs access to a vector store of documents related to its domain. Create a new folder at the root of the project called `RAG-Cartoes`, or modify the name at `src/scripts/embender.py`. Inside the script set your embedding model or use the default one. The default vector store location will be at `./chroma_db` directory.

Run the script and wait a little:
```bash
uv run src/scripts/embender.py
```

Your vector store will be created and your agents can use it.

### Bonus: Run tests

Use the script inside `test/` to run tests. To run all tests:

```bash
uv run tests/run_tests.py
```

See more at [test/README.md](./test/README.md).

## License

This project is under the [MIT License](https://spdx.org/licenses/MIT.html). Check the [License](./LICENSE) for informations about permissions, distribution and modifications.
