#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "timesim",
#     "sqlmodel>=0.0.38",
#     "typer>=0.21.2",
# ]
#
# [tool.uv.sources]
# timesim = { path = "../libs/timesim" }
# ///

import datetime as dt
import enum
import json
import random
import uuid
from typing import Dict, Optional

import typer
from sqlmodel import (
    JSON,
    Column,
    Enum,
    Field,
    Relationship,
    Session,
    SQLModel,
    create_engine,
)
from timesim import TimeSimulationConfig, TimingMetadata

PERSONAS_FILE: str = "data/personas.json"

PAUSE_PROBABILITY: float = 0.05
PAUSE_TIME_RANGE_S: tuple[float, float] = (60.0, 3600.0)


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


def get_typing_speed_and_thinking_range(duration: str) -> tuple[float, tuple[int, int]]:
    match duration:
        case "lenta":
            typing_speed = random.uniform(10, 24)
            thinking_range = (8, 35)
        case "media":
            typing_speed = random.uniform(25, 54)
            thinking_range = (2, 12)
        case "rapida":
            typing_speed = random.uniform(55, 90)
            thinking_range = (2, 7)
        case _:
            typing_speed = random.uniform(25, 54)
            thinking_range = (2, 12)
    return typing_speed, thinking_range


def create_persona_metadata_from_name(name: str, temporal_offset: dt.timedelta):
    with open(PERSONAS_FILE, "r", encoding="utf-8") as f:
        personas = json.load(f)
        id = name[-1]
        data = personas[id]

        typing_speed, thinking_range = get_typing_speed_and_thinking_range(
            data["duração"]
        )

        return {
            "persona": str(data["persona"]),
            "timesim": TimeSimulationConfig(
                temporal_offset=temporal_offset,
                pause_probability=PAUSE_PROBABILITY,
                pause_time_range=PAUSE_TIME_RANGE_S,
                typing_speed_wpm=typing_speed,
                thinking_time_range=thinking_range,
                simulate_delays=False,
            ).model_dump(mode="json"),
        }


def calculate_temporal_offset(data):
    current_time = dt.datetime.fromisoformat(
        data["messages"][0]["simulated_timestamp"]
    ).astimezone()
    initial_time = dt.datetime.fromisoformat(
        data["conversation_timestamp"]
    ).astimezone()
    return current_time - initial_time


def main(
    input_file_path: str, db_conn: str = "sqlite:///messages.db", quiet: bool = False
) -> None:
    """
    Import conversations and touchpoints from json files into a SQL database.
    """
    if not quiet:
        print("Initializing export")
    try:
        engine = create_engine(db_conn)
        SQLModel.metadata.create_all(engine)
        session = Session(engine)

        # DONE: read a json file
        with open(input_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # DONE: create metadata for a conversation
        temporal_offset = calculate_temporal_offset(data)
        metadata = create_persona_metadata_from_name(
            data["persona_id"], temporal_offset
        )
        # DONE: create a conversation
        props = ConversationCreate(meta=metadata)
        conversation = Conversation.model_validate(props)

        if not quiet:
            print(f"Adding Conversation: {conversation}")
        session.add(conversation)

        # DONE: iterate over messages
        previous_message_id = None
        for message_data in data["messages"]:
            # DONE: create values for the messages
            if message_data["type"] == "human":
                pause_time = message_data["timing_metadata"]["break_time"]
                typing_time = message_data["timing_metadata"]["typing_time"]
                thinking_time = message_data["timing_metadata"]["thinking_time"]
            else:
                pause_time = 0.0
                typing_time = 0.0
                thinking_time = 0.0

            props = MessageCreate(
                conversation_id=conversation.id,
                content=message_data["content"],
                type=message_data["type"],
                timing_metadata=TimingMetadata(
                    simulated_timestamp=dt.datetime.fromisoformat(
                        message_data["timing_metadata"].get("simulated_timestamp")
                        or message_data["timing_metadata"].get(
                            "banco_generation_timestamp"
                        )
                        or message_data["simulated_timestamp"]
                    ).timestamp(),
                    pause_time=pause_time,
                    typing_time=typing_time,
                    thinking_time=thinking_time,
                ),
                parent_message_id=previous_message_id,
            )

            msg = Message.model_validate(props)
            if not quiet:
                print(f"Adding Message: {msg}")
            session.add(msg)
            previous_message_id = msg.id

        # DONE: save everything on the database
        session.commit()
    except Exception as err:
        print(f"ERROR: {str(err)}")
        raise err


if __name__ == "__main__":
    typer.run(main)
