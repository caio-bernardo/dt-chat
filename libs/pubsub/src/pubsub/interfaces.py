from abc import ABC, abstractmethod
from typing import Dict, TypedDict


class QueueMessage(TypedDict):
    origin: str
    model_type: str
    content: Dict


class IPublisher(ABC):
    """Publisher Interface, allows to publish message to a channel"""

    @abstractmethod
    async def publish(self, channel: str, message: QueueMessage): ...


class ISubscriber(ABC):
    """Subscriber interface, allows to subscribe and unsubscribe to a channel"""

    @abstractmethod
    async def subscribe(self, channel: str) -> QueueMessage: ...

    @abstractmethod
    async def unsubscribe(self, channel: str): ...
