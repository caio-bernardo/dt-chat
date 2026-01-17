# !/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer>=0.21.1",
#     "userbot>=0.1.0",
# ]
#
# [tool.uv.sources]
# userbot = { path = "../apps/userbot" }
# ///

import typer

import userbot


def main(
    prompts_file: str,
    api_url: str = "http://localhost:8000",
    workers: int = 4,
    sequencial: bool = False,
    times: int = 1,
    typing_speed: int = 40,
    thinking_min: float = 2.0,
    thinking_max=10.0,
    pause_probability: float = 0.05,
    pause_min: float = 60.0,
    pause_max: float = 3600.0,
    simulate_delays: bool = False,
) -> None:
    """Script que produz um enxame de usuário contra um chatbot de API.

    Utiliza um arquivo json de prompts para gerar os usuários.

    Args:
        prompts_file: path to json file containing the prompt engeneering of each user
        api_url: URL for the chatbot API to request (default: "localhost:8000")
        workers: number of worker threads to use (default: 4)
        sequencial: run users sequentially (overrides workers) (default: False)
        times: number of times to run each user (default: 1)
        typing_speed: typing speed in words per minute (default: 40)
        thinking_min: minimum time to think in seconds (default: 2.0)
        thinking_max: maximum time to think in seconds (default: 10.0)
        pause_probability: probability of pausing between messages (default: 0.05)
        pause_min: minimum pause time in seconds (default: 60.0)
        pause_max: maximum pause time in seconds (default: 3600.0)
        simulate_delays: sleep during typing, pauses and thinking. WARN it will slow down the application considerably! (default: False)
    """


if __name__ == "__main__":
    typer.run(main)
