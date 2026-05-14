from bancobot.agent import (
    BancoAgentBuilder,
    get_vector_store,
    make_search_documentation_tool,
)


def single_rag_tool():
    """Uses a RAG tool to the agent choose how to retrieve documents"""

    banco_agent = BancoAgentBuilder()

    banco_agent.toolkit = [make_search_documentation_tool(get_vector_store())]

    return banco_agent
