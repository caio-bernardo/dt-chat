import datetime as dt
import uuid

# Usado para criar a tabela Messages no lado do classificador
from bancobot.models import (
    Conversation,  # pyright: ignore[reportUnusedImport]
    Message,
)
from sqlmodel import Field, Relationship, SQLModel


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
