import datetime as dt
import random

from pydantic.dataclasses import dataclass


@dataclass
class TimeSimulationConfig:
    temporal_offset: dt.timedelta = dt.timedelta(seconds=0)
    typing_speed_wpm: float = 40.0
    thinking_time_range: tuple = (2, 10)
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
