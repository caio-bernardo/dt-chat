import os

from classifier.models import Touchpoint
from dotenv import load_dotenv
from pubsub.redis import RedisQueueConsumer, RedisQueueProducer
from redis.asyncio import Redis
from sqlmodel import Session

from fork_engine import twinbots
from fork_engine.config import ForkConfig, create_config
from fork_engine.engine import ForkEngine

load_dotenv()


def two_steps(storage: Session, data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.two_step_rag()
    return create_config(storage, data, bancobot, "two-step")


def triple_rag(storage: Session, data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.triple_rag_tool()
    return create_config(storage, data, bancobot, "triple-rag")


# EXEMPLO:
def default(storage: Session, data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.single_rag_tool()
    return create_config(storage, data, bancobot, "default")


async def amain():
    print("[INFO]: Initializing Fork Engine...")

    redis = Redis(port=int(os.environ["REDIS_PORT"]))
    consumer = RedisQueueConsumer(redis)
    producer = RedisQueueProducer(redis)
    engine = ForkEngine(consumer, producer)

    print("[INFO]: Setting up fork conditions...")
    engine.create_condition(
        "SOLICITAÇÃO DIRETA DE HUMANO", [two_steps, triple_rag, default]
    )
    print("[INFO]: Listening for new messages ...")
    await engine.awatch()
