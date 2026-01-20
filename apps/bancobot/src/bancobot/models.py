import datetime as dt
import enum
import uuid
from typing import Optional

from pydantic import UUID4
from sqlmodel import Column, Enum, Field, Relationship, SQLModel


class TimingMetadata(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    simulated_timestamp: dt.datetime
    typing_time: float
    pause_time: float
    thinking_time: float


class TimingMetadataCreatePublic(SQLModel):
    simulated_timestamp: dt.datetime
    typing_time: float
    pause_time: float
    thinking_time: float


class MessageType(str, enum.Enum):
    AI = "ai"
    Human = "human"  # Aksually... it may not be a human but represents a client


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: UUID4 = Field(default_factory=uuid.uuid4)
    content: str
    type: MessageType = Field(
        default=MessageType.Human, sa_column=Column(Enum(MessageType))
    )

    timing_metadata_id: Optional[int] = Field(
        default=None, foreign_key="timingmetadata.id"
    )
    timing_metadata: Optional[TimingMetadata] = Relationship()
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)


class MessagePublic(SQLModel):
    id: int
    session_id: UUID4
    content: str
    type: MessageType
    timing_metadata: Optional[TimingMetadataCreatePublic]
    created_at: dt.datetime


class MessageCreate(SQLModel):
    session_id: Optional[UUID4] = None
    content: str
    timing_metadata: Optional[TimingMetadataCreatePublic] = None
