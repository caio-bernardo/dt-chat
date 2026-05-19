import os

from bancobot.agent import BancoAgentBuilder
from classifier.models import Touchpoint
from dotenv import load_dotenv
from pubsub.redis import RedisQueueConsumer, RedisQueueProducer
from redis.asyncio import Redis
from userbot import UserBotBuilder

from fork_engine import twinbots
from fork_engine.engine import ForkConfig, ForkEngine
from fork_engine.helpers import (
    convert_conversation_to_langchain_types,
    retrieve_messages_until,
    retrieve_timesim_from_metadata,
    retrieve_userbot_persona_from_metadata,
)

load_dotenv()


def create_config(data: Touchpoint, bot: BancoAgentBuilder, label: str) -> ForkConfig:
    """Creates a ForkConfig for the given data and bot, with the given label.
    Inserts previous messages of the conversation
    """
    meta = data.message.conversation.meta
    userbot = UserBotBuilder()
    userbot.prompt = retrieve_userbot_persona_from_metadata(meta)

    previous_messages = convert_conversation_to_langchain_types(
        retrieve_messages_until(data.message_id)
    )

    # This touchpoint is only produced by humans, so If the message is at the
    # begining (max position 2) then we are begin the conversation from the
    # start
    if len(previous_messages) < 4:
        next_msg = "Olá"
        userbot.initial_messages = []
    else:
        # Else reask the previous question
        next_msg = previous_messages[-3].content
        userbot.initial_messages = previous_messages[:-3]

    timesim = retrieve_timesim_from_metadata(meta)
    return ForkConfig(
        parent_conversation=data.message.conversation_id,
        bancobot_builder=bot,
        userbot_builder=userbot,
        branched_message_id=data.message.id,
        next_msg=str(next_msg),  # re-ask the message before the touchpoint
        timesim=timesim,
        label=label,
    )


def two_steps(data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.two_step_rag()
    return create_config(data, bancobot, "two-step")


def triple_rag(data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.triple_rag_tool()
    return create_config(data, bancobot, "triple-rag")


# EXEMPLO:
def default(data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.single_rag_tool()
    return create_config(data, bancobot, "default")


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
