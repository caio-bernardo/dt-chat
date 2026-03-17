import datetime as dt
import json
from typing import Any, Dict

import redis.asyncio as redis
import redis.exceptions as redis_exceptions
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


class StreamService:
    """Stream Service. Allows to publish and subscribe to channels"""

    def __init__(self, redis: redis.Redis, channel: str) -> None:
        self.redis = redis
        self.consumer_group = "touchpoint_group"
        self.consumer_name = "classifier"
        self.stream = channel
        # Needs to create a group so it can difer from processed and unprocessed messages with ack.

    async def _create_group(self, starting_point: str = "$"):
        """Auxiliary function to create a new redis group to process messages
        Reads from a Redis stream starting from:
            0 - oldest message
            $ - new messages beggining now
        """
        try:
            # Creates new group
            await self.redis.xgroup_create(
                self.stream, self.consumer_group, id=starting_point, mkstream=True
            )
        except redis_exceptions.ResponseError as e:
            # Ignores if the group already exists.
            if "BUSYGROUP" not in str(e):
                raise e

    async def subscribe(self) -> tuple[str, dict[str, Any]]:
        """Subscribe to a channel, this function yields new messages. Blocks execution waiting for new messages"""
        response = await self.redis.xreadgroup(
            self.consumer_group,
            self.consumer_name,
            {self.stream: ">"},
            count=1,
            block=0,
        )
        # retrieves message id and payload from the nested response
        id = response[0][1][0][0]
        bpayload = response[0][1][0][1][b"payload"]
        # double loads because the first makes a string with "" inside, the second actually produces the json
        obj = json.loads(json.loads(bpayload))
        assert type(obj) is dict  # just a type check to make sure we got a object
        return (id, obj)

    async def acknowledge(self, msg_id: str):
        """Acknowledges the message received by `subscribe`. Or else the message may repeatedly come again."""
        await self.redis.xack(self.stream, self.consumer_group, msg_id)

    async def publish(self, channel_name: str, data: Dict):
        """Publish a data to a channel. This function serializes data to a json string."""
        self.redis.xadd(channel_name, {"payload": json.dumps(data)})
