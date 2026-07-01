"""Adaptive RAG workflow: query rewriting → routing → retrieval loop → grading → response.

All node functions live here to keep the submodule minimal.
"""

from typing import Any, Dict, List

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from .config import RAGConfig
from .state import RAGState

_MAX_REWRITTEN_QUERIES = 3


# ---------------------------------------------------------------------------
# Node factories (closures capturing config / model / retrievers)
# ---------------------------------------------------------------------------


def _make_rewrite_query(config: RAGConfig, model: BaseChatModel):
    system = config.global_prompts.rewrite_query_prompt

    def rewrite_query(state: RAGState) -> Dict[str, Any]:
        question = state.get("question", "")
        if not question:
            return {
                "original_question": "",
                "rewritten_queries": [],
                "current_query_index": 0,
                "has_more_queries": False,
            }
        try:
            result = model.invoke(
                [SystemMessage(content=system), HumanMessage(content=question)]
            )
            raw = str(result.content)
            queries: List[str] = []
            for line in raw.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line[0].isdigit() and "." in line:
                    q = line.split(".", 1)[-1].strip()
                elif line.startswith("- "):
                    q = line[2:].strip()
                else:
                    continue
                if q:
                    queries.append(q)
            if not queries:
                queries = [raw.strip()]
            queries = queries[:_MAX_REWRITTEN_QUERIES]
        except Exception:
            queries = [question]
        return {
            "original_question": question,
            "rewritten_queries": queries,
            "current_query_index": 0,
            "has_more_queries": bool(queries),
        }

    return rewrite_query


def _make_router(config: RAGConfig, datasource_names: List[str], model: BaseChatModel):
    desc_lines = []
    for ds in config.datasources:
        if ds.name in datasource_names:
            desc_lines.append(f"- '{ds.name}': {ds.description or ''}")
    desc_str = "\n".join(desc_lines)

    system = config.global_prompts.router_prompt
    if "{datasource_descriptions}" in system:
        system = system.replace("{datasource_descriptions}", desc_str)
    else:
        system += f"\n\nAvailable datasources:\n{desc_str}"

    prompt = ChatPromptTemplate.from_messages(
        [("system", system), ("human", "{question}")]
    )

    class _RouteQuery(BaseModel):
        datasource: str = Field(
            ..., description="Most relevant datasource for the query"
        )

    chain = prompt | model.with_structured_output(
        _RouteQuery, method="function_calling"
    )

    def route(state: RAGState) -> Dict[str, Any]:
        question = state.get("question", "")
        try:
            result = chain.invoke({"question": question})
            selected = getattr(result, "datasource", datasource_names[0])
            ds = selected if selected in datasource_names else datasource_names[0]
        except Exception:
            ds = datasource_names[0]
        return {"datasource": ds, "messages": [HumanMessage(content=question)]}

    return route


def _make_retriever(retrievers: Dict[str, Any]):
    def retrieve(state: RAGState) -> Dict[str, Any]:
        datasource = state.get("datasource")
        question = state.get("question", "")
        if not datasource or datasource not in retrievers:
            datasource = next(iter(retrievers), None)
        if not datasource or not question:
            return {"context": []}
        try:
            docs = retrievers[datasource].invoke(question)
            return {"context": [d.page_content for d in docs]}
        except Exception:
            return {"context": []}

    return retrieve


def _make_grader(config: RAGConfig, model: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", config.global_prompts.grader_prompt),
            ("human", "Retrieved document:\n\n{document}\n\nUser question: {question}"),
        ]
    )

    class _GradeDoc(BaseModel):
        binary_score: str = Field(..., description="'yes' or 'no'")

    chain = prompt | model.with_structured_output(_GradeDoc, method="function_calling")

    def grade(state: RAGState) -> Dict[str, Any]:
        context = state.get("context", [])
        question = state.get("question", "")
        if not context or not question:
            return {"documents_relevant": False, "relevant_context": []}
        relevant: List[str] = []
        for doc in context:
            if not doc.strip():
                continue
            try:
                result = chain.invoke({"question": question, "document": doc})
                score = getattr(result, "binary_score", "no")
                if score.lower() == "yes":
                    relevant.append(doc)
            except Exception:
                pass
        return {"documents_relevant": bool(relevant), "relevant_context": relevant}

    return grade


def _make_responder(config: RAGConfig, model: BaseChatModel):
    ds_prompts = {ds.name: ds.prompt_templates.rag_prompt for ds in config.datasources}

    def respond(state: RAGState) -> Dict[str, Any]:
        question = state.get("question", "")
        datasource = state.get("datasource") or ""
        relevant_context = state.get("relevant_context", [])
        messages = state.get("messages", [])

        if not relevant_context:
            ai = AIMessage(content="No relevant information found.")
            return {"response": ai.content, "messages": [ai]}

        template = ds_prompts.get(datasource, "{context}\n{question}")
        system_content = template.format(
            context="\n\n".join(relevant_context), question=question
        )
        try:
            ai = model.invoke([SystemMessage(content=system_content)] + messages)
            return {"response": ai.content, "messages": [ai]}
        except Exception:
            ai = AIMessage(content="Error generating response.")
            return {"response": ai.content, "messages": [ai]}

    return respond


