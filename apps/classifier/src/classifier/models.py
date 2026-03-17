import datetime as dt
import enum

from bancobot.models import MessageType
from sqlmodel import Column, Enum, Field, SQLModel


class ActorType(str, enum.Enum):
    """Represent Actor in a message"""

    SYSTEM = "System"
    AI = "AI"
    HUMAN = "Human"


def from_message_type(type: MessageType) -> ActorType:
    """Converts from a MessageType to an ActorType so it can be used in the Touchpoint"""
    match type:
        case MessageType.Human:
            return ActorType.HUMAN
        case MessageType.AI:
            return ActorType.AI
        case _:
            raise ValueError(f"Invalid message type: {type}")


class Touchpoint(SQLModel, table=True):
    """Touchpoint Model"""

    id: int | None = Field(default=None, primary_key=True)
    session_id: int
    internal_id: int
    actor: ActorType = Field(
        default=ActorType.SYSTEM, sa_column=Column(Enum(ActorType))
    )
    message_id: int
    message: str
    timestamp: dt.datetime
    activity: str

    created_at: dt.datetime = Field(default_factory=dt.datetime.now)
