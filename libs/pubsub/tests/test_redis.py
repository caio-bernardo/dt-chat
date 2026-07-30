import asyncio
from unittest.mock import AsyncMock

from pubsub import QueueMessage
from pubsub.redis import RedisQueueConsumer, RedisQueueProducer


def test_stream_publish_consume_ack():
    asyncio.run(_test_stream_publish_consume_ack())


async def _test_stream_publish_consume_ack():
    redis = AsyncMock()
    redis.xautoclaim.return_value = (b"0-0", [], [])
    redis.xreadgroup.return_value = [
        (
            b"messages",
            [
                (
                    b"1-0",
                    {
                        b"payload": b'{"origin":"test","model_type":"message","content":{}}'
                    },
                )
            ],
        )
    ]

    message: QueueMessage = {
        "origin": "test",
        "model_type": "message",
        "content": {},
    }
    await RedisQueueProducer(redis).publish("messages", message)
    consumer = RedisQueueConsumer(redis, group="classifier", consumer_name="test")

    received = await consumer.subscribe("messages")
    assert received == message
    await consumer.ack(received)

    redis.xadd.assert_awaited_once()
    redis.xgroup_create.assert_awaited_once_with(
        "messages", "classifier", id="0-0", mkstream=True
    )
    redis.xack.assert_awaited_once_with("messages", "classifier", "1-0")
