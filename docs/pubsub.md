# PubSub Library &mdash; Publisher-Subscriber Interface

The `pubsub` library is a core asynchronous communication package within the `libs/` directory. It establishes a decoupled, real-time message exchange mechanism between different components of the Digital Twin framework.

## Purpose

The dt-chat architecture runs as separate processes: Bancobot generates messages, Classifier maps messages to touchpoints, and Fork Engine reacts to touchpoints. The `pubsub` library abstracts Redis Streams behind high-level interfaces.

## Architecture

```
┌─────────────────┐       pubsub.RedisQueueProducer       ┌───────────────┐
│    Bancobot     │ ────────────────────────────────────> │  Redis Stream │
└─────────────────┘                                       │ (msg_channel) │
                                                          └───────────────┘
                                                                  │
                                                      pubsub.RedisQueueConsumer
                                                                  ▼
┌─────────────────┐       pubsub.RedisQueueProducer       ┌───────────────┐
│   Classifier    │ ────────────────────────────────────> │  Redis Stream │
└─────────────────┘                                       │ (tp_channel)  │
                                                          └───────────────┘
                                                                  │
                                                      pubsub.RedisQueueConsumer
                                                                  ▼
                                                          ┌───────────────┐
                                                          │  Fork Engine  │
                                                          └───────────────┘
```

## Key Features

1. **Decoupled Messaging**: Components communicate entirely via message topics/streams, meaning they can be started, stopped, or scaled independently.
2. **High-Performance Async Transport**: Utilizes `redis.asyncio` for non-blocking I/O operations.
3. **Consumer Groups**: Each downstream service uses its own group and ACKs only after successful processing, providing at-least-once delivery.
4. **Flexible Interface**: Declares clean, mockable abstract base classes (`IPublisher` and `ISubscriber`), making local unit-testing straightforward without running Redis.

## Library Structure

```
libs/pubsub/
├── pubsub/
│   ├── __init__.py
│   ├── interfaces.py  # Abstract interfaces for Publishers & Consumers
│   └── redis.py       # Concrete implementations of Producer/Consumer using Redis as backend
├── pyproject.toml
└── README.md
```

## Developer Usage

### 1. Adding to a Package

To declare `pubsub` as a dependency in a workspace package, run:

```sh
uv add libs/pubsub
```

### 2. Publishing Messages (Producer)

```python
import json
from pubsub.redis import RedisQueueProducer
from redis.asyncio import Redis

async def produce():
    redis_client = Redis(port=16739)
    producer = RedisQueueProducer(redis_client)

    payload = {"origin": "example", "model_type": "message", "content": {}}
    await producer.publish("msg_channel", payload)
```

### 3. Consuming Messages (Consumer)

```python
from pubsub.redis import RedisQueueConsumer
from redis.asyncio import Redis

async def consume():
    redis_client = Redis(port=16739)
    consumer = RedisQueueConsumer(redis, group="classifier")

    while True:
        event = await consumer.subscribe("msg_channel")
        # ACK only after successful processing.
        if event:
            print("Received:", event)
            await consumer.ack(event)
```

For configuring ports and running redis, please consult the [USAGE Guide](USAGE.md).
