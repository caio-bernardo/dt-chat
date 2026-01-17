import datetime as dt
import enum
import uuid
from typing import Optional

from pydantic import UUID4
from sqlmodel import Column, Enum, Field, SQLModel


class MessageType(str, enum.Enum):
    AI = "ai"
    Human = "Human"  # Aksually... it may not be a human but represents a client


class TimingMetadata(SQLModel, table=False):
    typing_time: float
    pause_time: float
    thinking_time: float


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: UUID4 = Field(default_factory=uuid.uuid4)
    content: str
    type: MessageType = Field(
        default=MessageType.Human, sa_column=Column(Enum(MessageType))
    )

    created_at: dt.datetime = Field(default_factory=dt.datetime.now)


class MessageCreate(SQLModel):
    session_id: Optional[UUID4] = None
    content: str
    timing_metadata: Optional[TimingMetadata] = None
