from typing import Sequence

from chatbot import BaseChatModel, BaseTool, ChatBotBase, Checkpointer, SystemMessage
from chatbot.builder import ChatBotBuilder
from langchain_chroma import Chroma
from langchain_core.tools import tool
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langgraph.checkpoint.memory import InMemorySaver

BANCO_BOT_SYSTEM_PROMPT = SystemMessage(
    "Você é um chatbot de banco. "
    "Sua especialidade é fornecer informações claras, precisas e acessíveis sobre programas de fidelidade do banco X, milhagem de companhias parceiras do banco X,"
    " sobre cartões de crédito e outros produtos bancários "
    " e programas de fidelidade de redes de varejo parceiras do banco X. "
    "Você tem acesso a uma ferramenta para buscar documentação relevante, use-a para responder perguntas do cliente."
    "Você deve agir como um chatbot com conhecimento limitado. "
    "Você deve tentar ajudar o cliente, mas suas respostas podem ser confusas ou incompletas. "
    "Caso você não tenha uma resposta certeira, você deve comunicar ao cliente."
    "Responda exclusivamente com base no contexto da documentação e conforme todas as instruções acima."
)

DEFAULT_MODEL = "gpt-4.1"


class BancoAgent(ChatBotBase):
    """Banco Agent. Allows control over model, tools avaiable, prompt
    engeneering and checkpointer saver."""

    def __init__(
        self,
        model: BaseChatModel | str,
        toolkit: Sequence[BaseTool] = [],
        prompt_eng: SystemMessage | str = BANCO_BOT_SYSTEM_PROMPT,
        saver: Checkpointer = None,
    ):
        super().__init__(model, prompt_eng, [], toolkit, saver)


def make_search_documentation_tool(vector_store: VectorStore) -> BaseTool:
    """Make a tool to search for documents inside a vector store"""

    @tool(response_format="content_and_artifact")
    def search_documentation(query: str):
        """Retrieve bank X's information to help answer a query."""
        retrieved_docs = vector_store.similarity_search(query)
        serialized = "\n\n".join([doc.page_content for doc in retrieved_docs])
        return serialized, retrieved_docs

    return search_documentation


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


class BancoAgentBuilder(ChatBotBuilder):
    """Banco Agent Builder class. Allows to build a new agent using Builder pattern and with some standard defaults."""

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
            return BancoAgent(self._model, self._toolkit, self._prompt, self._memory)
        except AssertionError as e:
            raise ValueError(
                f"Object build failed: {e}. Attribute must be defined to complete build."
            )
