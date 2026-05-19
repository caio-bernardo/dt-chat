import uuid
from typing import Dict

from bancobot.agent import BancoAgent
from bancobot.models import ConversationCreate, MessageCreate
from bancobot.services import BancoBotService
from chatbot import AIMessage, HumanMessage
from pubsub import IPublisher
from sqlmodel import Session
from userbot.user import IAsyncMessageSender


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
