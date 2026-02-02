## Dependencies
from typing import Annotated

import redis.asyncio as redis
from chatbot import Checkpointer
from fastapi import Depends
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langgraph.checkpoint.memory import InMemorySaver
from sqlmodel import Session

import bancobot
import bancobot.agent

from .agent import BancoAgent
from .services import BancoBotService


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


def get_search_tool():
    """Returns a search tool that operates over a vector store"""
    vector_store = get_vector_store()
    return bancobot.agent.make_search_documentation_tool(vector_store)


def get_memory_saver() -> Checkpointer:
    """Returns a Memory Saver for checkpoiting"""
    return InMemorySaver()


def get_banco_agent(saver: Annotated[Checkpointer, Depends(get_memory_saver)]):
    """Returns Banco Agent"""
    search_tool = get_search_tool()
    return BancoAgent(model="gpt-4.1", toolkit=[search_tool], saver=saver)


def get_redis():
    """Creates a Redis Connections"""
    return redis.Redis()


def get_session():
    """Returns a SQLite storage class"""
    from .database import engine

    with Session(engine) as session:
        yield session


def get_bbchat_service(
    storage: Annotated[Session, Depends(get_session)],
    agent: Annotated[BancoAgent, Depends(get_banco_agent)],
    red_storage: Annotated[redis.Redis, Depends(get_redis)],
):
    """Returns Banco bot service class"""
    return BancoBotService(agent=agent, storage=storage, r=red_storage)
