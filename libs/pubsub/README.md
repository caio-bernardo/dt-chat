# PubSub &mdash; A Publisher-Subscriber Interface

Provides a Publisher and Subscriber Interface, allowing communication between process. Currently, provides both an interface and implementation using Redis Queue.

## Features

- Redis Queue, working as a publish-subscriber system for realtime events.

## Usage

### Pre-requisites

- a Redis Server
- redis-py to create a Redis Client (**use the async client**)

1. Add the library to your project (considering you are in this workspace).

```sh
uv add libs/pubsub
```

2. Import the components needed, you can either use the interfaces or the concrete types. The next examplo shows using the redis queue.

```py
## Producer Process
from pubsub.redis import RedisQueueProducer
from redis.asyncio import redis # notice the use of the async client
import json

redis = Redis()

proc = RedisQueueProducer(redis)

msg = {
    "payload": {
        "data": 42
    },
    "origin": "consumer"
}

await proc.publish("myqueue", json.dumps(msg))

## Consumer process
from pubsub.redis import RedisQueueConsumer
from redis.asyncio import redis # notice the use of the async client
import json

redis = Redis()

cons = RedisQueueConsumer(redis)

# awaiting for new messages
while True:
    msg = await cons.subscribe("myqueue")
    if msg:
        print(json.loads(msg))
```

## License

This project is under the [MIT License](../../LICENSE).
