# Exporter

The `exporter` package is a focused utility designed to compile and format the raw classified touchpoints database into standard event logs suitable for process mining, sequence analysis, or research evaluation.

## Purpose

While the `classifier` app records individual touchpoints as they occur, process mining techniques require structured event sequences complete with case markers. The `exporter` reads database logs, adds synthetic boundaries (`START` and `END` events), reconstructs parent histories for branched conversations, and outputs a highly clean CSV.

## Key Features

1. **Boundary Insertion**: Inject synthetic events `START-DIALOGUE-SYSTEM` (internal ID `-1`) and `END-DIALOGUE-SYSTEM` (internal ID `99999`) for each dialogue session to establish clear start and end marks.
2. **Fork Reassembly**: If a conversation was branched or simulated via the Fork Engine, the exporter dynamically traces the message tree. It includes all parent messages and touchpoints prior to the fork point in the exported file, ensuring each simulated case has a complete, unbroken chronological history without duplicating the catalyst event.
3. **Comprehensive Schema**: Serializes timestamps, actor identities (Human/AI/System), catalyst details, tools triggered during RAG search, and bot configurations.

## Schema Specification

The generated CSV maps each touchpoint to the following fields:

| Field | Type | Description |
|---|---|---|
| `event_id` | `int` | Unique global incremental ID of the event log row. |
| `case_id` | `UUID` | UUID representing the conversation session (case). |
| `internal_id` | `int` | Sequential ID of the touchpoint within the scope of this conversation (`-1` for start, `99999` for end). |
| `actor` | `str` | Producer of the message: `System`, `Human`, or `AI`. |
| `activity` | `str` | The touchpoint class name (e.g., `SAUDAÇÃO`, `START-DIALOGUE-SYSTEM`). |
| `timestamp` | `str` | ISO-8601 simulated timestamp of the touchpoint. |
| `bot_label` | `str` | Configuration/name of the chatbot model that answered. |
| `tool_source` | `str` | Source files accessed by the chatbot (e.g., in RAG documents). |
| `catalyst_case_id` | `UUID \| None` | If this session was a simulation fork, the ID of the original source conversation. |
| `catalyst_message_id`| `UUID \| None` | UUID of the specific message that triggered the fork. |
| `catalyst_activity`| `str \| None` | The touchpoint class of the triggering message. |
| `catalyst_message_ts`| `str \| None` | Timestamp of the catalyst message. |

## Usage

Run the exporter using `just` (highly recommended):
```sh
just exporter output-file="my_events.csv" db-path="db/touchpoints.db"
```
Or directly using `uv run`:
```sh
uv run --package exporter exporter --file-output my_events.csv --db-path db/touchpoints.db
```

For more context on running the entire pipeline, see the [USAGE Guide](USAGE.md).
