import datetime as dt
import time
import uuid
from typing import Callable

from chatbot import BaseChatModel, ChatBotBase, Checkpointer
from langchain_core.messages import AnyMessage
from langchain_core.messages.ai import AIMessage
from langchain_core.messages.human import HumanMessage

from .timing_config import TimeSimulationConfig

TypedSender = Callable[[HumanMessage], AIMessage]


class UserBot(ChatBotBase):
    """Classe UserBot simula a interação entre um usuário e um chatbot.
    Utiliza um agente conversacional que assume a personalidade do usuário e
    realiza no máximo N interações com o chatbot."""

    EXIT_SAFE_WORD = "quit"

    def __init__(
        self,
        persona: str,
        model: BaseChatModel | str,
        send_to_bot: TypedSender,
        initial_messages: list[AnyMessage] = [],
        saver: Checkpointer = None,
    ) -> None:
        self.send_to_bot = send_to_bot
        super().__init__(
            model, prompt_eng=persona, initial_messages=initial_messages, saver=saver
        )

    def run(
        self,
        initial_msg: str,
        max_iterations: int = 15,
        timesim_config: TimeSimulationConfig = TimeSimulationConfig(),
    ):
        """Executa a simulação de interação entre um usuário e um chatbot.

        Args:
            initial_msg (str): Mensagem inicial do usuário.
            max_iterations (int, optional): Número máximo de interações. Padrão 15.
            timesim_config (TimeSimulationConfig, optional): Configurações de simulação de tempo. Padrão TimeSimulationConfig().
        """
        thread_id = uuid.uuid4()
        query = initial_msg

        simulated_timestamp = dt.datetime.now() + timesim_config.temporal_offset

        for _ in range(max_iterations):
            response = str(
                self.process_message(str(thread_id), HumanMessage(query)).content
            )

            ##### Simulação de Tempo ####
            # Intervalo de Pausa
            pause_time = dt.timedelta(seconds=0)
            if timesim_config.should_pause():
                pause_time = timesim_config.get_pause_time()
                if timesim_config.simulate_delays:
                    print(f"Pausing for: {pause_time}")
                    time.sleep(pause_time.seconds)
                simulated_timestamp += pause_time

            # Intervalo para Reflexão
            thinking_time = timesim_config.get_thinking_time()
            if timesim_config.simulate_delays:
                print(f"Thinking for: {thinking_time}")
                time.sleep(thinking_time.seconds)
            simulated_timestamp += thinking_time

            # Intervalo de Digitação
            typing_time = timesim_config.get_typing_delta(response)
            if timesim_config.simulate_delays:
                print(f"Typing message for: {typing_time}")
                time.sleep(typing_time.seconds)
            simulated_timestamp += typing_time

            timing_metadata = {
                "simulated_timestamp": simulated_timestamp.isoformat(),
                "typing_time": typing_time.total_seconds(),
                "thinking_time": thinking_time.total_seconds(),
                "pause_time": pause_time.total_seconds(),
            }
            ##### FIM da Simulação de Tempo ####

            query = str(
                self.send_to_bot(
                    HumanMessage(response, timing_metadata=timing_metadata)
                ).content
            )

            if self.EXIT_SAFE_WORD in response.lower():
                print("=" * 8, "USUÁRIO ENCERROU A CONVERSA", "=" * 8)
                break

            if self.EXIT_SAFE_WORD in query.lower():
                print("=" * 8, "BANCO ENCERROU A CONVERSA", "=" * 8)
                break
