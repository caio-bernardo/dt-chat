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
    print(f"[DEBUG]: {conversation}")
    # pass history of conversation if we have at least 4 messages
    # because -1 is the touchpoint, -2 is the answer that "caused" the
    # touchpoint, and -3 will be reasked (or modified) in the next step to see
    # if we can avoid the touchpoint
    if len(conversation) < 4:
        userbot.initial_messages = []
    else:
        userbot.initial_messages = conversation[:-4]  # last message that caused

    # retrieve the time config from the conversation
    timesim = retrieve_timesim_from_metadata(meta)

    return ForkConfig(
        parent_conversation=data.session_id,
        bancobot_builder=bancobot,
        userbot_builder=userbot,
        next_msg=str(
            conversation[-3].content
        ),  # re-ask the message before the touchpoint
        timesim=timesim,
    )


async def amain():
    print("[INFO]: Initializing Fork Engine...")

    redis = Redis()
    consumer = RedisQueueConsumer(redis)
    producer = RedisQueueProducer(redis)
    engine = ForkEngine(consumer, producer)

    print("[INFO]: Setting up fork conditions...")
    engine.create_condition("FINALIZAÇÃO COM RECLAMAÇÃO", on_reclamacao)
    # engine.create_condition("SOLICITAÇÃO DIRETA DE HUMANO", on_transbordo)
    print("[INFO]: Listening for new messages ...")
    await engine.awatch()
