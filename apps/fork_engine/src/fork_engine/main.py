import asyncio

from bancobot.agent import BancoAgentBuilder
from classifier.models import Touchpoint
from pubsub.redis import RedisQueueConsumer, RedisQueueProducer
from redis.asyncio import Redis
from userbot import UserBotBuilder

from fork_engine.engine import ForkConfig, ForkEngine
from fork_engine.helpers import (
    retrieve_conversation_messages,
    retrieve_conversation_metadata,
    retrieve_timesim_from_metadata,
    retrieve_userbot_persona_from_metadata,
)


def on_reclamacao(data: Touchpoint) -> ForkConfig:
    bancobot = BancoAgentBuilder()
    # bancobot.prompt = "Você um assistente virtual muito gentil" # exemplo de mudança de engenharia de prompt

    # Gets the persona and timesim from the original conversation
    meta = retrieve_conversation_metadata(data.session_id)

    # Userbot builder
    userbot = UserBotBuilder()
    userbot.prompt = retrieve_userbot_persona_from_metadata(meta)
    # put messages from the conversation on the userbot
    conversation = retrieve_conversation_messages(data.session_id)
    # pass all history except the last two messages that caused the current touchpoint + remove the last answer because the conversation will re-start from -4
    userbot.initial_messages = conversation[:-3]

    # retrieve the time config from the conversation
    timesim = retrieve_timesim_from_metadata(meta)

    return ForkConfig(
        parent_conversation=data.session_id,
        bancobot_builder=bancobot,
        userbot_builder=userbot,
        next_msg=str(conversation[-4].content),
        timesim=timesim,
    )


async def main():
    redis = Redis()
    consumer = RedisQueueConsumer(redis)
    producer = RedisQueueProducer(redis)
    engine = ForkEngine(consumer, producer)

    engine.create_condition("REJEIÇÃO DA SOLUÇÃO", on_reclamacao)
    await engine.awatch()


if __name__ == "__main__":
    asyncio.run(main())
