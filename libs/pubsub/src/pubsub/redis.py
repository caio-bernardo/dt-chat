import json
import os
import socket

import redis.asyncio as redis
from redis.exceptions import ResponseError

from pubsub.interfaces import IPublisher, ISubscriber, QueueMessage


class RedisQueueProducer(IPublisher):
    """Redis Streams producer."""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def publish(self, channel: str, message: QueueMessage):
        await self.redis_client.xadd(channel, {"payload": json.dumps(message)})  # pyright: ignore[reportGeneralTypeIssues]


class RedisQueueConsumer(ISubscriber):
    """Redis Streams consumer-group reader with at-least-once delivery."""

    def __init__(
        self,
        redis_client: redis.Redis,
        group: str = "default",
        consumer_name: str | None = None,
        reclaim_idle_ms: int = 60_000,
    ):
        self.redis_client = redis_client
        self.group = group
        self.consumer_name = consumer_name or f"{socket.gethostname()}-{os.getpid()}"
        self.reclaim_idle_ms = reclaim_idle_ms
        self._subscribed_channels: set[str] = set()
        self._pending: dict[int, tuple[str, str]] = {}

    async def _ensure_group(self, channel: str):
        if channel in self._subscribed_channels:
            return
        try:
            await self.redis_client.xgroup_create(
                channel, self.group, id="0-0", mkstream=True
            )  # pyright: ignore[reportGeneralTypeIssues]
        except ResponseError as error:
            if "BUSYGROUP" not in str(error):
                raise
        self._subscribed_channels.add(channel)

    @staticmethod
    def _decode(value):
        return value.decode("utf-8") if isinstance(value, bytes) else value

    def _decode_entry(self, channel: str, entry_id, fields) -> QueueMessage:
        entry_id = self._decode(entry_id)
        payload = fields.get(b"payload", fields.get("payload"))
        message = json.loads(self._decode(payload))
        self._pending[id(message)] = (channel, entry_id)
        return message

    async def subscribe(self, channel: str) -> QueueMessage:
        await self._ensure_group(channel)

        # Reclaim crashed consumers' deliveries before reading new entries.
        _, claimed, _ = await self.redis_client.xautoclaim(
            channel,
            self.group,
            self.consumer_name,
            self.reclaim_idle_ms,
            start_id="0-0",
            count=1,
        )  # pyright: ignore[reportGeneralTypeIssues]
        if claimed:
            entry_id, fields = claimed[0]
            return self._decode_entry(channel, entry_id, fields)

        result = await self.redis_client.xreadgroup(
            self.group,
            self.consumer_name,
            {channel: ">"},
            count=1,
            block=0,
        )  # pyright: ignore[reportGeneralTypeIssues]
        if result:
            _, entries = result[0]
            entry_id, fields = entries[0]
            return self._decode_entry(channel, entry_id, fields)
        raise RuntimeError("Redis stream read returned no message")

    async def ack(self, message: QueueMessage):
        channel, entry_id = self._pending.pop(id(message))
        await self.redis_client.xack(channel, self.group, entry_id)  # pyright: ignore[reportGeneralTypeIssues]

    async def unsubscribe(self, channel: str):
        self._subscribed_channels.discard(channel)
