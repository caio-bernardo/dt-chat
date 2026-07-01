from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RetrieverConfig(BaseModel):
    search_type: str = "similarity"
    top_k: int = 3
    fetch_k: Optional[int] = None
    lambda_mult: Optional[float] = None
    score_threshold: Optional[float] = None


class PromptTemplates(BaseModel):
    rag_prompt: str


class Datasource(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    folders: List[str]
    prompt_templates: PromptTemplates
    retriever_config: RetrieverConfig


class GlobalPrompts(BaseModel):
    router_prompt: str
    grader_prompt: str
    fallback_prompt: str
    rewrite_query_prompt: str


class EmbeddingConfig(BaseModel):
    model: str
    provider: str = "openai"
    batch_size: Optional[int] = None
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)


class VectorstoreConfig(BaseModel):
    provider: str
    persist_directory: str


class LLMConfig(BaseModel):
    model: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


class TextSplitterConfig(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 100


class RAGConfig(BaseModel):
    version: str
    datasources: List[Datasource]
    global_prompts: GlobalPrompts
    embedding_config: EmbeddingConfig
    vectorstore_config: VectorstoreConfig
    llm_config: LLMConfig
    text_splitter: TextSplitterConfig = Field(default_factory=TextSplitterConfig)
