import pytest
import uuid
from unittest.mock import Mock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_core.vectorstores import VectorStore
from langgraph.types import Checkpointer

from bancobot.agent import (
    BancoAgent,
    make_search_documentation_tool,
    BANCO_BOT_SYSTEM_PROMPT,
)


class TestBancoAgent:
    """Test cases for the BancoAgent class"""

    @patch("bancobot.agent.create_agent")
    def test_agent_initialization_with_string_model(self, mock_create_agent):
        """Test agent initialization with string model name"""
        # Setup
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent

        # Act
        agent = BancoAgent(model="gpt-4", toolkit=[], saver=None)

        # Assert
        mock_create_agent.assert_called_once_with(
            model="gpt-4",
            tools=[],
            system_prompt=BANCO_BOT_SYSTEM_PROMPT,
            checkpointer=None,
        )
        assert agent.agent == mock_agent

    @patch("bancobot.agent.create_agent")
    def test_agent_initialization_with_model_object(self, mock_create_agent):
        """Test agent initialization with model object"""
        # Setup
        mock_model = Mock()
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent
        mock_tools = [Mock(spec=BaseTool)]
        mock_saver = Mock(spec=Checkpointer)

        # Act
        _ = BancoAgent(model=mock_model, toolkit=mock_tools, saver=mock_saver)

        # Assert
        mock_create_agent.assert_called_once_with(
            model=mock_model,
            tools=mock_tools,
            system_prompt=BANCO_BOT_SYSTEM_PROMPT,
            checkpointer=mock_saver,
        )

    @patch("bancobot.agent.create_agent")
    def test_agent_initialization_with_custom_prompt(self, mock_create_agent):
        """Test agent initialization with custom prompt"""
        # Setup
        custom_prompt = "Custom system prompt"
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent

        # Act
        _ = BancoAgent(model="gpt-4", prompt_eng=custom_prompt)

        # Assert
        mock_create_agent.assert_called_once_with(
            model="gpt-4", tools=[], system_prompt=custom_prompt, checkpointer=None
        )

    @patch("bancobot.agent.create_agent")
    def test_agent_initialization_with_system_message_prompt(self, mock_create_agent):
        """Test agent initialization with SystemMessage prompt"""
        # Setup
        custom_prompt = SystemMessage(content="Custom system message")
        mock_agent = Mock()
        mock_create_agent.return_value = mock_agent

        # Act
        _ = BancoAgent(model="gpt-4", prompt_eng=custom_prompt)

        # Assert
        mock_create_agent.assert_called_once_with(
            model="gpt-4", tools=[], system_prompt=custom_prompt, checkpointer=None
        )

    @patch("bancobot.agent.create_agent")
    def test_process_message_success(self, mock_create_agent):
        """Test successful message processing"""
        # Setup
        mock_agent = Mock()
        mock_ai_message = AIMessage(content="AI response")
        mock_agent.invoke.return_value = {
            "messages": [HumanMessage(content="Test"), mock_ai_message]
        }
        mock_create_agent.return_value = mock_agent

        agent = BancoAgent(model="gpt-4")
        thread_id = uuid.uuid4()
        human_message = HumanMessage(content="Hello")

        # Act
        result = agent.process_message(thread_id, human_message)

        # Assert
        assert result == mock_ai_message
        mock_agent.invoke.assert_called_once_with(
            {"messages": [human_message]}, {"configurable": {"thread_id": thread_id}}
        )

    @patch("bancobot.agent.create_agent")
    def test_process_message_with_multiple_messages_in_response(
        self, mock_create_agent
    ):
        """Test message processing when agent returns multiple messages"""
        # Setup
        mock_agent = Mock()
        messages = [
            HumanMessage(content="Input"),
            AIMessage(content="Intermediate"),
            AIMessage(content="Final response"),
        ]
        mock_agent.invoke.return_value = {"messages": messages}
        mock_create_agent.return_value = mock_agent

        agent = BancoAgent(model="gpt-4")
        thread_id = uuid.uuid4()
        human_message = HumanMessage(content="Complex query")

        # Act
        result = agent.process_message(thread_id, human_message)

        # Assert
        assert result == messages[-1]  # Should return the last message
        assert result.content == "Final response"


    @patch("bancobot.agent.create_agent")
    def test_process_message_agent_exception(self, mock_create_agent):
        """Test handling agent exceptions during message processing"""
        # Setup
        mock_agent = Mock()
        mock_agent.invoke.side_effect = Exception("Agent processing failed")
        mock_create_agent.return_value = mock_agent

        agent = BancoAgent(model="gpt-4")
        thread_id = uuid.uuid4()
        human_message = HumanMessage(content="Error test")

        # Act & Assert
        with pytest.raises(Exception, match="Agent processing failed"):
            agent.process_message(thread_id, human_message)

    def test_default_system_prompt_content(self):
        """Test that the default system prompt contains expected content"""
        prompt_content = BANCO_BOT_SYSTEM_PROMPT.content

        # Assert key elements are present
        assert "chatbot de banco" in prompt_content
        assert "programas de fidelidade" in prompt_content
        assert "cartões de crédito" in prompt_content
        assert "banco X" in prompt_content
        assert "ferramenta para buscar documentação" in prompt_content

    def test_default_system_prompt_type(self):
        """Test that the default system prompt is a SystemMessage"""
        assert isinstance(BANCO_BOT_SYSTEM_PROMPT, SystemMessage)


