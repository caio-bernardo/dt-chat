import json

import redis.asyncio as redis

from pubsub.interfaces import IPublisher, ISubscriber, QueueMessage


class RedisQueueProducer(IPublisher):
    """Queue producer using Redis lists, implements IPublisher interface"""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def publish(self, channel: str, message: QueueMessage):
        """Push a message onto the queue (FIFO)"""
        # WARN: ignoring typing error, there seems to be a typing problem with redis
        # functions, there type indicates they both return awaitable and
        # nonawaitable types
        await self.redis_client.lpush(channel, json.dumps(message))  # pyright: ignore[reportGeneralTypeIssues]


class RedisQueueConsumer(ISubscriber):
    """Queue consumer using Redis lists, implements ISubscriber interface"""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self._subscribed_channels = set()

    async def subscribe(self, channel: str) -> QueueMessage:
        """
        Subscribe to a queue and retrieve a message.
        Blocks until a message is available.
        Returns the message as a string.
        """
        self._subscribed_channels.add(channel)
        # BRPOP blocks until a message is available (timeout=0 means wait forever)
        result = await self.redis_client.brpop([channel], timeout=0)  # pyright: ignore[reportGeneralTypeIssues]
        if result:
            # brpop returns (channel_name, message) tuple
            message = result[1]
            return json.loads(
                message.decode("utf-8") if isinstance(message, bytes) else message
            )
        raise Exception("somehow the blocking queue timeouted???")

    async def unsubscribe(self, channel: str):
        """Unsubscribe from a queue"""
        self._subscribed_channels.discard(channel)
