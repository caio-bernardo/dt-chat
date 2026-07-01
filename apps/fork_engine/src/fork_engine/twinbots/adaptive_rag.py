"""Adaptive RAG twinbot.

Builds a BancoAgent backed by the multi-datasource adaptive RAG workflow
from `twinbots/rag/`. The workflow rewrites the incoming query into up to
three variants, routes each to the appropriate Chroma datasource, aggregates
retrieved docs, grades their relevance, then either generates a grounded
response or a fallback.

Usage::

    from fork_engine.twinbots import adaptive_rag
    builder = adaptive_rag()          # uses default paths
    # or
    builder = adaptive_rag(config_path="path/to/config.yaml", chroma_db="./chroma_db")
"""

from typing import Any, Dict, List, Optional

import yaml
from bancobot.agent import BancoAgent, BancoAgentBuilder
from langchain_chroma import Chroma
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from .rag.config import RAGConfig
from .rag.workflow import build_rag_workflow

# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class _RAGBancoAgent(BancoAgent):
    """BancoAgent whose process_message is driven by the adaptive RAG workflow."""

    def __init__(self, workflow: Any, initial_messages: Optional[List] = None) -> None:
        # ponytail: skip BancoAgent.__init__; we own process_message entirely and
        #           don't need the standard LangChain react-agent or its checkpointer.
        self._workflow = workflow
        self._initial_messages: List = list(initial_messages or [])

    def process_message(self, thread_id: str, message: HumanMessage) -> AIMessage:
        msgs = list(self._initial_messages) + [message]
        if self._initial_messages:
            self._initial_messages = []
        result = self._workflow.invoke(
            {"question": str(message.content), "messages": msgs},
            {"configurable": {"thread_id": thread_id}},
        )
        return AIMessage(
            content=result.get("response", ""),
            additional_kwargs={"tool_source": result.get("datasource", "")},
        )


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class _RAGBancoAgentBuilder(BancoAgentBuilder):
    """BancoAgentBuilder that produces a _RAGBancoAgent."""

    def __init__(self, workflow: Any) -> None:
        super().__init__()
        self._rag_workflow = workflow

    def build_with_default(self) -> _RAGBancoAgent:
        return _RAGBancoAgent(self._rag_workflow, self._initial_messages)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_embeddings(config: RAGConfig):
    if config.embedding_config.provider.lower() == "huggingface":
        from langchain_community.embeddings import (
            HuggingFaceEmbeddings,  # type: ignore[import]
        )

        return HuggingFaceEmbeddings(
            model_name=config.embedding_config.model,
            model_kwargs=config.embedding_config.model_kwargs,
        )
    if config.embedding_config.provider.lower() == "openai":
        return OpenAIEmbeddings(model=config.embedding_config.model)
    raise ValueError(
        f"Unsupported embedding provider: {config.embedding_config.provider}"
    )


def _load_vectorstores(config: RAGConfig, chroma_db: str) -> Dict[str, Chroma]:
    embeddings = _make_embeddings(config)
    return {
        ds.name: Chroma(
            persist_directory=chroma_db,
            embedding_function=embeddings,
            collection_name=ds.name,
        )
        for ds in config.datasources
    }


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------


def adaptive_rag(
    config_path: str = "config.yaml",
    chroma_db: str = "./chroma_db",
) -> _RAGBancoAgentBuilder:
    """Return a BancoAgentBuilder backed by the adaptive RAG workflow.

    Args:
        config_path: Path to the RAG config.yaml (default: ``RAG Cartões/config.yaml``).
        chroma_db: Root directory of the persisted Chroma vectorstores.
                   Each datasource is expected at ``<chroma_db>/<datasource_name>/``.

    Returns:
        _RAGBancoAgentBuilder ready to be stored in a ForkConfig.
    """
    with open(config_path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    config = RAGConfig(**raw)

    vectorstores = _load_vectorstores(config, chroma_db)

    llm_kwargs: Dict[str, Any] = {"model": config.llm_config.model}
    if config.llm_config.temperature is not None:
        llm_kwargs["temperature"] = config.llm_config.temperature
    model = ChatOpenAI(**llm_kwargs)

    workflow = build_rag_workflow(config, vectorstores, model)
    return _RAGBancoAgentBuilder(workflow)
