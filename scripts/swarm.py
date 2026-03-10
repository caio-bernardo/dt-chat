#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "langchain-openai>=1.1.7",
#     "python-dotenv>=1.2.1",
#     "requests>=2.32.5",
#     "typer>=0.21.1",
#     "userbot",
# ]
#
# [tool.uv.sources]
# userbot = { path = "../libs/userbot" }
# ///

"""
Script to generate a swarm of users to interact with a chatbot through http requests. Uses a json file to configure user behaivor.
Accepts other parameters to configure general behaivor. See `userswarm.py --help` for more.

Example:
    ./userswarm.py --workers=2 --typing-speed=30 --pause-probability=0.10 prompts.json

Example format for json file:
{
    "1": {
        "persona": "Seu nome é Marcos, 32 anos. Siga as instruções: [[como agir]] ... [[missao]] ...",
        "duração": "media",
        "offset": "horario-comercial",
        "weekend": false
    },
    ...
}
"""

import datetime as dt
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict

import requests
import typer
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from userbot import (
    AIMessage,
    HumanMessage,
    IMessageSender,
    TimeSimulationConfig,
    UserBot,
)


@dataclass
class Persona:
    id: int
    prompt: str
    typing_speed: float
    thinking_range: tuple[int, int]
    temporal_offset: dt.timedelta


class BancoBotSender(IMessageSender):
    def __init__(self, api_url: str):
        self.session_id: int | None = None
        self.api_url = api_url

    def create_channel(self, data: Dict | None = None):
        payload = {"meta": data or {}}

        response = requests.post(f"{self.api_url}/sessions", json=payload)
        response.raise_for_status()
        self.session_id = response.json()["id"]

    def send_message(self, msg: HumanMessage) -> AIMessage:
        assert self.session_id, (
            "Error: no channel created. Do you remembered to call `create_channel` before this fuction?"
        )
        assert msg.timing_metadata, "Error: no timing_metadata in HumanMessage."  # pyright: ignore[reportAttributeAccessIssue]

        payload = {
            "conversation_id": self.session_id,
            "content": str(msg.content),
            "timing_metadata": msg.timing_metadata,  # pyright: ignore[reportAttributeAccessIssue]
        }

        response = requests.post(f"{self.api_url}/messages", json=payload)
        response.raise_for_status()
        return AIMessage(content=response.json()["content"])


LLM_MODEL = "gpt-4.1"


def check_server_availability(api_url: str) -> bool:
    """Retorna *True* se `api_url/health` responder *HTTP 200* em até 5 s."""
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def is_weekend(date: dt.datetime) -> bool:
    """Retorna se uma data é um fim de semana."""
    return date.weekday() >= 5


def calculate_temporal_offset(
    offset_type: str, max_days: int = 30, weekend: bool = False
) -> dt.timedelta:
    """Calcula o offset de tempo entre o tempo atual e a data escolhida para a simulação."""

    time_ranges = {
        "manhã": (7, 11),
        "tarde": (12, 17),
        "noite": (18, 6),
        "horario-comercial": (8, 17),
    }

    assert offset_type in time_ranges.keys(), (
        f"Error: Invalid Offset Type: {offset_type}"
    )

    now = dt.datetime.now()

    # Escolhemos um dia no futuro
    target_date = random.choice(
        [
            now + dt.timedelta(days=x)
            for x in range(1, max_days)
            if weekend == is_weekend(now + dt.timedelta(days=x))
        ]
    )

    # Escolhemos uma hora aleatoria. Para "noite" temos 70% de chance de ser de noite e 30% de madrugada.
    if offset_type == "noite":
        target_hour = (
            random.randint(18, 23) if random.random() < 0.7 else random.randint(0, 6)
        )
    else:
        start, end = time_ranges[offset_type]
        target_hour = random.randint(start, end)

    # Randomizamos minuto e segundo e retornamos o offset
    return (
        target_date.replace(
            hour=target_hour, minute=random.randint(0, 59), second=random.randint(0, 59)
        )
        - now
    )


