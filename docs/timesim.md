# Time Simulation Library

The `timesim` library is a helper data-modeling library in the `libs/` directory. It defines configurations and timing metadata used to represent realistic human behavior in simulated chat environments.

## Purpose

When historical conversations are generated or replayed (for example, in the `userbot` swarm or when importing records via `importer.py`), representing them with static, identical timestamps breaks sequence accuracy. The `timesim` library encapsulates parameters that govern how delay, typing speed, and thought process intervals are represented, allowing the simulations to feel realistic in both timestamps and actual delay.

## Key Features

1. **Simulation Configuration Model**: Holds properties defining probability of pauses, the duration ranges of those pauses, and words-per-minute simulation bounds.
2. **Timing Metadata Representation**: Stores timing metadata for individual messages (e.g. `typing_time`, `thinking_time`, `simulated_timestamp`), which are serialized into database records.
3. **Time Calculations**: Provides mathematical formulas to estimate realistic delays based on string lengths and configuration profiles.

## Library Structure

```
libs/timesim/
├── timesim/
│   ├── __init__.py
│   ├── config.py      # TimeSimulationConfig dataclass (typing speed, pauses, probabilities)
│   └── models.py      # TimingMetadata class containing computed delays & timestamps
├── pyproject.toml
└── README.md
```

## Models Breakdown

### `TimeSimulationConfig`
This configuration holds constants used by the simulation algorithms:
* `wpm`: Words per minute for typing speed (e.g., 40 WPM).
* `thinking_time_range_s`: Tuple defining bounds for "thought" delays (e.g., `(1.0, 5.0)` seconds).
* `pause_probability`: Chance that a simulated human takes a longer break between actions (e.g., `0.05` or 5%).
* `pause_time_range_s`: Duration range for simulated long pauses (e.g., `(60.0, 3600.0)` seconds).
* `simulate_sleep`: A boolean flag. If `True`, the simulation actually blocks execution (via `asyncio.sleep`) to simulate real human delays in real-time. If `False` (default), it merely computes the timestamps mathematically and stores them in metadata, allowing simulations to run at blazing-fast speed.

### `TimingMetadata`
Appended to every generated message to record simulation dynamics:
* `thinking_time`: Seconds simulated "thinking".
* `typing_time`: Seconds simulated "typing".
* `pause_time`: Seconds simulated on "pause".
* `simulated_timestamp`: Epoch Unix timestamp representing when the message theoretically was sent by the user.

For more information, see the [Userbot Library Documentation](userbot.md).
