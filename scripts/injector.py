#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pubsub",
#     "sqlmodel>=0.0.38",
#     "timesim",
#     "typer>=0.25.1",
# ]
#
# [tool.uv.sources]
# pubsub = { path = "../libs/pubsub" }
# timesim = { path = "../libs/timesim" }
# ///


"""
injector.py reads a database and injects its contents inside a Redis stream
"""

import asyncio
import datetime as dt
import enum
import uuid
from typing import Annotated, Dict, Optional

import typer
from pubsub import QueueMessage
from pubsub.redis import RedisQueueProducer
from redis.asyncio import Redis
from sqlmodel import (
    JSON,
    Column,
    Enum,
    Field,
    Relationship,
    Session,
    SQLModel,
    col,
    create_engine,
    select,
)
from timesim import TimingMetadata


class ConversationBase(SQLModel):
    # Holds info about the persona and timesimulation config
    meta: Dict = Field(default_factory=dict, sa_column=Column(JSON))


class Conversation(ConversationBase, table=True):
    """Table for a Conversation."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)

    messages: list["Message"] = Relationship(
        back_populates="conversation", cascade_delete=True
    )


class ConversationCreate(ConversationBase):
    """Props to create a Session"""

    pass


class MessageType(str, enum.Enum):
    """Type of messages. Either AI (Server) generated or Human (Cliente) Generated"""

    AI = "ai"
    Human = "human"  # Aksually... it may not be a human but represents a client
    System = "System"


class MessageBase(SQLModel):
    """Base for Message. Holds a conversation, content, type and metadata"""

    conversation_id: uuid.UUID = Field(
        foreign_key="conversation.id", ondelete="CASCADE"
    )
    content: str
    type: MessageType = Field(
        default=MessageType.Human, sa_column=Column(Enum(MessageType))
    )
    timing_metadata: TimingMetadata = Field(
        default_factory=dict, sa_column=Column(JSON)
    )

    # Used to create a timeline
    parent_message_id: uuid.UUID | None = Field(foreign_key="message.id", default=None)


class Message(MessageBase, table=True):
    """Message table on the database"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)
    conversation: Conversation = Relationship(back_populates="messages")
    parent_message: Optional["Message"] = Relationship(
        back_populates="children_messages",
        sa_relationship_kwargs={"remote_side": "Message.id"},
    )
    children_messages: list["Message"] = Relationship(back_populates="parent_message")


class MessageCreate(MessageBase):
    """Props to create a Message"""

    pass


class Touchpoint(SQLModel, table=True):
    """Touchpoint Model"""

    id: int | None = Field(default=None, primary_key=True)
    message_id: uuid.UUID = Field(foreign_key="message.id")
    message: Message = Relationship()
    activity: str

    created_at: dt.datetime = Field(default_factory=dt.datetime.now)

    @property
    def timestamp(self) -> dt.datetime:
        return (
            dt.datetime.fromtimestamp(
                self.message.timing_metadata["simulated_timestamp"]
            )
            or self.message.created_at
        )

    @property
    def conversation_id(self) -> uuid.UUID:
        return self.message.conversation_id


async def main_async(
    db_url: str,
    stream_name: str,
    qnt: int = 100,
    offset: int = 0,
    redis_port: int = 16739,
    type: str = "conversation",
) -> None:
    """injects database data into a Redis Queue."""

    redis_client = Redis(port=redis_port)
    publisher = RedisQueueProducer(redis_client)
    engine = create_engine(db_url)

    with Session(engine) as storage:
        match type:
            case "conversation":
                await injects_conversation(storage, publisher, stream_name, qnt, offset)
            case "touchpoint":
                await injects_touchpoints(storage, publisher, stream_name, qnt, offset)
            case _:
                raise ValueError("Invalid type: " + type)


def main(
    db_url: Annotated[str, typer.Argument()],
    stream_name: Annotated[str, typer.Argument()],
    qnt: Annotated[int, typer.Option()] = 100,
    offset: Annotated[int, typer.Option()] = 0,
    type: Annotated[str, typer.Option()] = "conversation",
    redis_port: Annotated[int, typer.Option()] = 16739,
) -> None:
    """injects database data into a Redis Queue."""

    asyncio.run(main_async(db_url, stream_name, qnt, offset, redis_port, type))


async def injects_conversation(
    storage: Session, publisher: RedisQueueProducer, channel: str, qnt: int, offset: int
):

    conversations = storage.exec(
        select(Conversation)
        .order_by(col(Conversation.created_at))
        .limit(qnt)
        .offset(offset)
    ).all()

    for conv in conversations:
        try:
            payload = QueueMessage(
                origin="injector",
                model_type="conversation",
                content=conv.model_dump(mode="json"),
            )
            await publisher.publish(channel, payload)
            print(f"PUBLISH: {payload}")

            for msg in conv.messages:
                payload = QueueMessage(
                    origin="injector",
                    model_type="message",
                    content=msg.model_dump(mode="json"),
                )
                await publisher.publish(channel, payload)
                print(f"PUBLISH: {payload}")
        except Exception as e:
            print(f"FAILURE: {str(e)}")


async def injects_touchpoints(
    storage: Session, publisher: RedisQueueProducer, channel: str, qnt: int, offset: int
):
    tps = storage.exec(
        select(Touchpoint)
        .order_by(col(Touchpoint.created_at))
        .limit(qnt)
        .offset(offset)
    ).all()

    for tp in tps:
        try:
            payload = QueueMessage(
                origin="injector",
                model_type="touchpoint",
                content=tp.model_dump(mode="json"),
            )
            await publisher.publish(channel, payload)
            print(f"PUBLISH: {payload}")
        except Exception as e:
            print(f"FAILURE: {str(e)}")


if __name__ == "__main__":
    typer.run(main)
