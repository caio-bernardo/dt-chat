# Exporter (exporter)

The Exporter is a dedicated utility package designed to compile and serialize the raw classified touchpoints database into standard event logs.

## What it is

This package reads touchpoints stored in SQLite, structures them chronologically, inserts synthetic boundary events (`START-DIALOGUE-SYSTEM` and `END-DIALOGUE-SYSTEM`), traces and reassembles complete parent histories for branched (forked) simulations, and exports them into a clean CSV file.

## For what it can be used for

- Generating standardized event logs compatible with Process Mining software (Celonis, Disco, or the PM4Py Python library).
- Organizing branched conversation histories into sequential event rows without repeating the branching trigger event.
- Aggregating model performance, tools called, and simulated timing variables into a single file for research and auditing.

---

## Detailed Documentation

For details on the exact output schema, fields, and options, see the dedicated documentation page:
👉 **[docs/exporter.md](../../docs/exporter.md)**

To learn how to run the exporter via `just` commands, refer to the:
👉 **[docs/USAGE.md](../../docs/USAGE.md)**
