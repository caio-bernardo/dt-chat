import datetime as dt
from typing import Any, Sequence

from chatbot import HumanMessage
from fastapi import HTTPException
from pydantic import UUID4
from sqlmodel import Session as DBSession
from sqlmodel import col, desc, select

from .agent import BancoAgent
from .models import (
    Message,
    MessageCreate,
    MessageType,
    Session,
    SessionCreate,
    TimingMetadata,
    TimingMetadataCreatePublic,
)


class IStorage:
    async def arcv(self, source: str) -> Any: ...

    async def asend(self, dst: str, origin: str, value: Any): ...


class BancoBotService:
    """BancoBot' service to create a new agent with special prompt engeneering."""

    def __init__(self, agent: BancoAgent, storage: DBSession, r: IStorage):
        self.agent = agent
        self.storage = storage
        self.redis = r
        self.msg_stream = "msg_chan"

    async def create_session(self, props: SessionCreate) -> Session:
        """Create a session, holds messages and metadata of a conversation"""
        session = Session.model_validate(props)
        self.storage.add(session)
        self.storage.commit()
        self.storage.refresh(session)

        return session

    async def get_all_sessions(self) -> Sequence[Session]:
        """Retrieve all sessions"""
        try:
            return self.storage.exec(
                select(Session).order_by(col(Session.created_at))
            ).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def fetch_session(self, id: int) -> Session:
        """Fecth a single session"""

        session = self.storage.get(Session, id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    async def delete_session(self, id: int) -> None:
        """Delete a session, also cascading their messages"""

        session = self.storage.get(Session, id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        self.storage.delete(session)
        self.storage.commit()

    async def create_message(self, props: MessageCreate) -> Message:
        """Create a message of bancobot, answering a previous message."""
        try:
            message = await self.save_and_publish_message(props, props.timing_metadata)

            start = dt.datetime.now()
            # LLM call
            answer = self.agent.process_message(
                str(message.session_id),
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

    async def get_messages_by_session(self, session_id: int) -> Sequence[Message]:
        """Get a specific message by its ID."""
        return self.storage.exec(
            select(Message).where(Message.session_id == session_id)
        ).all()

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

    async def publish(self, msg: Message):
        """Publish a Message to a internal channel as json string."""
        await self.redis.asend(
            self.msg_stream, "real", {"payload": msg.model_dump_json()}
        )

    async def subscribe_and_yield(self, request):
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

                msg = await self.redis.arcv(self.msg_stream)

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
