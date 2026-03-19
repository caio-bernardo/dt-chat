import datetime as dt
import json
from typing import Dict, Sequence, TypedDict

from chatbot import HumanMessage
from fastapi import HTTPException
from pubsub import IPublisher
from sqlmodel import Session as DBSession
from sqlmodel import col, desc, select

from .agent import BancoAgent
from .models import (
    Conversation,
    ConversationCreate,
    Message,
    MessageCreate,
    MessageType,
    TimingMetadata,
)


class QueueMessage(TypedDict):
    origin: str
    content: Dict


def create_simulated_timestamp_or_default(
    user_metadata: TimingMetadata | None, delta
) -> TimingMetadata:
    """Create a Simulated Timestamp for the Bancobot from the user metadata, or returns a default if the previous component is None."""
    # Usamos o timestamp da pergunta + tempo para produzir resposta do BancoBot como timestamp do bancobot
    if not user_metadata:
        new_sim_tmstp = dt.datetime.now + delta
    else:
        new_sim_tmstp = (
            dt.datetime.fromtimestamp(user_metadata["simulated_timestamp"]) + delta
        )
    return {
        "simulated_timestamp": new_sim_tmstp.timestamp(),
        "pause_time": 0,
        "typing_time": 0,
        "thinking_time": 0,
    }


class BancoBotService:
    """BancoBot' service to create a new agent with special prompt engeneering."""

    def __init__(
        self, agent: BancoAgent, storage: DBSession, producer_service: IPublisher
    ):
        self.agent = agent
        self.storage = storage
        self.producer = producer_service
        self.channel = "msg_channel"

    async def create_session(self, props: ConversationCreate) -> Conversation:
        """Create a session, holds messages and metadata of a conversation"""
        session = Conversation.model_validate(props)
        self.storage.add(session)
        self.storage.commit()
        self.storage.refresh(session)

        return session

    async def get_all_sessions(self) -> Sequence[Conversation]:
        """Retrieve all sessions"""
        try:
            return self.storage.exec(
                select(Conversation).order_by(col(Conversation.created_at))
            ).all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def fetch_session(self, id: int) -> Conversation:
        """Fecth a single session"""

        session = self.storage.get(Conversation, id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

    async def delete_session(self, id: int) -> None:
        """Delete a session, also cascading their messages"""

        session = self.storage.get(Conversation, id)
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
                str(message.conversation_id),
                HumanMessage(message.content, timing_metadata=props.timing_metadata),
            )
            answer_delta = dt.datetime.now() - start
            answer_metadata = create_simulated_timestamp_or_default(
                message.timing_metadata, answer_delta
            )
            payload = MessageCreate(
                conversation_id=message.conversation_id,
                content=str(answer.content),
                type=MessageType.AI,
                timing_metadata=answer_metadata,
            )

            print(f"INFO: {payload}")

            return await self.save_and_publish_message(payload, answer_metadata)
        except Exception as e:
            raise e

    async def get_messages_by_conversation(self, session_id: int) -> Sequence[Message]:
        """Get a specific message by its ID."""
        return self.storage.exec(
            select(Message).where(Message.conversation_id == session_id)
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
        self, session_id: int, limit: int = 10
    ) -> Sequence[Message]:
        """Get recent messages for a session."""
        try:
            messages = self.storage.exec(
                select(Message)
                .where(Message.conversation_id == session_id)
                .order_by(desc(Message.created_at))
                .limit(limit)
            ).all()
            return messages
        except Exception as e:
            raise e

    async def publish(self, msg: Message):
        """Publish a Message to a internal channel as json string."""
        try:
            # uses json mode to parse datetime into isoformat
            payload: QueueMessage = {
                "origin": "bancobot",
                "content": msg.model_dump(mode="json"),
            }
            await self.producer.publish(self.channel, json.dumps(payload))
        except Exception as e:
            print(
                f"[{dt.datetime.now()}] WARN: failed to publish message to queue. Detail: {str(e)}"
            )

    def save_message(
        self,
        props: MessageCreate,
        timing_metadata: TimingMetadata,
    ) -> Message:
        """Saves Message to Storage"""

        message = Message(
            conversation_id=props.conversation_id,
            content=props.content,
            type=props.type,
            timing_metadata=timing_metadata,
        )
        self.storage.add(message)
        self.storage.commit()
        self.storage.refresh(message)
        return message

    async def save_and_publish_message(
        self,
        props: MessageCreate,
        timing_metadata: TimingMetadata,
    ) -> Message:
        """Save Message to Storage and Publish to Cache Channel."""
        msg = self.save_message(props, timing_metadata)
        await self.publish(msg)
        return msg
