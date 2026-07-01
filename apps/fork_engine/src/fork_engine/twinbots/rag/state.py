from typing import List, Optional

from langgraph.graph import MessagesState


class RAGState(MessagesState):
    """State for the adaptive RAG workflow.

    Inherits `messages: Annotated[List[AnyMessage], add_messages]` from MessagesState.
    Additional fields track the multi-query loop and document grading.
    """

    question: str
    datasource: Optional[str]
    context: List[str]
    relevant_context: List[str]
    documents_relevant: bool
    response: Optional[str]
    # query rewriting + loop
    original_question: str
    rewritten_queries: List[str]
    current_query_index: int
    aggregated_docs: List[str]
    has_more_queries: bool
