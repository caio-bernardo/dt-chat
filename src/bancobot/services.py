from typing import Sequence

from pydantic import UUID4
from sqlmodel import Session, desc, select

from .agent import BancoAgent, HumanMessage
from .models import Message, MessageCreate, MessageType


class BancoBotService:
    """BancoBot' service to create a new agent with special prompt engeneering."""

    def __init__(self, agent: BancoAgent, storage: Session):
        self.agent = agent
        self.storage = storage

    async def create_message(self, props: MessageCreate) -> Message:
        try:
            message = Message(**props.model_dump())
            self.storage.add(message)
            self.storage.commit()
            answer = self.agent.process_message(
                message.session_id, HumanMessage(message.content)
            )
            result = Message(
                session_id=message.session_id,
                content=str(answer.content),
                type=MessageType.AI,
            )
            self.storage.add(result)
            self.storage.commit()
            self.storage.refresh(result)
            return result
        except Exception as e:
            raise e

    async def get_message_by_session(self, id: UUID4) -> Sequence[Message]:
        """Get all messages for a specific session."""
        try:
            return self.storage.exec(
                select(Message).where(Message.session_id == id)
            ).all()
        except Exception as e:
            raise e

    async def get_all_sessions(self) -> Sequence[UUID4]:
        """Get all unique session IDs."""
        try:
            return self.storage.exec(select(Message.session_id).distinct()).all()
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
