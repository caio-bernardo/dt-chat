import uuid
from typing import Sequence

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.types import Checkpointer


class ChatBotBase:
    def __init__(
        self,
        model: BaseChatModel | str,
        prompt_eng: SystemMessage,
        toolkit: Sequence[BaseTool] = [],
        saver: Checkpointer = None,
    ):
        self.agent = create_agent(
            model=model,
            tools=toolkit,
            system_prompt=prompt_eng,
            checkpointer=saver,
        )

        self.thread_id = uuid.uuid4()

    def process_message(self, thread_id: uuid.UUID, message: HumanMessage) -> AIMessage:
        """Process an incoming human message and return the AIMessage response.
        Args:
            thread_id (uuid.UUID): Identifier for the conversation thread.
            message (HumanMessage): The user's message to process.
        Returns:
            AIMessage: The agent's response message.
        """
        msg = self.agent.invoke(
            {"messages": [message]}, {"configurable": {"thread_id": thread_id}}
        )["messages"][-1]
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
        return res["messages"][-1]


__all__ = ["ChatBotBase", "BaseChatModel", "SystemMessage", "HumanMessage"]
