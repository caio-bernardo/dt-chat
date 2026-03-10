import json
import os
from typing import Any

import redis.asyncio as redis
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine

from bancobot.services import IStorage

from .models import *  # noqa: F403

load_dotenv()

engine = create_engine(os.environ["DB_URL"])


def create_db_and_tables():
    """Initialize SQLModel with database and tables"""

    SQLModel.metadata.create_all(engine)


class RedisStorage(IStorage):
    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        self.redis = redis.Redis(host=host, port=port)

    async def arcv(self, source: str) -> Any:
        return await self.redis.xread({source: "0"}, count=1, block=100)

    async def asend(self, dst: str, origin: str, value: Any):
        # WARN: need to serialize payload since redis only accepts primitive types (int, str, float)
        await self.redis.xadd(dst, {"origin": origin, "payload": json.dumps(value)})
