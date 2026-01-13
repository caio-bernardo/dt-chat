import uuid
from typing import Sequence

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_core.vectorstores import VectorStore
from langgraph.types import Checkpointer

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


class BancoAgent:
    """Banco Agent. Allows control over model, tools avaiable, prompt
    engeneering and checkpointer saver."""

    def __init__(
        self,
        model: BaseChatModel | str,
        toolkit: Sequence[BaseTool] = [],
        prompt_eng: SystemMessage | str = BANCO_BOT_SYSTEM_PROMPT,
        saver: Checkpointer = None,
    ):
        self.agent = create_agent(
            model=model,
            tools=toolkit,
            system_prompt=prompt_eng,
            checkpointer=saver,
        )

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


def make_search_documentation_tool(vector_store: VectorStore) -> BaseTool:
    """Make a tool to search for documents inside a vector store"""

    @tool(response_format="content_and_artifact")
    def search_documentation(query: str):
        """Retrieve bank X's information to help answer a query."""
        retrieved_docs = vector_store.similarity_search(query)
        serialized = "\n\n".join([doc.page_content for doc in retrieved_docs])
        return serialized, retrieved_docs

    return search_documentation
