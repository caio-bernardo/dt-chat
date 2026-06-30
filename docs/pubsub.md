# PubSub Library &mdash; Publisher-Subscriber Interface

The `pubsub` library is a core asynchronous communication package within the `libs/` directory. It establishes a decoupled, real-time message exchange mechanism between different components of the Digital Twin framework.

## Purpose

The dt-chat architecture runs as a set of separate processes (such as `bancobot` generating messages, `classifier` mapping those messages to touchpoints, and `fork_engine` reacting to touchpoint events). The `pubsub` library abstracts away the transport layer, providing high-level interfaces for producing and consuming stream messages, implemented on top of a Redis database.

## Architecture

```
┌─────────────────┐       pubsub.RedisQueueProducer       ┌───────────────┐
│    Bancobot     │ ────────────────────────────────────> │  Redis Queue  │
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
3. **Flexible Interface**: Declares clean, mockable abstract base classes (`IPublisher` and `ISubscriber`), making local unit-testing straightforward without running Redis.

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
    
    payload = {"message_id": "...", "content": "Hello World"}
    await producer.publish("msg_channel", json.dumps(payload))
```

### 3. Consuming Messages (Consumer)
```python
from pubsub.redis import RedisQueueConsumer
from redis.asyncio import Redis

async def consume():
    redis_client = Redis(port=16739)
    consumer = RedisQueueConsumer(redis_client)
    
    while True:
        event = await consumer.subscribe("msg_channel")
        if event:
            print("Received:", event)
```

For configuring ports and running redis, please consult the [USAGE Guide](USAGE.md).
