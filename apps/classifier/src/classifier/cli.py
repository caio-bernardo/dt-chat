import asyncio
import json
import os
from datetime import datetime
from typing import Optional

from bancobot.models import MessageType
from dotenv import load_dotenv
from pubsub import QueueMessage
from pubsub.redis import RedisQueueConsumer, RedisQueueProducer
from pydantic import BaseModel
from redis.asyncio import Redis
from typer import Typer

from classifier.agent import ClassifierAgent
from classifier.database import create_db_and_tables, get_session
from classifier.models import Conversation, Message
from classifier.services import ClassifierService, TouchpointItem

load_dotenv()

app = Typer()

MSG_CHANNEL: str = os.environ["MSG_CHANNEL"]
TOUCHPOINT_CHANNEL: str = os.environ["TOUCHPOINT_CHANNEL"]
DB_URL: str = os.environ["TOUCHPOINT_DATABASE_URL"]


def get_agent(model: str, temperature=0.0) -> ClassifierAgent:
    return ClassifierAgent(model, temperature)


def get_redis() -> Redis:
    return Redis(port=int(os.environ["REDIS_PORT"]))


def load_tp_list(path: str) -> list[TouchpointItem]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [TouchpointItem.model_validate(item) for item in data]


class ClassifierConfig(BaseModel):
    llm_model: str
    llm_temperature: Optional[float] = None
    db_saver: str
    stream: bool
    stream_name: str
    ai_touchpoint_list: list[TouchpointItem]
    human_touchpoint_list: list[TouchpointItem]


async def arun(config: ClassifierConfig):
    agent = get_agent(config.llm_model, config.llm_temperature or 0)
    engine = create_db_and_tables(config.db_saver)
    storage = next(get_session(engine))
    redis = get_redis()
    classifier = ClassifierService(agent, storage)
    consumer = RedisQueueConsumer(redis)
    producer = RedisQueueProducer(redis)

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
            data: QueueMessage = await consumer.subscribe(config.stream_name)

            if data["model_type"] == "conversation":
                conversation = Conversation.model_validate(data["content"])
                classifier.save_conversation(conversation)
                continue
            elif data["model_type"] != "message":
                raise ValueError("Wrong data passed on the queue:", data)

            message = Message.model_validate(data["content"])

            classifier.save_message(message)
            tp = await classifier.create_and_save_touchpoint(
                message, **cases[message.type]
            )

            # print(f"[{datetime.now()}] INFO: Touchpoint produced. Detail: {tp}")

            # INFO: we do not repass messages comming from the fork, or else we
            # may have a recursive explosion of messages made by the forkers
            # causing more forks
            if config.stream and data["origin"] != "twin_bancobot":
                payload: QueueMessage = {
                    "origin": "classifier",
                    "model_type": "touchpoint",
                    "content": tp.model_dump(mode="json"),
                }
                await producer.publish(TOUCHPOINT_CHANNEL, payload)

        except KeyboardInterrupt:
            print(
                f"[{datetime.now()}] INFO: User interrupted the process. Finishing now."
            )
            break
        except Exception as e:
            print(f"[{datetime.now()}] ERROR: Failure on {e}")
            break
    await consumer.unsubscribe(config.stream_name)


@app.command()
def run(
    ai_touchpoints_file_path: str,
    human_touchpoints_file_path: str,
    model: str = "openai:gpt-5.4-nano",
    stream_name: str = "msg_channel",
    stream: bool = False,
    db_path: str = DB_URL,
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
