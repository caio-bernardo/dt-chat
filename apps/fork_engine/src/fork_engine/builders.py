from bancobot.agent import (
    BANCO_BOT_SYSTEM_PROMPT,
    BancoAgent,
    make_search_documentation_tool,
)
from chatbot.builder import ChatBotBuilder
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langgraph.checkpoint.memory import InMemorySaver
from userbot import TypedSender, UserBot

DEFAULT_MODEL = "gpt-4.1"


class UserBotBuilder(ChatBotBuilder):
    def __init__(self):
        super().__init__()
        self._sender = None

    @property
    def sender(self) -> TypedSender | None:
        return self._sender

    @sender.setter
    def sender(self, send_func: TypedSender):
        self._sender = send_func

    def build_with_default(self) -> UserBot:
        self.prompt = (
            self.prompt
            or "Você é Ana Beatriz Silva, uma mulher transgênero parda, bissexual, com mobilidade reduzida, de 26 anos, residente em São Paulo (SP). É designer gráfico freelancer com ensino superior incompleto e renda mensal de R$ 5.000,00. Siga as duas próximas seções: [[como agir]] e [[missão]]. [[como agir]] Adote um estilo de fala descontraído e criativo, demonstrando ser proativa. Seja independente na busca por soluções. Mantenha sempre um comportamento respeitoso, utilizando palavras de cortesia em todas as interações. Responda usando no máximo 110 palavras. [[missão]] Você está interagindo com o chatbot do banco buscando construir estabilidade financeira para abrir um estúdio próprio. Seu objetivo é obter informações ou serviços que auxiliem nesse plano de forma respeitosa. Suas falas devem se manter dentro do contexto dos seus objetivos, mantendo a conversa na mesma linha do que você quer que o banco te responda. Finalize com 'quit' assim que encontrar soluções financeiras que auxiliem na construção da estabilidade ou se o atendimento não apresentar opções relevantes."
        )
        self.model = self.model or DEFAULT_MODEL
        self.memory = self.memory or InMemorySaver()
        return self.build()

    def build(self) -> UserBot:
        try:
            assert self._prompt is not None
            assert self._model is not None
            assert self._sender is not None
            assert self._memory is not None
            return UserBot(str(self._prompt), self._model, self._sender, self._memory)
        except AssertionError as e:
            raise ValueError(
                f"Object build failed: {e}. Attribute must be defined to complete build."
            )


def get_embeddings():
    """Returns model to create text embeddings"""
    return OpenAIEmbeddings(model="text-embedding-3-large")


def get_vector_store(persist_directory: str = "./chroma_db"):
    """Returns a vector store"""
    embeddings = get_embeddings()
    return Chroma(
        collection_name="banco_collection",
        embedding_function=embeddings,
        persist_directory=persist_directory,
    )


class BancoBotBuilder(ChatBotBuilder):
    def __init__(self):
        super().__init__()

    def build_with_default(self) -> BancoAgent:
        self.model = self.model or DEFAULT_MODEL
        self.toolkit = self.toolkit or [
            make_search_documentation_tool(get_vector_store())
        ]
        self.prompt = self.prompt or BANCO_BOT_SYSTEM_PROMPT
        self.memory = self.memory or InMemorySaver()
        return self.build()

    def build(self) -> BancoAgent:
        try:
            assert self._model is not None
            assert self._toolkit is not None
            assert self._prompt is not None
            assert self._memory is not None
            return BancoAgent(self._model, self._toolkit, self._prompt, self._memory)
        except AssertionError as e:
            raise ValueError(
                f"Object build failed: {e}. Attribute must be defined to complete build."
            )
