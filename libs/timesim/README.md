# Time Simulation Library (timesim)

The `timesim` library is a helper package designed to encapsulate configuration models and timing metadata.

## What it is

This library defines parameters (like words-per-minute typing rates, pause probabilities, and thinking intervals) that model realistic human behavior. It calculates individual delays based on text lengths and compiles timing metadata directly into serialized message files, allowing simulated conversations to have lifelike timestamps.

## For what it can be used for

- Generating mathematically realistic timestamps for simulated chat messages.
- Back-populating timing configurations when importing raw json files into the framework.
- Controlling typing, thinking, and break behaviors within the Userbot simulation swarms.

---

## Detailed Documentation

For a structural breakdown of the timing models, fields description, and configurations, see the dedicated documentation page:
👉 **[docs/timesim.md](../../docs/timesim.md)**
