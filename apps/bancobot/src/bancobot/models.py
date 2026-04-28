import datetime as dt
import enum
import uuid
from typing import Dict, Optional

from sqlmodel import JSON, Column, Enum, Field, Relationship, SQLModel
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


class ConversationPublic(ConversationBase):
    """Public view of a Conversation"""

    id: uuid.UUID
    created_at: dt.datetime


class ConversationPublicWithMessages(ConversationPublic):
    """Public view of a Conversation with list of messages"""

    messages: list["MessagePublic"]


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


class MessagePublic(MessageBase):
    """Public view of a Message"""

    id: int
    created_at: dt.datetime


class MessagePublicWithConversation(MessageBase):
    """Public Message Without Conversation data"""

    id: int
    created_at: dt.datetime
    conversation: ConversationPublic


class MessagePublicWithParent(MessageBase):
    id: int
    created_at: dt.datetime
    parent: Optional[MessagePublicWithConversation] = None


class MessagePublicComplete(MessageBase):
    id: int
    created_at: dt.datetime
    conversation: ConversationPublic
    parent: Optional[MessagePublicWithConversation] = None


class MessageCreate(MessageBase):
    """Props to create a Message"""

    pass
