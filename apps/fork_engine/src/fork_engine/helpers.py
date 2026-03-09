from typing import Sequence

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage

from bancobot.database import MessageType
from bancobot.models import Message

load_dotenv()

BANCOBOT_URL = "http://localhost:8000"


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
