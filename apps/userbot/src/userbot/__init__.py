from typing import Callable

from chatbot import BaseChatModel, ChatBotBase, SystemMessage
from langchain_core.messages.human import HumanMessage

EXIT_SAFE_WORD: str = "quit"


class UserBot(ChatBotBase):
    def __init__(
        self,
        persona: str,
        model: BaseChatModel,
        send_to_bot: Callable[[str], str],
    ) -> None:
        self.send_to_bot = send_to_bot

        super().__init__(model, prompt_eng=SystemMessage(persona))

    def run(self, initial_msg: str, max_iterations: int = 15):
        # Create fake time delay

        query = initial_msg

        for _ in range(max_iterations):
            response = str(
                self.process_message(self.thread_id, HumanMessage(query)).content
            )

            if EXIT_SAFE_WORD in response.lower():
                break

            query = str(self.send_to_bot(response))
