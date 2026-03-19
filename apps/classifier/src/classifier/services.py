import datetime as dt

from bancobot.models import Message
from sqlmodel import Session, col, func, select

from classifier.agent import ClassifierAgent
from classifier.models import Touchpoint, from_message_type


class ClassifierService:
    """Classifier Service manages the creation and saving of any touchpoint."""

    def __init__(self, agent: ClassifierAgent, storage: Session):
        self.agent = agent
        self.storage = storage

    def _get_last_internal_id(self, case_id: int) -> int:
        """Returns the last used internal id from a case (equivalent for the number of messages in the case/conversation/session)"""
        return self.storage.exec(
            select(func.count(col(Touchpoint.session_id))).where(
                Touchpoint.session_id == case_id
            )
        ).one()

    async def create_touchpoint(
        self, msg: Message, actor: str, tp_list: list[str]
    ) -> Touchpoint:
        """Creates a new touchpoint requesting to the agent"""
        last_internal_id = self._get_last_internal_id(msg.conversation_id)

        touchpoint = await self.agent.classify(msg.content, actor, tp_list)

        case_id = msg.conversation_id
        timestamp = (
            dt.datetime.fromtimestamp(msg.timing_metadata["simulated_timestamp"])
            if msg.timing_metadata
            else msg.created_at
        )
        return Touchpoint(
            session_id=case_id,
            internal_id=last_internal_id + 1,
            actor=from_message_type(msg.type),
            message_id=msg.id or -1,
            message=msg.content,
            activity=touchpoint,
            timestamp=timestamp,
        )

    def save_touchpoint(self, touchpoint: Touchpoint):
        """Saves a touchpoint on the database"""
        self.storage.add(touchpoint)
        self.storage.commit()
        self.storage.refresh(touchpoint)

    async def create_and_save_touchpoint(
        self, msg: Message, actor: str, tp_list: list[str]
    ) -> Touchpoint:
        """Both creates and saves the touchpoint, see associated functions above."""
        tp = await self.create_touchpoint(msg, actor, tp_list)
        self.save_touchpoint(tp)
        return tp