def _make_fallback(config: RAGConfig, model: BaseChatModel):
    system = config.global_prompts.fallback_prompt

    def fallback(state: RAGState) -> Dict[str, Any]:
        messages = state.get("messages", [])
        try:
            ai = model.invoke([SystemMessage(content=system)] + messages)
            return {"response": ai.content, "messages": [ai]}
        except Exception:
            ai = AIMessage(content="Could not find relevant information.")
            return {"response": ai.content, "messages": [ai]}

    return fallback


# ---------------------------------------------------------------------------
# Pure node functions (stateless helpers, no closures needed)
# ---------------------------------------------------------------------------


def _prepare_next_query(state: RAGState) -> Dict[str, Any]:
    queries = state.get("rewritten_queries", [])
    idx = state.get("current_query_index", 0)
    return {
        "question": queries[idx]
        if idx < len(queries)
        else state.get("original_question", "")
    }


def _aggregate_docs(state: RAGState) -> Dict[str, Any]:
    idx = state.get("current_query_index", 0)
    queries = state.get("rewritten_queries", [])
    context = state.get("context", [])
    aggregated = list(state.get("aggregated_docs", []))
    for doc in context:
        if doc not in aggregated:
            aggregated.append(doc)
    next_idx = idx + 1
    return {
        "current_query_index": next_idx,
        "aggregated_docs": aggregated,
        "has_more_queries": next_idx < len(queries),
    }


def _prepare_for_grading(state: RAGState) -> Dict[str, Any]:
    return {
        "question": state.get("original_question", ""),
        "context": state.get("aggregated_docs", []),
    }


def _cleanup(state: RAGState) -> Dict[str, Any]:
    return {"aggregated_docs": []}


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------


def _should_continue_loop(state: RAGState) -> str:
    if state.get("has_more_queries"):
        idx = state.get("current_query_index", 0)
        if idx < len(state.get("rewritten_queries", [])):
            return "continue_loop"
    return "finish_loop"


def _decide_next_step(state: RAGState) -> str:
    return (
        "relevant"
        if state.get("documents_relevant") and state.get("relevant_context")
        else "irrelevant"
    )


# ---------------------------------------------------------------------------
# Public builder
# ---------------------------------------------------------------------------


def build_rag_workflow(
    config: RAGConfig,
    vectorstores: Dict[str, Any],
    model: BaseChatModel,
):
    """Build and compile the adaptive RAG StateGraph.

    Args:
        config: RAGConfig loaded from config.yaml.
        vectorstores: Mapping of datasource name → Chroma vectorstore (already initialised).
        model: LLM used for all reasoning steps.

    Returns:
        Compiled LangGraph workflow with InMemorySaver checkpointer.
    """
    # Build retrievers from vectorstores, honouring each datasource's retriever_config.
    retrievers: Dict[str, Any] = {}
    for ds in config.datasources:
        if ds.name not in vectorstores:
            continue
        rc = ds.retriever_config
        search_kwargs: Dict[str, Any] = {}
        if rc.top_k:
            search_kwargs["k"] = rc.top_k
        if rc.search_type == "mmr":
            if rc.fetch_k:
                search_kwargs["fetch_k"] = rc.fetch_k
            if rc.lambda_mult is not None:
                search_kwargs["lambda_mult"] = rc.lambda_mult
        if rc.score_threshold is not None:
            search_kwargs["score_threshold"] = rc.score_threshold
        retrievers[ds.name] = vectorstores[ds.name].as_retriever(
            search_type=rc.search_type, search_kwargs=search_kwargs
        )

    datasource_names = list(retrievers.keys())

    graph = StateGraph(RAGState)

    graph.add_node("rewrite_query", _make_rewrite_query(config, model))
    graph.add_node("prepare_next_query", _prepare_next_query)
    graph.add_node("route", _make_router(config, datasource_names, model))
    graph.add_node("retrieve", _make_retriever(retrievers))
    graph.add_node("aggregate_docs", _aggregate_docs)
    graph.add_node("prepare_for_grading", _prepare_for_grading)
    graph.add_node("grade", _make_grader(config, model))
    graph.add_node("respond_with_relevant", _make_responder(config, model))
    graph.add_node("respond_with_fallback", _make_fallback(config, model))
    graph.add_node("cleanup", _cleanup)

    graph.set_entry_point("rewrite_query")
    graph.add_edge("rewrite_query", "prepare_next_query")
    graph.add_edge("prepare_next_query", "route")
    graph.add_edge("route", "retrieve")
    graph.add_edge("retrieve", "aggregate_docs")
    graph.add_conditional_edges(
        "aggregate_docs",
        _should_continue_loop,
        {"continue_loop": "prepare_next_query", "finish_loop": "prepare_for_grading"},
    )
    graph.add_edge("prepare_for_grading", "grade")
    graph.add_conditional_edges(
        "grade",
        _decide_next_step,
        {"relevant": "respond_with_relevant", "irrelevant": "respond_with_fallback"},
    )
    graph.add_edge("respond_with_relevant", "cleanup")
    graph.add_edge("respond_with_fallback", "cleanup")
    graph.add_edge("cleanup", END)

    return graph.compile(checkpointer=InMemorySaver())
