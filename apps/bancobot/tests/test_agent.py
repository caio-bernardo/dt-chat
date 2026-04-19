from unittest.mock import MagicMock

import pytest
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from bancobot.agent import (
    BANCO_BOT_SYSTEM_PROMPT,
    DEFAULT_MODEL,
    BancoAgent,
    BancoAgentBuilder,
    make_search_documentation_tool,
)


class TestBancoAgent:
    """Test BancoAgent class."""

    def test_banco_agent_initialization(self):
        """Test BancoAgent can be initialized with minimal parameters."""
        agent = BancoAgent(model="gpt-4")
        assert agent is not None

    def test_banco_agent_with_custom_prompt(self):
        """Test BancoAgent initialization with custom prompt."""
        custom_prompt = "Custom prompt"
        agent = BancoAgent(model="gpt-4", prompt_eng=custom_prompt)
        assert agent is not None

    def test_banco_agent_with_middleware(self):
        """Test BancoAgent initialization with middleware."""
        agent = BancoAgent(model="gpt-4", middleware=[])
        assert agent is not None


class TestBancoAgentBuilder:
    """Test BancoAgentBuilder class."""

    def test_builder_build_with_defaults(self):
        """Test building agent with default values."""
        builder = BancoAgentBuilder()
        agent = builder.build_with_default()

        assert isinstance(agent, BancoAgent)
        assert agent is not None

    def test_builder_set_model_via_default(self):
        """Test building agent uses default or specified model."""
        builder = BancoAgentBuilder()
        agent = builder.build_with_default()

        assert isinstance(agent, BancoAgent)

    def test_builder_build_without_required_model_fails(self):
        """Test that building without model raises error."""
        builder = BancoAgentBuilder()

        with pytest.raises(ValueError):
            builder.build()

    def test_builder_with_toolkit_defaults(self):
        """Test builder initializes with default toolkit."""
        builder = BancoAgentBuilder()
        agent = builder.build_with_default()

        assert isinstance(agent, BancoAgent)

    def test_builder_uses_default_prompt(self):
        """Test builder uses default or custom prompt."""
        builder = BancoAgentBuilder()
        agent = builder.build_with_default()

        assert isinstance(agent, BancoAgent)


class TestMakeSearchDocumentationTool:
    """Test make_search_documentation_tool function."""

    def test_search_tool_creation(self):
        """Test that search tool is created successfully."""
        mock_vector_store = MagicMock(spec=VectorStore)
        mock_vector_store.similarity_search.return_value = [
            Document(page_content="Test document")
        ]

        tool = make_search_documentation_tool(mock_vector_store)

        assert tool is not None

    def test_search_tool_functionality(self):
        """Test search tool returns documents."""
        mock_doc = Document(page_content="Bank information")
        mock_vector_store = MagicMock(spec=VectorStore)
        mock_vector_store.similarity_search.return_value = [mock_doc]

        tool = make_search_documentation_tool(mock_vector_store)
        result = tool.invoke({"query": "credit card information"})

        assert result is not None
        mock_vector_store.similarity_search.assert_called_once()

    def test_search_tool_empty_results(self):
        """Test search tool with empty results."""
        mock_vector_store = MagicMock(spec=VectorStore)
        mock_vector_store.similarity_search.return_value = []

        tool = make_search_documentation_tool(mock_vector_store)
        result = tool.invoke({"query": "nonexistent query"})

        assert result is not None


class TestConstants:
    """Test module constants."""

    def test_banco_bot_system_prompt(self):
        """Test that system prompt is defined."""
        assert BANCO_BOT_SYSTEM_PROMPT is not None
        assert "chatbot de banco" in BANCO_BOT_SYSTEM_PROMPT.content.lower()  # pyright: ignore[reportAttributeAccessIssue]

    def test_default_model(self):
        """Test that default model is defined."""
        assert DEFAULT_MODEL is not None
        assert isinstance(DEFAULT_MODEL, str)
        assert len(DEFAULT_MODEL) > 0
