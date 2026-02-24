from multiprocessing import Process
from typing import Callable, Iterable, Literal, TypedDict

from bancobot.agent import BancoAgent
from bancobot.database import IStorage
from classifier.models import Touchpoint
from pydantic import BaseModel
from userbot import TimeSimulationConfig, UserBot


class StreamData(TypedDict):
    origin: Literal["real", "simulated"]
    payload: Touchpoint


class ForkConfig(BaseModel):
    userbot: UserBot
    next_msg: str
    iterations: int = 15
    timesim: TimeSimulationConfig = TimeSimulationConfig()
    bancobot: BancoAgent


Condition = Callable[[StreamData], ForkConfig | None]


class ForkEngine:
    def __init__(self, queue: IStorage, conditions: Iterable[Condition]):
        self.queue = queue
        self.conditions: Iterable[Condition] = conditions

    async def awatch(self):

        threads: list[Process] = []
        while True:
            try:
                data: StreamData = await self.queue.arcv("tp_chan")

                # Ignore simulated touchpoints, to avoid recursion
                if data["origin"] == "simulated":
                    continue

                for condition in self.conditions:
                    config = condition(data)
                    if config:
                        t = Process(target=self.fork, args=(config,))
                        threads.append(t)
                        t.start()
            except Exception as e:
                print("Finish all forks")
                for t in threads:
                    t.join()
                raise e

    def fork(self, config: ForkConfig):
        config.userbot.run(config.next_msg, config.iterations, config.timesim)
