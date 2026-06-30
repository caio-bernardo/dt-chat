# PubSub Library (pubsub)

The `pubsub` library is a core asynchronous communication utility managing the decoupled real-time message exchange between backend services.

## What it is

This package declares clean interfaces (`IPublisher` and `ISubscriber`) and provides concrete production-ready implementations using **Redis streams and queues**. It allows real-time, non-blocking message flow from Bancobot to the Classifier, and from the Classifier to the Fork Engine.

## For what it can be used for

- Streaming raw conversational messages and labeled touchpoints in real-time between decoupled services.
- Isolating other application packages from the underlying Redis library APIs.
- Facilitating robust asynchronous I/O architectures within python packages.

---

## Detailed Documentation

For architectural diagrams, complete producer/consumer code snippets, and interface designs, see the dedicated documentation page:
👉 **[docs/pubsub.md](../../docs/pubsub.md)**
