from typing import Sequence

from bancobot.database import MessageType
from bancobot.models import Message
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from sqlmodel import Session, col, select
from userbot import TimeSimulationConfig


def load_history(session_id: int, limit: int) -> Sequence[Message]:
    return []


def map_internal_2_langchain_message(msg: Message) -> AnyMessage:
    match msg.type:
        case MessageType.AI:
            return AIMessage(content=msg.content)
        case MessageType.Human:
            return HumanMessage(
                content=msg.content,
            )
        case MessageType.System:
            return SystemMessage(content=msg.content)


def retrieve_timesim_from_metadata(meta: dict) -> TimeSimulationConfig:
    """Retrive a TimeSimulationConfig from a metadata dictionary"""
    assert "timesim" in meta
    return TimeSimulationConfig.model_validate(meta["timesim"])


def retrieve_userbot_persona_from_metadata(meta: dict) -> str:
    """Retrive the persona prompt from a metadata dictionary"""
    assert "persona" in meta
    return meta["persona"]


def convert_conversation_to_langchain_types(
    raw_conversation: list[Message],
) -> Sequence[AnyMessage]:
    """Retrieve the messages from a given conversation"""
    return [map_internal_2_langchain_message(msg) for msg in raw_conversation]


def retrieve_messages_until(storage: Session, msg: Message) -> list[Message]:
    """Retrieve messages in a conversation from the database until (including) a certain message (id)"""

    conv = storage.exec(
        select(Message)
        .where(Message.conversation_id == msg.conversation_id)
        .where(col(Message.created_at) <= msg.created_at)
        .order_by(col(Message.created_at))
    )
    return list(conv.all())
