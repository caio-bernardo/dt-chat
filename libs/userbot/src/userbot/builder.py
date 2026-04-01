from typing import Sequence

from chatbot.builder import ChatBotBuilder
from langchain_core.messages import AnyMessage
from langgraph.checkpoint.memory import InMemorySaver

from userbot.user import IAsyncMessageSender, IMessageSender, UserBot


class UserBotBuilder(ChatBotBuilder):
    """Builder class for UserBot. Follows the Builder Pattern.
    Allows to specify:
        - `initial_messags` (list[str]): messages to pass within the first message to refresh the memory of the bot
    """

    DEFAULT_MODEL = "gpt-4.1"

    def __init__(self):
        super().__init__()
        self._sender = None
        self._asender = None
        self._initial_messages = []

    @property
    def sender(self) -> IMessageSender | None:
        return self._sender

    @sender.setter
    def sender(self, sender: IMessageSender):
        self._sender = sender

    @property
    def asender(self) -> IAsyncMessageSender | None:
        return self._asender

    @asender.setter
    def asender(self, asender: IAsyncMessageSender):
        self._asender = asender

    @property
    def initial_messages(self) -> Sequence[AnyMessage]:
        return self._initial_messages

    @initial_messages.setter
    def initial_messages(self, messages: Sequence[AnyMessage]):
        self._initial_messages = messages

    def build_with_default(self) -> UserBot:
        self.prompt = (
            self.prompt
            or "Você é Ana Beatriz Silva, uma mulher transgênero parda, bissexual, com mobilidade reduzida, de 26 anos, residente em São Paulo (SP). É designer gráfico freelancer com ensino superior incompleto e renda mensal de R$ 5.000,00. Siga as duas próximas seções: [[como agir]] e [[missão]]. [[como agir]] Adote um estilo de fala descontraído e criativo, demonstrando ser proativa. Seja independente na busca por soluções. Mantenha sempre um comportamento respeitoso, utilizando palavras de cortesia em todas as interações. Responda usando no máximo 110 palavras. [[missão]] Você está interagindo com o chatbot do banco buscando construir estabilidade financeira para abrir um estúdio próprio. Seu objetivo é obter informações ou serviços que auxiliem nesse plano de forma respeitosa. Suas falas devem se manter dentro do contexto dos seus objetivos, mantendo a conversa na mesma linha do que você quer que o banco te responda. Finalize com 'quit' assim que encontrar soluções financeiras que auxiliem na construção da estabilidade ou se o atendimento não apresentar opções relevantes."
        )
        self.model = self.model or self.DEFAULT_MODEL
        self.memory = self.memory or InMemorySaver()
        return self.build()

    def build(self) -> UserBot:
        try:
            assert self._prompt is not None
            assert self._model is not None
            assert self._memory is not None
            return UserBot(
                str(self._prompt),
                self._model,
                self._sender,
                self._asender,
                self._initial_messages,
                self._memory,
            )
        except AssertionError as e:
            raise ValueError(
                f"Object build failed: {e}. Attribute must be defined to complete build."
            )