class TestMakeSearchDocumentationTool:
    """Test cases for the make_search_documentation_tool function"""

    def test_make_search_documentation_tool_creation(self):
        """Test creating search documentation tool"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)

        # Act
        tool = make_search_documentation_tool(mock_vector_store)

        # Assert
        assert isinstance(tool, BaseTool)
        assert tool.name == "search_documentation"
        assert "Retrieve bank X's information" in tool.description

    def test_search_documentation_tool_execution(self):
        """Test executing the search documentation tool"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)
        mock_docs = [
            Mock(page_content="Document 1 content"),
            Mock(page_content="Document 2 content"),
            Mock(page_content="Document 3 content"),
        ]
        mock_vector_store.similarity_search.return_value = mock_docs

        tool = make_search_documentation_tool(mock_vector_store)

        # Act
        result = tool.run("test query")

        # Assert
        mock_vector_store.similarity_search.assert_called_once_with("test query")
        # Result should be the concatenated content
        expected_content = (
            "Document 1 content\n\nDocument 2 content\n\nDocument 3 content"
        )
        assert result == expected_content

    def test_search_documentation_tool_empty_results(self):
        """Test search documentation tool with no results"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)
        mock_vector_store.similarity_search.return_value = []

        tool = make_search_documentation_tool(mock_vector_store)

        # Act
        result = tool.run("no results query")

        # Assert
        assert result == ""

    def test_search_documentation_tool_single_document(self):
        """Test search documentation tool with single document"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)
        mock_doc = Mock(page_content="Single document content")
        mock_vector_store.similarity_search.return_value = [mock_doc]

        tool = make_search_documentation_tool(mock_vector_store)

        # Act
        result = tool.run("single doc query")

        # Assert
        assert result == "Single document content"

    def test_search_documentation_tool_vector_store_exception(self):
        """Test handling vector store exceptions"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)
        mock_vector_store.similarity_search.side_effect = Exception(
            "Vector store error"
        )

        tool = make_search_documentation_tool(mock_vector_store)

        # Act & Assert
        with pytest.raises(Exception, match="Vector store error"):
            tool.run("error query")

    def test_search_documentation_tool_response_format(self):
        """Test that the tool has correct response format"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)
        tool = make_search_documentation_tool(mock_vector_store)

        # Assert
        # Check if the tool was created with response_format (this is implementation dependent)
        assert hasattr(tool, "response_format") or hasattr(tool, "_response_format")

    def test_search_documentation_tool_with_different_queries(self):
        """Test search tool with various query types"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)
        mock_docs = [Mock(page_content="Relevant content")]
        mock_vector_store.similarity_search.return_value = mock_docs

        tool = make_search_documentation_tool(mock_vector_store)

        # Test different query types
        queries = [
            "Como posso transferir dinheiro?",
            "cartão de crédito",
            "programa de fidelidade",
            "What are the fees?",
            "",  # Empty query
            "Very long query with lots of details about banking services and fees and transfers",
        ]

        for query in queries:
            result = tool.run(query)
            assert isinstance(result, str)
            mock_vector_store.similarity_search.assert_called_with(query)

    def test_search_documentation_tool_document_content_formatting(self):
        """Test proper formatting of multiple documents"""
        # Setup
        mock_vector_store = Mock(spec=VectorStore)
        mock_docs = [
            Mock(page_content="First document\nwith multiple lines"),
            Mock(page_content="Second document"),
            Mock(page_content="Third document\nwith more\ncontent"),
        ]
        mock_vector_store.similarity_search.return_value = mock_docs

        tool = make_search_documentation_tool(mock_vector_store)

        # Act
        result = tool.run("formatting test")

        # Assert
        expected = (
            "First document\nwith multiple lines\n\n"
            "Second document\n\n"
            "Third document\nwith more\ncontent"
        )
        assert result == expected
