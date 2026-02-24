import asyncio
import uuid

from bancobot.database import RedisStorage

from fork_engine.builders import BancoBotBuilder, UserBotBuilder
from fork_engine.engine import ForkConfig, ForkEngine, StreamData
from fork_engine.helpers import load_history, map_internal_2_langchain_message


def on_reclamacao(data: StreamData) -> ForkConfig | None:

    # condition
    if data["payload"].activity == "REJEIÇÃO DA SOLUÇÃO":
        session = uuid.uuid4()

        # Init bots
        bbbuilder = BancoBotBuilder()
        bancobot = bbbuilder.build_with_default()

        conversation = load_history(
            data["payload"].session_id, data["payload"].internal_id
        )

        userbuilder = UserBotBuilder()
        userbuilder.sender = lambda msg: bancobot.process_message(session, msg)
        userbuilder.initial_messages = list(
            map(map_internal_2_langchain_message, conversation)
        )
        userbot = userbuilder.build_with_default()

        return ForkConfig(
            userbot=userbot,
            bancobot=bancobot,
            iterations=int(15 - len(conversation) / 2),
            next_msg="",
        )
    return None


async def main():
    redis = RedisStorage()
    engine = ForkEngine(redis, [on_reclamacao])
    await engine.awatch()


if __name__ == "__main__":
    asyncio.run(main())
