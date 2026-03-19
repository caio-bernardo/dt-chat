"""
A Python module for handling timing metadata in simulations.

This module provides the TimingMetadata class, a Pydantic model that encapsulates metadata associated with time simulations. It includes fields for simulated timestamps and various time intervals such as pause time, typing time, and thinking time.
"""

import datetime as dt
import random
from typing import TypedDict

from pydantic import BaseModel


class TimingMetadata(TypedDict):
    """Metadata associated with the time simulation.
    - simulated_timestamp: float (UNIX timestamp, timestamp when user sends the message)
    - pause_time: float (time the user paused to think about the answer in seconds)
    - typing_time: float (time the user spend to type things in seconds)
    - thinking_time: float (time the user spend thinking about the answer in seconds)
    """

    simulated_timestamp: float
    pause_time: float
    typing_time: float
    thinking_time: float


class TimeSimulationConfig(BaseModel):
    temporal_offset: dt.timedelta = dt.timedelta(seconds=0)
    typing_speed_wpm: float = 40.0
    thinking_time_range: tuple[int, int] = (2, 10)
    pause_probability: float = 0.05
    pause_time_range: tuple = (60, 3600)
    simulate_delays: bool = False

    def get_thinking_time(self) -> dt.timedelta:
        """Gera um tempo de reflexão aleatorio dentro de `thinking_time_range`."""
        return dt.timedelta(seconds=random.randint(*self.thinking_time_range))

    def get_typing_delta(self, sentence: str) -> dt.timedelta:
        """Gera o tempo de digitação de uma senteça com base em `typing_speed_wpm` com uma aleatoriedade de ±20%."""
        # Add +-20% randomness
        randomness = random.uniform(0.8, 1.2)
        return dt.timedelta(
            seconds=len(sentence.split()) / self.typing_speed_wpm * 60 * randomness
        )

    def should_pause(self) -> bool:
        """Retorna True caso deva pausar, False caso contrário.
        Utiliza `pause_probability` e uma distribuição uniforme para decidir."""
        return random.random() < self.pause_probability

    def get_pause_time(self) -> dt.timedelta:
        """Gera um tempo de pausa aleatorio dentro de `pause_time_range`."""
        return dt.timedelta(seconds=random.randint(*self.pause_time_range))
