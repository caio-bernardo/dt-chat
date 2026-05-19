import asyncio
import threading
import uuid
from concurrent.futures import Future
from typing import Any, Callable, Dict, Sequence

from bancobot.agent import BancoAgent
from bancobot.database import MessageType
from bancobot.models import Message
from bancobot.services import BancoBotService, ConversationCreate, MessageCreate
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from pubsub import IPublisher
from sqlmodel import Session
from userbot import IAsyncMessageSender, TimeSimulationConfig

load_dotenv()


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
    result = []
    for msg in raw_conversation:
        match msg.type:
            case MessageType.AI:
                result.append(
                    AIMessage(content=msg.content, timing_metadata=msg.timing_metadata)
                )
            case MessageType.Human:
                result.append(
                    HumanMessage(
                        content=msg.content, timing_metadata=msg.timing_metadata
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
        self,
        parent_id: uuid.UUID,
        agent: BancoAgent,
        storage: Session,
        producer: IPublisher,
        metadata: Dict | None = None,
    ):
        self.parent_conversation_id = parent_id
        self.conversation_id = None
        self._service = BancoBotService(agent, storage, producer)
        self._service.source = "twin_bancobot"
        self._metadata = metadata

    async def create_channel(self, data: Dict | None = None):
        if self._metadata and data:
            data.update(self._metadata)
        props = ConversationCreate.model_validate(
            {"meta": data or {}, "parent_conversation_id": self.parent_conversation_id}
        )
        conversation = await self._service.create_session(props)
        self.conversation_id = conversation.id

    async def send_message(self, msg: HumanMessage) -> AIMessage:
        if not self.conversation_id:
            raise ValueError("Conversation not created yet")
        assert msg.timing_metadata, ValueError(  # pyright: ignore[reportAttributeAccessIssue]
            "no timing metadata attached to human msg"
        )
        props = MessageCreate(
            conversation_id=self.conversation_id,
            content=str(msg.content),
            timing_metadata=msg.timing_metadata,  # pyright: ignore[reportAttributeAccessIssue]
        )
        answer = await self._service.save_publish_answer_message(props)
        return AIMessage(content=answer.content, timing_metadata=answer.timing_metadata)


def run_async_thread(async_func: Callable[..., Any], *args, **kwargs) -> Any:
    fut = Future()

    def _runnet():
        try:
            res = asyncio.run(async_func(*args, **kwargs))
            fut.set_result(res)
        except Exception as e:
            fut.set_exception(e)

    thread = threading.Thread(target=_runnet)
    thread.start()
    return fut
