# Touchpoint Classifier

Classifing tool to create touchpoints from messages. Saves them in a database and retransmit through a Redis Stream. Also allows exporting to csv.

## Features
- Listen to Redis Stream for new messages.
- Classify messages according to touchpoint lists.
- Save touchpoints in SQL database and send to a Redis Stream.

## Pre-requisites

- Python 3.12+
- Redis Stream
- Banco Bot
- OpenAI API Key

## Install

1. Clone the repository

```sh
git clone https://github.com/caio-bernardo/dt-chat.git
```

2. Install Dependencies

```sh
uv sync --package classifier
```

3. Enviroment Setup

```sh
cp .env.example .env
```

4. Configure your LLM API Key.

## Usage

### Creating Touchpoints

First make sure BancoBot is running and producing touchpoints. See [bancobot](../bancobot) and [swarm script](../../scripts/swarm.py) for more information.
Once this is done, use the following command to run the classifier.

```sh
classifier run data/ai_touchpoints.json data/human_touchpoints.json
```

The classifier will continuosly process new messages and store touchpoints in a database. To see how to stream the touchpoints in a Redis Stream, or how to configure behaivor. See `classifier run --help`.

### Exporting

Use the CLI to export touchpoints to a `csv` file.

```sh
classifier export --file-output output.csv --db-path sqlite:///db.sqlite3
``` 

Use `classifier export --help` to see more information.

## License

This project is licensed under the MIT License -- see the [LICENSE](../../LICENSE) file for details.
