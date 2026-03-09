import datetime as dt
import enum
from typing import Dict, Optional

from sqlmodel import JSON, Column, Enum, Field, Relationship, SQLModel


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


class Session(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    # Holds persona information
    # TODO: may replace by a user profile
    meta: Dict = Field(default_factory=dict, sa_column=Column(JSON))

    created_at: dt.datetime = Field(default_factory=dt.datetime.now)
    # Used only by the fork_engine
    parent_conversation_id: int | None = Field(default=None, foreign_key="session.id")
    parent_conversation: Optional["Session"] = Relationship()


class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id", ondelete="CASCADE")
    session: Session = Relationship(back_populates="messages")

    content: str
    type: MessageType = Field(
        default=MessageType.Human, sa_column=Column(Enum(MessageType))
    )

    timing_metadata_id: Optional[int] = Field(
        default=None, foreign_key="timingmetadata.id"
    )
    timing_metadata: Optional[TimingMetadata] = Relationship()
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)


class SessionWithMessages(Session, table=False):
    messages: list["Message"] = Relationship(
        back_populates="session", cascade_delete=True
    )


class SessionCreate(SQLModel):
    """Props to create a Session"""

    meta: Dict
    parent_conversation_id: int | None = None


class MessageCreate(SQLModel):
    """Props to create a Message"""

    session_id: int
    content: str
    type: MessageType = Field(default=MessageType.Human)
    timing_metadata: Optional[TimingMetadataCreatePublic] = None
