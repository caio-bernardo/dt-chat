import uuid
from typing import Any, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.types import Checkpointer


class ChatBotBase:
    def __init__(
        self,
        model: BaseChatModel | str,
        prompt_eng: SystemMessage | str,
        initial_messages: Sequence[AnyMessage] = [],
        middlewares: Sequence[AgentMiddleware] = [],
        toolkit: Sequence[BaseTool] = [],
        saver: Checkpointer = None,
    ):
        self.agent = create_agent(
            model=model,
            tools=toolkit,
            middleware=middlewares,
            system_prompt=prompt_eng,
            checkpointer=saver,
        )
        self._prompt_eng = prompt_eng
        self._initial_messages = initial_messages

    @property
    def prompt_eng(self) -> SystemMessage | str:
        return self._prompt_eng

    def process_message(self, thread_id: str, message: HumanMessage) -> AIMessage:
        """Process an incoming human message and return the AIMessage response.
        Args:
            thread_id (uuid.UUID): Identifier for the conversation thread.
            message (HumanMessage): The user's message to process.
        Returns:
            AIMessage: The agent's response message.
        """

        messages = list(self._initial_messages) + [message]
        if self._initial_messages:
            self._initial_messages = []

        result = self.agent.invoke(
            {"messages": messages},  # pyright: ignore[reportArgumentType]
            {"configurable": {"thread_id": thread_id}},
        )

        tool_source = self._get_tool_sources(result["messages"])
        msg = result["messages"][-1]
        msg.additional_kwargs["tool_source"] = tool_source
        return msg

    async def aprocess_message(
        self, thread_id: uuid.UUID, message: HumanMessage
    ) -> AIMessage:
        """Asyncronous process of incoming human messages returning the AI response.
        Args:
            thread_id (uuid.UUID): Identifier for the conversation thread.
            message (HumanMessage): The user's message to process.
        Returns:
            AIMessage: The agent's response message.
        """

        res = await self.agent.ainvoke(
            {"messages": [message]}, {"configurable": {"thread_id": thread_id}}
        )

        tool_source = self._get_tool_sources(res["messages"])
        msg = res["messages"][-1]
        # includes tools used during thinking process and adds to metadata
        msg.additional_kwargs["tool_source"] = tool_source
        return msg

    def _get_tool_sources(self, msgs: Sequence[Any]) -> str:
        """Extract the tools used from the messages."""
        tool_source: set[str] = set()
        for m in msgs:
            if isinstance(m, ToolMessage):
                tool_source.add(m.name)
        return ",".join(tool_source)
