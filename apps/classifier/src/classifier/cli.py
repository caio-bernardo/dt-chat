import asyncio
import json
from typing import Any, Optional

from bancobot.models import Message, MessageType
from dotenv import load_dotenv
from pydantic import BaseModel
from redis.asyncio import Redis
from typer import Typer

from classifier.agent import ClassifierAgent
from classifier.database import create_db_and_tables, get_session
from classifier.exporter import TouchpointExporter
from classifier.service import ClassifierService

load_dotenv()

app = Typer()


def get_agent(model: str, temperature=0.0) -> ClassifierAgent:
    return ClassifierAgent(model, temperature)


def get_redis() -> Redis:
    return Redis()


def load_tp_list(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [item.get("subtipo", "") for item in data if "subtipo" in item]


@app.command(name="export")
def export_command(
    file_output: str = "output.csv", db_path: str = "sqlite:///touchpoints.db"
):
    """Export touchpoints to a csv file, retrieve touchpoints from `db_path`.

    The file is composable of an global event id, a case id (represents the
    conversation session), the producer/actor of the message, the touchpoint
    type, a timestamp of the message and a internal id, representing the age of the message in the conversatio.

    Each conversation has a `START` and `END` touchpoint with internal ids -1
    and 99999 respectively, they contain the timestamp of the first and last
    message in the conversation.
    """
    engine = create_db_and_tables(db_path)
    session = next(get_session(engine))
    exporter = TouchpointExporter(storage=session)

    print("Exporting touchpoints")
    with open(file_output, "w+") as f:
        contents = exporter.export_csv_str()
        f.write(contents.getvalue())

    print("Exporting Complete.")


class ClassifierConfig(BaseModel):
    llm_model: str
    llm_temperature: Optional[float] = None
    db_saver: str
    stream: bool
    stream_name: str
    ai_touchpoint_list: list[str]
    human_touchpoint_list: list[str]


async def arun(config: ClassifierConfig):
    agent = get_agent(config.llm_model, config.llm_temperature or 0)
    storage = next(get_session(config.db_saver))
    redis = get_redis()
    classifier = ClassifierService(agent, storage, redis)

    cases = {
        MessageType.AI: {"actor": "Bot", "tp_list": config.ai_touchpoint_list},
        MessageType.Human: {
            "actor": "Usuário",
            "tp_list": config.human_touchpoint_list,
        },
    }

    print("INFO: Classifier running. Listening to messages now. Press Ctrl-C to stop.")

    while True:
        try:
            data: dict[str, Any] = await classifier.read_stream(config.stream_name)
            message = Message.model_validate(data["payload"])

            tp = await classifier.create_and_save_touchpoint(
                message, **cases[message.type]
            )
            if config.stream:
                await classifier.publish(tp)

        except KeyboardInterrupt:
            print("INFO: User interrupted the process. Finish now.")
            break
        except Exception as e:
            print(f"ERROR: Failure on {e}")


@app.command()
def run(
    ai_touchpoints_file_path: str,
    human_touchpoints_file_path: str,
    stream_name: str = "msg_chan",
    stream: bool = False,
    db_path: str = "sqlite:///db.sqlite3",
    model: str = "gpt-3.5-turbo",
):
    """Listen for new BancoBot's messages at `stream_name`. Try to classify them
    using a llm `model` and touchpoints files (for AI and human messages).
    Saves them in a database and allows to retransmit through a redis stream.
    """
    ai_tp_list = load_tp_list(ai_touchpoints_file_path)
    human_tp_list = load_tp_list(human_touchpoints_file_path)

    config = ClassifierConfig(
        stream_name=stream_name,
        llm_model=model,
        llm_temperature=0.0,
        ai_touchpoint_list=ai_tp_list,
        human_touchpoint_list=human_tp_list,
        stream=stream,
        db_saver=db_path,
    )

    asyncio.run(arun(config))
