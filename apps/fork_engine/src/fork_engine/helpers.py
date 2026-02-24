import os
from typing import Sequence

from bancobot.database import MessageType
from bancobot.models import Message
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from pydantic import UUID4
from sqlmodel import Session, col, create_engine, select

load_dotenv()

DB_URL = os.environ["DB_URL"]

engine = create_engine(DB_URL)
storage = Session(engine)


def load_history(session_id: UUID4, limit: int) -> Sequence[Message]:
    try:
        return storage.exec(
            select(Message)
            .order_by(col(Message.created_at))
            .where(Message.session_id == id)
            .limit(limit)
        ).all()
    except Exception as e:
        raise e


def map_internal_2_langchain_message(msg: Message) -> AnyMessage:
    match msg.type:
        case MessageType.AI:
            return AIMessage(content=msg.content)
        case MessageType.Human:
            return HumanMessage(
                content=msg.content,
            )
