from typing import Sequence

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.types import Checkpointer

from chatbot.core import ChatBotBase


class ChatBotBuilder:
    def __init__(self):
        self._model = None
        self._toolkit = None
        self._middlewares = None
        self._prompt = None
        self._memory = None
        self._initial_messages = []

    @property
    def model(self) -> BaseChatModel | str | None:
        return self._model

    @model.setter
    def model(self, model: BaseChatModel | str):
        self._model = model

    @property
    def toolkit(self) -> Sequence[BaseTool] | None:
        return self._toolkit

    @toolkit.setter
    def toolkit(self, toolkit: Sequence[BaseTool]):
        self._toolkit = toolkit

    @property
    def middlewares(self) -> Sequence[AgentMiddleware] | None:
        return self._middlewares

    @middlewares.setter
    def middlewares(self, middlewares: Sequence[AgentMiddleware]):
        self._middlewares = middlewares

    @property
    def prompt(self) -> str | SystemMessage | None:
        return self._prompt

    @prompt.setter
    def prompt(self, prompt: str | SystemMessage):
        self._prompt = prompt

    @property
    def initial_messages(self) -> Sequence[AnyMessage]:
        return self._initial_messages

    @initial_messages.setter
    def initial_messages(self, messages: list[AnyMessage]):
        self._initial_messages = messages

    @property
    def memory(self) -> Checkpointer | None:
        return self._memory

    @memory.setter
    def memory(self, saver: Checkpointer):
        self._memory = saver

    def build(self) -> ChatBotBase:
        try:
            assert self._model is not None
            assert self._toolkit is not None
            assert self._prompt is not None
            assert self._initial_messages is not None
            assert self._middlewares is not None
            assert self._memory is not None
            return ChatBotBase(
                self._model,
                self._prompt,
                self._initial_messages,
                self._middlewares,
                self._toolkit,
                self._memory,
            )
        except AssertionError as e:
            raise ValueError(
                f"Object build failed: {e}. Attribute must be defined to complete build."
            )
