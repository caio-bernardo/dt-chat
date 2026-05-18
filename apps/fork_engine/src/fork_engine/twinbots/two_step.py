from bancobot.agent import BancoAgentBuilder, get_vector_store
from langchain.agents.middleware import ModelRequest, dynamic_prompt


def two_step_rag():
    """Uses a Two Steps technique over RAG. Injects the retrieved documents directly in the prompt."""
    bancobot = BancoAgentBuilder()
    bancobot.toolkit = []  # Não vamos usar nenhuma ferramenta
    bancobot.middlewares = [prompt_with_context]
    return bancobot


@dynamic_prompt
def prompt_with_context(request: ModelRequest) -> str:
    "Injeta contexto na engenharia de prompt"
    last_query = request.state["messages"][-1].text
    retrieved_docs = get_vector_store().similarity_search(last_query)

    docs_content = "\n\n".join(doc.page_content for doc in retrieved_docs)

    system_message = (
        "Você é um chatbot de banco. "
        "Sua especialidade é fornecer informações claras, precisas e acessíveis sobre programas de fidelidade do banco X, milhagem de companhias parceiras do banco X,"
        " sobre cartões de crédito e outros produtos bancários "
        " e programas de fidelidade de redes de varejo parceiras do banco X. "
        "Você deve agir como um chatbot com conhecimento limitado. "
        "Você deve tentar ajudar o cliente, mas suas respostas podem ser confusas ou incompletas. "
        "Caso você não tenha uma resposta certeira, você deve comunicar ao cliente."
        "Responda exclusivamente com base no contexto da documentação abaixo e conforme todas as instruções acima."
        f"\n\n{docs_content}"
    )

    return system_message
