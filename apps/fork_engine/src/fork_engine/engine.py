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

# Read env vars lazily / safely so importing this module doesn't crash in unit tests.
DEFAULT_TOUCHPOINT_CHANNEL: str = os.getenv("TOUCHPOINT_CHANNEL", "tp_channel")
DEFAULT_TWIN_DATABASE_URL: str | None = os.getenv("TWIN_DATABASE_URL")

DEFAULT_QUEUE_SIZE: int = int(os.getenv("FORK_QUEUE_SIZE", "1000"))
DEFAULT_WORKERS: int = int(os.getenv("FORK_WORKERS", "8"))
DEFAULT_MAX_FORKS: int = int(os.getenv("FORK_MAX_FORKS", "6"))
# Maximum number of concurrent DB sessions used by watcher + forks.
DEFAULT_MAX_DB_SESSIONS: int = int(os.getenv("FORK_MAX_DB_SESSIONS", "6"))

DEFAULT_DB_POOL_SIZE: int = int(os.getenv("FORK_DB_POOL_SIZE", "10"))
DEFAULT_DB_MAX_OVERFLOW: int = int(os.getenv("FORK_DB_MAX_OVERFLOW", "10"))
DEFAULT_DB_POOL_TIMEOUT: int = int(os.getenv("FORK_DB_POOL_TIMEOUT", "30"))


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
            db_url = DEFAULT_TWIN_DATABASE_URL

        if not db_url:
            raise ValueError(
                "Missing database url: pass `db_url` or set TWIN_DATABASE_URL env var"
            )

        # WARN TODO: for now the database has a copy of the messages, but fork
        # engine should read the stream and have them saved in its storage.
        engine_kwargs = {}
        # Avoid passing queue pool args for sqlite, which uses a different pool strategy.
        if not db_url.startswith("sqlite"):
            engine_kwargs = {
                "pool_size": DEFAULT_DB_POOL_SIZE,
                "max_overflow": DEFAULT_DB_MAX_OVERFLOW,
                "pool_timeout": DEFAULT_DB_POOL_TIMEOUT,
                "pool_pre_ping": True,
            }

        engine = create_engine(db_url, **engine_kwargs)
        SQLModel.metadata.create_all(engine)
        self._engine = engine
        self.queue = queue
        self.queue_prod = queue_prod
        self.conditions: dict[str, list[ConditionCallback]] = {}
        self._fork_tasks: set[asyncio.Task] = set()

        self._queue_size = DEFAULT_QUEUE_SIZE
        self._workers = DEFAULT_WORKERS
        self._max_forks = DEFAULT_MAX_FORKS
        self._max_db_sessions = DEFAULT_MAX_DB_SESSIONS

    def create_condition(self, activity: str, callback: list[ConditionCallback]):
        """Create a new condition to spawn forks, if activity becomes true the callback is called."""
        self.conditions[activity] = callback

    async def awatch(self, channel: str | None = None):
        """Async Watch over a queue of touchpoints, matching againts conditions and spawn new forks if the condition matches."""
        channel = channel or DEFAULT_TOUCHPOINT_CHANNEL

        inbound = asyncio.Queue(maxsize=self._queue_size)
        fork_sem = asyncio.Semaphore(self._max_forks)
        db_sem = asyncio.Semaphore(self._max_db_sessions)

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._consume_message(channel, inbound))
                for _ in range(self._workers):
                    tg.create_task(self._worker(inbound, fork_sem, db_sem))
        finally:
            print(f"[{dt.datetime.now()}] - INFO: Finishing all forks...")
            await self.queue.unsubscribe(channel)
            if self._fork_tasks:
                await asyncio.gather(*self._fork_tasks, return_exceptions=True)

    async def _consume_message(
        self, channel: str, inbound: asyncio.Queue[QueueMessage]
    ):
        while True:
            data: QueueMessage = await self.queue.subscribe(channel)
            await inbound.put(data)

    async def _worker(
        self,
        inbound: asyncio.Queue[QueueMessage],
        fork_sem: asyncio.Semaphore,
        db_sem: asyncio.Semaphore,
    ):
        while True:
            data = await inbound.get()
            try:
                await self._handle_message(data, fork_sem, db_sem)
            except Exception as e:
                print(f"[{dt.datetime.now()}] - ERROR: {str(e)}")
            finally:
                inbound.task_done()

    async def _handle_message(
        self,
        data: QueueMessage,
        fork_sem: asyncio.Semaphore,
        db_sem: asyncio.Semaphore,
    ):
        async with db_sem:
            configs = await asyncio.to_thread(self._build_configs, data)

        for config in configs:
            task = asyncio.create_task(self._spawn_fork(config, fork_sem, db_sem))
            self._fork_tasks.add(task)
            task.add_done_callback(self._fork_tasks.discard)

    def _build_configs(self, data: QueueMessage) -> list[ForkConfig]:
        tp = Touchpoint.model_validate(data["content"])
        with Session(self._engine) as session:
            msg = session.get_one(Message, tp.message_id)
            session.refresh(msg)
            tp.message = msg

            callbacks = self.conditions.get(tp.activity) or []
            return [callback(session, tp) for callback in callbacks]

    async def _spawn_fork(
        self, config: ForkConfig, fork_sem: asyncio.Semaphore, db_sem: asyncio.Semaphore
    ):
        async with fork_sem:
            try:
                await self.fork(config, db_sem=db_sem)
            except Exception as e:
                print(f"[{dt.datetime.now()}] - ERROR: {str(e)}")

    async def fork(self, config: ForkConfig, db_sem: asyncio.Semaphore | None = None):
        print(
            f"[{dt.datetime.now()}] - INFO: Spawning fork for conversation {config.parent_conversation}"
        )

        """Spawn a New Fork of conversation from a configuration set."""
        bancobot = await asyncio.to_thread(config.bancobot_builder.build_with_default)
        # create a service that can use bancoagent and publish the messages back to the classifier
        # + Generates a new session connection for this fork, so each fork has a
        # database connection that will be closed on exit.
        # WARN: "twin_bot_type" and "branched_message_id" are deprecated, please use the new keys
        metadata = {
            "catalyst_message_id": str(config.branched_message_id),
            "bot_label": config.label,
        }

        if db_sem is None:
            await self._run_fork_with_session(config, bancobot, metadata)
            return

        async with db_sem:
            await self._run_fork_with_session(config, bancobot, metadata)

    async def _run_fork_with_session(
        self, config: ForkConfig, bancobot, metadata: dict
    ):
        with Session(self._engine) as fork_session:
            config.userbot_builder.asender = BancobotProcedureCallSender(
                config.parent_conversation,
                bancobot,
                fork_session,
                self.queue_prod,
                metadata,
            )

            # Re-make the temporal offset to start from the forked message
            # Because the old offset considers the distance between the target date and the time the conversation was made.
            # This code recalculates the offset by using the target date and the current time to give a new distance.
            config.timesim.temporal_offset = config.target_date - dt.datetime.now()

            # execute the userbot
            userbot = await asyncio.to_thread(config.userbot_builder.build_with_default)
            await userbot.arun(
                config.next_msg,
                config.iterations,
                config.timesim,
            )
