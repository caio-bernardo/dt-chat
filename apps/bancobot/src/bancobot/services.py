import asyncio
from asyncio import Queue
from typing import Sequence

from chatbot import HumanMessage
from pydantic import UUID4
from sqlmodel import Session, col, desc, select

from .agent import BancoAgent
from .models import Message, MessageCreate, MessageType, TimingMetadata


class BancoBotService:
    """BancoBot' service to create a new agent with special prompt engeneering."""

    def __init__(self, agent: BancoAgent, storage: Session):
        self.agent = agent
        self.storage = storage
        self.subscribers: set[Queue[Message]] = set()

    async def create_message(self, props: MessageCreate) -> Message:
        """Create a message of bancobot, answering a previous message."""
        try:
            timing_metadata = (
                TimingMetadata(**props.timing_metadata.model_dump())
                if props.timing_metadata
                else None
            )
            message = Message(
                session_id=props.session_id,  # pyright: ignore[reportArgumentType]
                content=props.content,
                type=MessageType.Human,
                timing_metadata=timing_metadata,
            )
            self.storage.add(message)
            self.storage.commit()

            # LLM call
            answer = self.agent.process_message(
                message.session_id,
                HumanMessage(message.content, timing_metadata=props.timing_metadata),
            )

            # Usamos o mesmo timestamp da pergunta para o BancoBot
            answer_metadata = (
                TimingMetadata(
                    simulated_timestamp=message.timing_metadata.simulated_timestamp,
                    pause_time=0,
                    typing_time=0,
                    thinking_time=0,
                )
                if message.timing_metadata
                else None
            )

            result = Message(
                session_id=message.session_id,
                content=str(answer.content),
                type=MessageType.AI,
                timing_metadata=answer_metadata,
            )
            self.storage.add(result)
            self.storage.commit()
            self.storage.refresh(result)
            return result
        except Exception as e:
            raise e

    async def get_message_by_session(self, id: UUID4) -> Sequence[Message]:
        """Get all messages for a specific session, orderer by time of creation, older first."""
        try:
            return self.storage.exec(
                select(Message)
                .order_by(col(Message.created_at))
                .where(Message.session_id == id)
            ).all()
        except Exception as e:
            raise e

    async def get_all_sessions(self) -> Sequence[UUID4]:
        """Get all unique session IDs."""
        try:
            return self.storage.exec(
                select(Message.session_id).distinct().order_by(col(Message.created_at))
            ).all()
        except Exception as e:
            raise e

    async def delete_messages_by_session(self, id: UUID4) -> int:
        """Delete all messages for a specific session. Returns count of deleted messages."""
        try:
            messages = await self.get_message_by_session(id)
            for message in messages:
                if message.id is not None:
                    await self.delete_message_by_id(message.id)
            return len(messages)
        except Exception as e:
            raise e

    async def get_message_by_id(self, message_id: int) -> Message:
        """Get a specific message by its ID."""
        try:
            message = self.storage.get(Message, message_id)
            if message is None:
                raise ValueError(f"Message with ID {message_id} not found")
            return message
        except Exception as e:
            raise e

    async def delete_message_by_id(self, message_id: int) -> bool:
        """Delete a specific message by its ID."""
        try:
            msg = self.storage.get(Message, message_id)
            self.storage.delete(msg)
            self.storage.commit()
            return self.storage.get(Message, message_id) is None
        except Exception as e:
            raise e

    async def get_messages(self) -> Sequence[Message]:
        """Fetches all messages from the chatbot."""
        try:
            messages = self.storage.exec(select(Message)).all()
            return messages
        except Exception as e:
            raise e

    async def get_recent_messages(
        self, session_id: UUID4, limit: int = 10
    ) -> Sequence[Message]:
        """Get recent messages for a session."""
        try:
            messages = self.storage.exec(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(desc(Message.created_at))
                .limit(limit)
            ).all()
            return messages
        except Exception as e:
            raise e

    def subscribe(self, subscriptor: Queue):
        self.subscribers.add(subscriptor)

    def unsubscribe(self, subscriptor: Queue):
        self.subscribers.remove(subscriptor)

    async def publish(self, msg: Message):
        if self.subscribers:
            await asyncio.gather(
                *[subscriptor.put(msg) for subscriptor in self.subscribers]
            )

    async def create_and_publish_message(self, props: MessageCreate) -> Message:
        created_message = await self.create_message(props)
        await self.publish(created_message)
        return created_message
