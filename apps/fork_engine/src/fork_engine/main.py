import os

from classifier.models import Touchpoint
from dotenv import load_dotenv
from pubsub.redis import RedisQueueConsumer, RedisQueueProducer
from redis.asyncio import Redis
from userbot import UserBotBuilder

from fork_engine import twinbots
from fork_engine.engine import ForkConfig, ForkEngine
from fork_engine.helpers import (
    convert_conversation_to_langchain_types,
    retrieve_timesim_from_metadata,
    retrieve_userbot_persona_from_metadata,
)

load_dotenv()


def insatisfaction(data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.two_step_rag()

    # Gets the persona and timesim from the original conversation
    meta = data.message.conversation.meta

    # Userbot builder
    userbot = UserBotBuilder()
    userbot.prompt = retrieve_userbot_persona_from_metadata(meta)
    # put messages from the conversation on the userbot
    conversation = convert_conversation_to_langchain_types(
        data.message.conversation.messages
    )
    # print(f"[DEBUG]: {conversation}")
    # pass history of conversation if we have at least 4 messages
    # because -1 is the touchpoint, -2 is the answer that "caused" the
    # touchpoint, and -3 will be reasked (or modified) in the next step to see
    # if we can avoid the touchpoint
    if len(conversation) < 4:
        userbot.initial_messages = []
    else:
        userbot.initial_messages = conversation[:-4]  # last message that caused

    # retrieve the time config from the conversation
    timesim = retrieve_timesim_from_metadata(meta)

    return ForkConfig(
        parent_conversation=data.message.conversation_id,
        bancobot_builder=bancobot,
        userbot_builder=userbot,
        branched_message_id=data.message.id,
        next_msg=str(
            conversation[-3].content
        ),  # re-ask the message before the touchpoint
        timesim=timesim,
        label="two-steps",
    )


# EXEMPLO:
def default(data: Touchpoint) -> ForkConfig:
    bancobot = twinbots.single_rag_tool()

    # Gets the persona and timesim from the original conversation
    meta = data.message.conversation.meta

    # Userbot builder
    userbot = UserBotBuilder()
    userbot.prompt = retrieve_userbot_persona_from_metadata(meta)
    # put messages from the conversation on the userbot
    conversation = convert_conversation_to_langchain_types(
        data.message.conversation.messages
    )
    # print(f"[DEBUG]: {conversation}")
    # pass history of conversation if we have at least 4 messages
    # because -1 is the touchpoint, -2 is the answer that "caused" the
    # touchpoint, and -3 will be reasked (or modified) in the next step to see
    # if we can avoid the touchpoint
    if len(conversation) < 4:
        userbot.initial_messages = []
    else:
        userbot.initial_messages = conversation[:-4]  # last message that caused

    # retrieve the time config from the conversation
    timesim = retrieve_timesim_from_metadata(meta)

    print(f"DEBUG: {timesim}")

    return ForkConfig(
        parent_conversation=data.message.conversation_id,
        bancobot_builder=bancobot,
        userbot_builder=userbot,
        branched_message_id=data.message.id,
        next_msg=str(
            conversation[-3].content
        ),  # re-ask the message before the touchpoint
        timesim=timesim,
        label="default",
    )


async def amain():
    print("[INFO]: Initializing Fork Engine...")

    redis = Redis(port=int(os.environ["REDIS_PORT"]))
    consumer = RedisQueueConsumer(redis)
    producer = RedisQueueProducer(redis)
    engine = ForkEngine(consumer, producer)

    print("[INFO]: Setting up fork conditions...")
    engine.create_condition("RESPOSTA COM INSATISFAÇÃO", [default])
    # engine.create_condition("SOLICITAÇÃO DIRETA DE HUMANO", [on_transbordo, default])
    print("[INFO]: Listening for new messages ...")
    await engine.awatch()
