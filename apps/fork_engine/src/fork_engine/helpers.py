from typing import Dict, Sequence

import requests
from bancobot.agent import BancoAgent
from bancobot.database import MessageType
from bancobot.models import Message
from bancobot.services import BancoBotService, ConversationCreate, MessageCreate
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from pubsub import IPublisher
from sqlmodel import Session
from userbot import IAsyncMessageSender, TimeSimulationConfig

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


def retrieve_conversation_metadata(conversation_id: int) -> dict:
    """Makes a HTTP request to the original Banco Bot to retrieve metadata values from a given conversation"""
    data = requests.get(f"{BANCOBOT_URL}/sessions/{conversation_id}").json()
    meta = data["meta"]
    return meta


def retrieve_timesim_from_metadata(meta: dict) -> TimeSimulationConfig:
    """Retrive a TimeSimulationConfig from a metadata dictionary"""
    assert "timesim" in meta
    return TimeSimulationConfig.model_validate(meta["timesim"])


def retrieve_userbot_persona_from_metadata(meta: dict) -> str:
    """Retrive the persona prompt from a metadata dictionary"""
    assert "persona" in meta
    return meta["persona"]


def retrieve_conversation_messages(conversation_id: int) -> Sequence[AnyMessage]:
    """Retrieve the messages from a given conversation"""
    data = requests.get(f"{BANCOBOT_URL}/sessions/{conversation_id}/messages").json()
    result = []
    for msg in data:
        match msg["type"].lower():
            case "ai":
                result.append(
                    AIMessage(
                        content=msg["content"], timing_metadata=msg["timing_metadata"]
                    )
                )
            case "human":
                result.append(
                    HumanMessage(
                        content=msg["content"], timing_metadata=msg["timing_metadata"]
                    )
                )
            case _:
                pass
    return result


class BancobotProcedureCallSender(IAsyncMessageSender):
    """Bancobot Sender through a procedure call.
    Create a channel and send messages through a bancobot service and
    """

    def __init__(
        self, parent_id: int, agent: BancoAgent, storage: Session, producer: IPublisher
    ):
        self.parent_conversation_id = parent_id
        self.conversation_id = None
        self._service = BancoBotService(agent, storage, producer)
        self._service.source = "twin_bancobot"

    async def create_channel(self, data: Dict | None = None):
        props = ConversationCreate.model_validate(
            {"meta": data or {}, "parent_conversation_id": self.parent_conversation_id}
        )
        conversation = await self._service.create_session(props)
        self.conversation_id = conversation.id

    async def send_message(self, msg: HumanMessage) -> AIMessage:
        if not self.conversation_id:
            raise ValueError("Conversation not created yet")
        props = MessageCreate.model_validate(
            {
                "conversation_id": self.conversation_id,
                "content": str(msg.content),
                "timinig_metadata": msg.timing_metadata or {},  # pyright: ignore[reportAttributeAccessIssue]
            }
        )
        answer = await self._service.save_publish_answer_message(props)
        return AIMessage(content=answer.content, timing_metadata=answer.timing_metadata)
