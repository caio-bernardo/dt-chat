import asyncio
import datetime as dt
import os
from typing import Callable

from classifier.models import (  # Imports this ones for database creation
    Conversation,  # pyright: ignore[reportUnusedImport]  # noqa: F401
    Message,  # pyright: ignore[reportUnusedImport]  # noqa: F401
    Touchpoint,
)
from dotenv import load_dotenv
from pubsub import IPublisher, ISubscriber, QueueMessage
from sqlmodel import Session, SQLModel, create_engine

from .config import ForkConfig
from .procedure import BancobotProcedureCallSender

load_dotenv()

TOUCHPOINT_CHANNEL: str = os.environ["TOUCHPOINT_CHANNEL"]

TWIN_DATABASE_URL: str = os.environ["TWIN_DATABASE_URL"]


ConditionCallback = Callable[[Session, Touchpoint], ForkConfig]


def get_session(engine):
    with Session(engine) as session:
        yield session


class ForkEngine:
    """Engine to spawn new forks of conversations between bancobots and userbots"""

    def __init__(
        self, queue: ISubscriber, queue_prod: IPublisher, db_url: str | None = None
    ):
        if db_url is None:
            db_url = TWIN_DATABASE_URL

        # WARN TODO: for now the database has a copy of the messages, but fork
        # engine should read the stream and have them saved in its storage.
        engine = create_engine(db_url)
        SQLModel.metadata.create_all(engine)
        self._storage = next(get_session(engine))
        self.queue = queue
        self.queue_prod = queue_prod
        self.conditions: dict[str, list[ConditionCallback]] = {}

    def create_condition(self, activity: str, callback: list[ConditionCallback]):
        """Create a new condition to spawn forks, if activity becomes true the callback is called."""
        self.conditions[activity] = callback

    async def awatch(self):
        """Async Watch over a queue of touchpoints, matching againts conditions and spawn new forks if the condition matches."""

        # Uses TaskGroup to create forks and join them at the end
        async with asyncio.TaskGroup() as tg:
            while True:
                try:
                    data: QueueMessage = await self.queue.subscribe(TOUCHPOINT_CHANNEL)

                    tp = Touchpoint.model_validate(data["content"])

                    # Saves the touchpoint and refreshs it so it has the message and conversation relationship
                    msg = self._storage.get_one(Message, tp.message_id)
                    self._storage.refresh(msg)
                    tp.message = msg

                    # print(f"DEBUG: reads {tp}")
                    # if there is any registered callback for an activity
                    # calls the callbacks and gets the config to spawn a new fork in a different process
                    # inspired by neovim `nvim.create_augroup()`.
                    callbacks = self.conditions.get(tp.activity) or []
                    for callback in callbacks:
                        config = callback(self._storage, tp)
                        # create new task
                        tg.create_task(self.fork(config))
                except KeyboardInterrupt:
                    print("Shutdown begin... Press Ctrl-C again to stop execution.")
                    break
                except Exception as e:
                    import traceback

                    traceback.print_exc()
                    print(f"[{dt.datetime.now()}] - ERROR: {str(e)}")
            # Close queue connection
            print(f"[{dt.datetime.now()}] - INFO: Finishing all forks...")
            await self.queue.unsubscribe("tp_channel")

    async def fork(self, config: ForkConfig):
        print(
            f"[{dt.datetime.now()}] - INFO: Spawning fork for conversation {config.parent_conversation}"
        )

        """Spawn a New Fork of conversation from a configuration set."""
        bancobot = config.bancobot_builder.build_with_default()
        # create a service that can use bancoagent and publish the messages back to the classifier
        # + Generates a new session connection for this fork, so each fork has a
        # database connection that will be closed on exit.
        metadata = {
            "branched_message_id": str(config.branched_message_id),
            "twinbot_type": config.label,
        }
        config.userbot_builder.asender = BancobotProcedureCallSender(
            config.parent_conversation,
            bancobot,
            self._storage,
            self.queue_prod,
            metadata,
        )

        # execute the userbot
        userbot = config.userbot_builder.build_with_default()
        await userbot.arun(
            config.next_msg,
            config.iterations,
            config.timesim,
        )
