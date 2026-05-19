"""fork_engine package.

Keep imports lightweight so unit tests can import submodules (e.g. `fork_engine.engine`)
without pulling in runtime-only dependencies.
"""

import asyncio


def main():
    # Lazy import to avoid importing runtime wiring (redis, twinbots, env vars)
    # during normal library usage and unit tests.
    from .main import amain

    asyncio.run(amain())


__all__ = ["main"]