def parse_to_persona(id: str, data: dict[str, str]) -> Persona:
    """Retorna uma Persona dado um objeto de dicionário."""
    match data["duração"]:
        case "lenta":
            typing_speed = random.uniform(10, 24)
            thinking_range = (8, 35)
        case "media":
            typing_speed = random.uniform(25, 54)
            thinking_range = (2, 12)
        case "rapida":
            typing_speed = random.uniform(55, 90)
            thinking_range = (2, 7)
        case _:
            typing_speed = random.uniform(25, 54)
            thinking_range = (2, 12)

    temporal_offset = calculate_temporal_offset(
        data["offset"], weekend=data["weekend"] == "true"
    )

    return Persona(
        id=int(id),
        prompt=data["persona"],
        temporal_offset=temporal_offset,
        typing_speed=typing_speed,
        thinking_range=thinking_range,
    )


def init_user(
    persona_id: int,
    prompt: str,
    api_url: str,
    temporal_offset: dt.timedelta,
    typing_speed: float,
    thinking_range: tuple[int, int],
    pause_probability: float,
    pause_time_range: tuple[float, float],
    simulate_delays: bool,
):
    """Inicia a simulação de um UserBot."""
    user = UserBot(
        prompt,
        LLM_MODEL,
        BancoBotSender(api_url),
        [],
        InMemorySaver(),
    )
    try:
        user.run(
            "Olá, cliente do Banco X.",
            timesim_config=TimeSimulationConfig(
                temporal_offset=temporal_offset,
                typing_speed_wpm=typing_speed,
                thinking_time_range=thinking_range,
                pause_probability=pause_probability,
                pause_time_range=pause_time_range,
                simulate_delays=simulate_delays,
            ),
        )
    except requests.HTTPError as e:
        print(
            f"[{dt.datetime.now()}] ERROR: HTTP error occurred. Detail: {e.response.content}"
        )
    except Exception as e:
        print(f"[{dt.datetime.now()}] ERROR: User run failed. Detail: {e}")
    else:
        print(f"[{dt.datetime.now()}] INFO: User {persona_id} finished.")


def main(
    prompts_file: str,
    api_url: str = "http://localhost:8000",
    workers: int = 4,
    sequential: bool = False,
    times: int = 1,
    pause_probability: float = 0.05,
    pause_min: float = 60.0,
    pause_max: float = 3600.0,
    simulate_delays: bool = False,
) -> None:
    """Execute a swarm of users against a chatbot through http requests.

    Uses a json file with prompts to simulate user behaivor.

    Args:
        prompts_file (str): path to json file containing the prompt engeneering of each user
        api_url (str): URL for the chatbot API to request (defaults to "localhost:8000")
        workers (int): number of worker threads to use (defaults to 4)
        sequential (bool): run users sequentially (overrides workers) (defaults to False)
        times (int): number of times to run each user (defaults to 1)
        pause_probability (float): probability of pausing between messages (defaults to 0.05)
        pause_min (float): minimum pause time in seconds (defaults to 60.0)
        pause_max (float): maximum pause time in seconds (defaults to 3600.0)
        simulate_delays (bool): sleep during typing, pauses and thinking. WARN it will slow down the application considerably! (defaults to False)
    """

    assert check_server_availability(api_url), (
        f"Error: the server at {api_url} is not available."
    )

    try:
        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts: dict = json.load(f)
    except Exception as e:
        print(f"Error: Problem reading file: {e}")
        exit(1)

    assert prompts, "Error: prompt file is empty."

    try:
        personas: list[Persona] = [
            parse_to_persona(id, prompt) for id, prompt in prompts.items()
        ] * times
    except Exception as e:
        print(f"Error: Problem parsing personas: {e}")
        exit(1)

    print("INFO: Init simulation")
    if sequential:
        for persona in personas:
            init_user(
                persona.id,
                persona.prompt,
                api_url,
                persona.temporal_offset,
                persona.typing_speed,
                persona.thinking_range,
                pause_probability,
                (pause_min, pause_max),
                simulate_delays,
            )
    else:
        with ThreadPoolExecutor(max_workers=workers) as exec:
            futures = [
                exec.submit(
                    init_user,
                    persona.id,
                    persona.prompt,
                    api_url,
                    persona.temporal_offset,
                    persona.typing_speed,
                    persona.thinking_range,
                    pause_probability,
                    (pause_min, pause_max),
                    simulate_delays,
                )
                for persona in personas
            ]

            for _ in as_completed(futures):
                pass

    print("INFO: simulation complete.")


if __name__ == "__main__":
    load_dotenv()

    assert os.environ.get("OPENAI_API_KEY") is not None, (
        "Error: there must be a env variable 'OPENAI_API_KEY' for the userbots."
    )

    typer.run(main)
