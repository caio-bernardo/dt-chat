from abc import ABC, abstractmethod


class IPublisher(ABC):
    """Publisher Interface, allows to publish message to a channel"""

    @abstractmethod
    async def publish(self, channel: str, message: str): ...


class ISubscriber(ABC):
    """Subscriber interface, allows to subscribe and unsubscribe to a channel"""

    @abstractmethod
    async def subscribe(self, channel: str) -> str: ...

    @abstractmethod
    async def unsubscribe(self, channel: str): ...
