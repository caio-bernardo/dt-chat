import datetime as dt
import enum
import uuid
from typing import Dict, Optional

from sqlmodel import JSON, Column, Enum, Field, Relationship, SQLModel
from timesim import TimingMetadata


class ConversationBase(SQLModel):
    # Holds info about the persona and timesimulation config
    meta: Dict = Field(default_factory=dict, sa_column=Column(JSON))

    # Used only by the fork_engine
    parent_conversation_id: uuid.UUID | None = Field(
        default=None, foreign_key="conversation.id", nullable=True
    )


class Conversation(ConversationBase, table=True):
    """Table for a Conversation."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)

    parent_conversation: Optional["Conversation"] = Relationship(
        back_populates="children_conversations",
        sa_relationship_kwargs={"remote_side": "Conversation.id"},
    )
    children_conversations: list["Conversation"] = Relationship(
        back_populates="parent_conversation"
    )
    messages: list["Message"] = Relationship(
        back_populates="conversation", cascade_delete=True
    )


class ConversationPublic(ConversationBase):
    """Public view of a Conversation"""

    id: uuid.UUID
    parent_conversation: Optional["ConversationPublic"] = None
    children_conversations: list["ConversationPublic"]
    created_at: dt.datetime


class ConversationPublicWithMessages(ConversationPublic):
    """Public view of a Conversation with list of messages"""

    messages: list["MessagePublicWithoutConversation"]


class ConversationCreate(ConversationBase):
    """Props to create a Session"""

    pass


class MessageType(str, enum.Enum):
    """Type of messages. Either AI (Server) generated or Human (Cliente) Generated"""

    AI = "ai"
    Human = "human"  # Aksually... it may not be a human but represents a client


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


class Message(MessageBase, table=True):
    """Message table on the database"""

    id: int | None = Field(default=None, primary_key=True)
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)
    conversation: Conversation = Relationship(back_populates="messages")


class MessagePublic(MessageBase):
    """Public view of a Message"""

    id: int
    conversation: ConversationPublic
    created_at: dt.datetime


class MessagePublicWithoutConversation(MessageBase):
    """Public Message Without Conversation data"""

    created_at: dt.datetime
    id: int


class MessageCreate(MessageBase):
    """Props to create a Message"""

    pass
