from bancobot.agent import BancoAgentBuilder, VectorStore, get_vector_store
from langchain.tools import tool
from langchain_core.tools import BaseTool


def make_search_credit_card_tool(vector_store: VectorStore) -> BaseTool:
    """Make a tool to search documents for credit card information in a vector store."""

    @tool(response_format="content_and_artifact")
    def search_credit_card(query: str):
        """Recupera informações de Cartão de Crédito e Produtos Bancários do Banco X para responder query."""
        retrieved_docs = vector_store.similarity_search(query)
        serialized = "\n\n".join([doc.page_content for doc in retrieved_docs])
        return serialized, retrieved_docs

    return search_credit_card


def make_search_fidelidade_varejo_tool(vector_store: VectorStore) -> BaseTool:
    """Make a tool to search documents for magazine discounts information in a vector store."""

    @tool(response_format="content_and_artifact")
    def search_credit_card(query: str):
        """Recupera informações de programas de fidelidade relacionados a redes de varejo do Banco X para responder query."""
        retrieved_docs = vector_store.similarity_search(query)
        serialized = "\n\n".join([doc.page_content for doc in retrieved_docs])
        return serialized, retrieved_docs

    return search_credit_card


def make_search_fidelidade_aereo_tool(vector_store: VectorStore) -> BaseTool:
    """Make a tool to search documents for aircompany discounts information in a vector store."""

    @tool(response_format="content_and_artifact")
    def search_credit_card(query: str):
        """Recupera informações de programas de fidelidade de companhias aéreas do Banco X para responder query."""
        retrieved_docs = vector_store.similarity_search(query)
        serialized = "\n\n".join([doc.page_content for doc in retrieved_docs])
        return serialized, retrieved_docs

    return search_credit_card


def triple_rag_tool():
    """Uses three tools with different documents sets as RAG"""
    bancobot = BancoAgentBuilder()
    bancobot.toolkit = [
        make_search_credit_card_tool(get_vector_store("cartoes_collection")),
        make_search_fidelidade_varejo_tool(get_vector_store("varejo_collection")),
        make_search_fidelidade_aereo_tool(get_vector_store("milhas_collection")),
    ]
    return bancobot
