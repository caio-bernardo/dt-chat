import datetime as dt
import os
import uuid
from multiprocessing import Process
from typing import Callable

from bancobot.agent import BancoAgentBuilder
from classifier.models import Touchpoint
from dotenv import load_dotenv
from pubsub import IPublisher, ISubscriber, QueueMessage
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session, create_engine
from userbot import TimeSimulationConfig, UserBotBuilder

from .helpers import BancobotProcedureCallSender

load_dotenv()

TOUCHPOINT_CHANNEL: str = os.environ["TOUCHPOINT_CHANNEL"]

TWIN_DATABASE_URL: str = os.environ["TWIN_DATABASE_URL"]


class ForkConfig(BaseModel):
    """Configuration of a Fork process. Allows to create a new conversation between a userbot and a bancobot, with specific values."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    parent_conversation: uuid.UUID
    bancobot_builder: BancoAgentBuilder
    userbot_builder: UserBotBuilder
    next_msg: str
    timesim: TimeSimulationConfig = TimeSimulationConfig()
    iterations: int = 15


ConditionCallback = Callable[[Touchpoint], ForkConfig]


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
        engine = create_engine(db_url)
        self._storage = get_session(engine)
        self.queue = queue
        self.queue_prod = queue_prod
        self.conditions: dict[str, ConditionCallback] = {}

    def create_condition(self, activity: str, callback: ConditionCallback):
        """Create a new condition to spawn forks, if activity becomes true the callback is called."""
        self.conditions[activity] = callback

    async def awatch(self):
        """Async Watch over a queue of touchpoints, matching againts conditions and spawn new forks if the condition matches."""
        threads: list[Process] = []
        while True:
            try:
                data: QueueMessage = await self.queue.subscribe(TOUCHPOINT_CHANNEL)

                tp = Touchpoint.model_validate(data["content"])
                print(f"DEBUG: reads {tp}")
                # if there is a registered callback for an activity
                # calls the callback and gets the config to spawn a new fork in a different process
                # inspired by neovim `nvim.create_augroup()`.
                callback = self.conditions.get(tp.activity)
                if callback:
                    config = callback(tp)
                    t = Process(target=self.fork, args=(config,))
                    threads.append(t)
                    t.start()
            except Exception as e:
                print(f"[{dt.datetime.now()}] - ERROR: {str(e)}")
            finally:
                # Close queue and wait for forks to finish
                print(f"[{dt.datetime.now()}] - INFO: Finishing all forks...")
                await self.queue.unsubscribe("tp_channel")
                for t in threads:
                    t.join()
                break

    async def fork(self, config: ForkConfig):
        print(
            f"[{dt.datetime.now()}] - INFO: Spawning fork for conversation {config.parent_conversation}"
        )

        """Spawn a New Fork of conversation from a configuration set."""
        bancobot = config.bancobot_builder.build_with_default()
        # create a service that can use bancoagent and publish the messages back to the classifier
        # + Generates a new session connection for this fork, so each fork has a
        # database connection that will be closed on exit.
        config.userbot_builder.asender = BancobotProcedureCallSender(
            config.parent_conversation, bancobot, next(self._storage), self.queue_prod
        )

        # execute the userbot
        userbot = config.userbot_builder.build_with_default()
        await userbot.arun(
            config.next_msg,
            config.iterations,
            config.timesim,
        )
