import asyncio

from bancobot.agent import (
    BancoAgentBuilder,
    get_vector_store,
    make_search_documentation_tool,
)
from classifier.models import Touchpoint
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from pubsub.redis import RedisQueueConsumer, RedisQueueProducer
from redis.asyncio import Redis
from userbot import UserBotBuilder

from fork_engine.engine import ForkConfig, ForkEngine
from fork_engine.helpers import (
    retrieve_conversation_messages,
    retrieve_conversation_metadata,
    retrieve_timesim_from_metadata,
    retrieve_userbot_persona_from_metadata,
)


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


def on_transbordo(data: Touchpoint) -> ForkConfig:
    # Nesse exemplo usaremos um RAG Chain
    # Um middleware que injeta contexto direto no prompt.
    bancobot = BancoAgentBuilder()
    bancobot.toolkit = []  # Não vamos usar nenhuma ferramenta
    bancobot.middlewares = [prompt_with_context]

    # User Bot
    meta = retrieve_conversation_metadata(data.session_id)
    userbot = UserBotBuilder()
    userbot.prompt = retrieve_userbot_persona_from_metadata(meta)
    conversation = retrieve_conversation_messages(data.session_id)
    userbot.initial_messages = conversation[:-3]
    timesim = retrieve_timesim_from_metadata(meta)

    return ForkConfig(
        parent_conversation=data.session_id,
        bancobot_builder=bancobot,
        userbot_builder=userbot,
        next_msg="",
        timesim=timesim,
    )


# EXEMPLO:
def on_reclamacao(data: Touchpoint) -> ForkConfig:
    bancobot = BancoAgentBuilder()
    # bancobot.prompt = "Você um assistente virtual muito gentil" # exemplo de mudança de engenharia de prompt
    bancobot.toolkit = [make_search_documentation_tool(get_vector_store())]

    # Gets the persona and timesim from the original conversation
    meta = retrieve_conversation_metadata(data.session_id)

    # Userbot builder
    userbot = UserBotBuilder()
    userbot.prompt = retrieve_userbot_persona_from_metadata(meta)
    # put messages from the conversation on the userbot
    conversation = retrieve_conversation_messages(data.session_id)
    # pass all history except the last two messages that caused the current touchpoint + remove the last answer because the conversation will re-start from -4
    userbot.initial_messages = conversation[:-3]

    # retrieve the time config from the conversation
    timesim = retrieve_timesim_from_metadata(meta)

    return ForkConfig(
        parent_conversation=data.session_id,
        bancobot_builder=bancobot,
        userbot_builder=userbot,
        next_msg=str(conversation[-4].content),
        timesim=timesim,
    )


async def main():
    redis = Redis()
    consumer = RedisQueueConsumer(redis)
    producer = RedisQueueProducer(redis)
    engine = ForkEngine(consumer, producer)

    # engine.create_condition("REJEIÇÃO DA SOLUÇÃO", on_reclamacao)
    engine.create_condition("SOLICITAÇÃO DIRETA DE HUMANO", on_transbordo)
    await engine.awatch()


if __name__ == "__main__":
    asyncio.run(main())
