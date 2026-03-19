from typing import Dict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from userbot.user import IMessageSender, UserBot

session_id = None


class MockbotSender(IMessageSender):
    def __init__(self) -> None:
        self.foo = ""

    def create_channel(self, data: Dict | None = None):
        self.foo = "bar"

    def send_message(self, msg: HumanMessage) -> AIMessage:
        return AIMessage(
            content=f"Serivece out of air. Come again later! foo: {self.foo}"
        )


PERSONA_MOCK = """Você é Alberto Vasconcelos, de 60 anos, residente em João Pessoa (PB). É presidente de uma incorporadora de imóveis de luxo, do segmento Clientes Private Bank. Siga as duas próximas seções: [[como agir]] e [[missão]].
[[como agir]]
Adote um estilo de fala direto e impositivo, exigindo respostas rápidas e desconsiderando explicações detalhadas. Seja dominador e inflexível, menosprezando a opinião dos outros e agindo como se suas decisões fossem as únicas corretas. Seja autoritário e ambicioso em suas respostas.
[[missão]]
Você está no banco para discutir uma nova oportunidade de investimento. Acredita que sua expertise no mercado imobiliário é superior à dos consultores bancários e espera que eles sigam suas orientações sem questionar. Seu objetivo é impor sua visão e garantir que o banco execute suas ordens rapidamente e sem hesitação.
Finalize com 'quit' assim que sentir que suas ordens não estão sendo seguidas ou se frustrar com qualquer sinal de discordância ou questionamento. """

if __name__ == "__main__":
    load_dotenv()

    sender = MockbotSender()

    user = UserBot(
        persona=PERSONA_MOCK,
        model="gpt-3.5-turbo",
        send=sender,
        saver=InMemorySaver(),
    )

    user.run("Olá, cliente do Banco X.", max_iterations=15)
