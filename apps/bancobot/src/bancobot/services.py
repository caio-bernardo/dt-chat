import datetime as dt
from typing import Sequence

import redis.asyncio as redis
from chatbot import HumanMessage
from pydantic import UUID4
from sqlmodel import Session, col, desc, select

from .agent import BancoAgent
from .models import (
    Message,
    MessageCreate,
    MessageType,
    TimingMetadata,
    TimingMetadataCreatePublic,
)


class BancoBotService:
    """BancoBot' service to create a new agent with special prompt engeneering."""

    def __init__(self, agent: BancoAgent, storage: Session, r: redis.Redis):
        self.agent = agent
        self.storage = storage
        self.redis = r
        self.msg_stream = "msg_chan"

    async def create_message(self, props: MessageCreate) -> Message:
        """Create a message of bancobot, answering a previous message."""
        try:
            message = await self.save_and_publish_message(props, props.timing_metadata)

            start = dt.datetime.now()
            # LLM call
            answer = self.agent.process_message(
                message.session_id,
                HumanMessage(message.content, timing_metadata=props.timing_metadata),
            )
            answer_delta = dt.datetime.now() - start

            # Usamos o timestamp da pergunta + tempo para produzir resposta do BancoBot
            answer_metadata = (
                TimingMetadataCreatePublic(
                    simulated_timestamp=message.timing_metadata.simulated_timestamp
                    + answer_delta,
                    pause_time=0,
                    typing_time=0,
                    thinking_time=0,
                )
                if message.timing_metadata
                else None
            )

            payload = MessageCreate(
                session_id=message.session_id,
                content=str(answer.content),
                type=MessageType.AI,
                timing_metadata=answer_metadata,
            )

            return await self.save_and_publish_message(payload, answer_metadata)
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

    async def publish(self, msg: Message):
        """Publish a Message to a internal channel as json string."""
        await self.redis.xadd(self.msg_stream, {"payload": msg.model_dump_json()})

    async def subscribe_and_yield(self, request, start_from="$"):
        """Subscribe for new messages through Redis and Yield New Messages.
        Takes a Request and checks if the connection still exists, or else stop
        listening.

        start_from="0": Read from the begginig of messages history
        start_from"$": Read only new messages since now.
        """
        try:
            while True:
                if await request.is_disconnected():
                    break

                msg = await self.redis.xread(
                    {self.msg_stream: start_from}, count=1, block=1000
                )

                if msg:
                    yield {"data": msg["payload"]}
        finally:
            pass

    def save_message(
        self,
        props: MessageCreate,
        timing_metadata: TimingMetadataCreatePublic | None = None,
    ) -> Message:
        """Saves Message to Storage"""
        metadata = TimingMetadata.model_validate(timing_metadata)

        message = Message(
            session_id=props.session_id,  # pyright: ignore[reportArgumentType]
            content=props.content,
            type=MessageType.Human,
            timing_metadata=metadata,
        )
        self.storage.add(message)
        self.storage.commit()
        self.storage.refresh(message)
        return message

    async def save_and_publish_message(
        self,
        props: MessageCreate,
        timing_metadata: TimingMetadataCreatePublic | None = None,
    ) -> Message:
        """Save Message to Storage and Publish to Cache Channel."""
        msg = self.save_message(props, timing_metadata)
        await self.publish(msg)
        return msg
