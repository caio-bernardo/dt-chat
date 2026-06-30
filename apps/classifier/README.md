# Touchpoint Classifier (classifier)

The Touchpoint Classifier is a real-time observation and mapping service that reads raw chat streams and translates unstructured language into structured process events.

## What it is

This package acts as an event classifier worker. It subscribes to raw chat messages on Redis (`msg_channel`), uses an LLM to categorize them into business-defined classes called **touchpoints** (defined in `/data/touchpoints/`), stores the results in SQLite, and republishes the labeled touchpoint events to a secondary Redis stream (`tp_channel`).

## For what it can be used for

- Mapping unstructured AI-User conversation logs into structured business event sequences.
- Generating clean database logs for Process Mining analyses.
- Broadcasting structured touchpoint events to trigger reactive simulations inside the Fork Engine.

---

## Detailed Documentation

For details on the touchpoint taxonomy, CLI options, and SQLite schemas, see the dedicated documentation page:
👉 **[docs/classifier.md](../../docs/classifier.md)**

To learn how to run the classifier worker or export touchpoint data, refer to the:
👉 **[docs/USAGE.md](../../docs/USAGE.md)**
