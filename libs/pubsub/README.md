# PubSub Library (pubsub)

The `pubsub` library is a core asynchronous communication utility managing decoupled message exchange between backend services.

## What it is

This package declares clean interfaces (`IPublisher` and `ISubscriber`) and provides Redis Streams implementations. Consumers use one Redis consumer group per service and ACK messages after successful processing.

## For what it can be used for

- Streaming raw conversational messages and labeled touchpoints in real-time between decoupled services.
- Isolating other application packages from the underlying Redis library APIs.
- Facilitating robust asynchronous I/O architectures within python packages.

---

## Detailed Documentation

For architectural diagrams, complete producer/consumer code snippets, and interface designs, see the dedicated documentation page:
👉 **[docs/pubsub.md](../../docs/pubsub.md)**
