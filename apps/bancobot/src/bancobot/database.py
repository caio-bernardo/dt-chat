import os

import redis.asyncio as redis
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine

from .models import *  # noqa: F403

load_dotenv()

engine = create_engine(os.environ["DB_URL"])
redis_port = int(os.environ.get("REDIS_PORT", 16379))

# Redis connection
redis_client = redis.Redis(host="localhost", port=redis_port)


def create_db_and_tables():
    """Initialize SQLModel with database and tables"""

    SQLModel.metadata.create_all(engine)
