from sqlmodel import Session

from classifier.agent import ClassifierAgent
from classifier.models import Conversation, Message, Touchpoint


class ClassifierService:
    """Classifier Service manages the creation and saving of any touchpoint."""

    def __init__(self, agent: ClassifierAgent, storage: Session):
        self.agent = agent
        self.storage = storage

    async def create_touchpoint(
        self, msg: Message, actor: str, tp_list: list[str]
    ) -> Touchpoint:
        """Creates a new touchpoint requesting to the agent"""
        activity = await self.agent.classify(msg.content, actor, tp_list)

        return Touchpoint(
            message_id=msg.id,
            activity=activity,
        )

    def save_conversation(self, conversation: Conversation):
        """Saves a conversation on the database"""
        self.storage.add(conversation)
        self.storage.commit()
        self.storage.refresh(conversation)

    def save_message(self, msg: Message):
        """Saves a message on the database"""
        self.storage.add(msg)
        self.storage.commit()
        self.storage.refresh(msg)

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
