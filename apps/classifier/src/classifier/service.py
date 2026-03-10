import datetime as dt
from typing import Any

import redis.asyncio as redis
from bancobot.models import Message
from sqlmodel import Session, col, func, select

from classifier.agent import ClassifierAgent
from classifier.models import Touchpoint, from_message_type


class ClassifierService:
    def __init__(self, agent: ClassifierAgent, storage: Session, redis: redis.Redis):
        self.agent = agent
        self.storage = storage
        self.redis = redis

    async def read_stream(
        self, stream: str = "msg_chan", start_from: str = "0"
    ) -> dict[str, Any]:
        """Reads from a Redis stream starting from:
        0 - oldest message
        $ - new messages since now
        Blocks execution waiting for new messages
        """
        return await self.redis.xread({stream: start_from}, count=1, block=0)

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
        self.storage.add(touchpoint)
        self.storage.commit()
        self.storage.refresh(touchpoint)

    async def create_and_save_touchpoint(
        self, msg: Message, actor: str, tp_list: list[str]
    ) -> Touchpoint:
        tp = await self.create_touchpoint(msg, actor, tp_list)
        self.save_touchpoint(tp)
        return tp

    async def publish(self, tp: Touchpoint, stream: str = "tp_chan"):
        self.redis.xadd(stream, {"payload": tp.model_dump_json()})
