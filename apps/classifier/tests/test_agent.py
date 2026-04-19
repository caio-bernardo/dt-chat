from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from classifier.agent import ClassifierAgent


class TestClassifierAgentInit:
    """Test ClassifierAgent initialization."""

    def test_agent_initialization(self):
        """Test basic agent initialization."""
        with patch("classifier.agent.init_chat_model") as mock_init:
            mock_init.return_value = MagicMock()
            agent = ClassifierAgent(model="gpt-4")
            assert agent is not None
            mock_init.assert_called_once_with("gpt-4", max_tokens=100, temperature=0.0)

    def test_agent_initialization_with_temperature(self):
        """Test agent initialization with custom temperature."""
        with patch("classifier.agent.init_chat_model") as mock_init:
            mock_init.return_value = MagicMock()
            agent = ClassifierAgent(model="gpt-4", temperature=0.7)  # pyright: ignore[reportUnusedVariable]
            mock_init.assert_called_once_with("gpt-4", max_tokens=100, temperature=0.7)


class TestPromptBuilding:
    """Test prompt construction."""

    def test_build_prompt_content(self):
        """Test that prompt is built with correct content."""
        with patch("classifier.agent.init_chat_model"):
            agent = ClassifierAgent(model="gpt-4")
            prompt = agent._build_prompt(
                "Qual é o meu saldo?",
                "Human",
                ["SALDO_CONSULTA", "TRANSFERENCIA"],
            )

            assert "Qual é o meu saldo?" in prompt
            assert "human" in prompt.lower()
            assert "SALDO_CONSULTA" in prompt
            assert "TRANSFERENCIA" in prompt

    def test_build_prompt_structure(self):
        """Test prompt has required sections."""
        with patch("classifier.agent.init_chat_model"):
            agent = ClassifierAgent(model="gpt-4")
            prompt = agent._build_prompt(
                "Test message", "AI", ["CATEGORY_A", "CATEGORY_B"]
            )

            assert "MENSAGEM:" in prompt
            assert "TOUCHPOINTS DISPONÍVEIS:" in prompt
            assert "INSTRUÇÕES:" in prompt
            assert "TOUCHPOINT:" in prompt


class TestClassification:
    """Test message classification."""

    @pytest.mark.asyncio
    async def test_classify_success(self):
        """Test successful classification."""
        with patch("classifier.agent.init_chat_model") as mock_init:
            mock_agent = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "SALDO_CONSULTA"
            mock_agent.ainvoke = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_agent

            agent = ClassifierAgent(model="gpt-4")
            result = await agent.classify(
                "Qual é o meu saldo?",
                "Human",
                ["SALDO_CONSULTA", "TRANSFERENCIA"],
            )

            assert result == "SALDO_CONSULTA"
            mock_agent.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_with_quotes(self):
        """Test classification handles quoted responses."""
        with patch("classifier.agent.init_chat_model") as mock_init:
            mock_agent = MagicMock()
            mock_response = MagicMock()
            mock_response.content = '"SALDO_CONSULTA"'
            mock_agent.ainvoke = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_agent

            agent = ClassifierAgent(model="gpt-4")
            result = await agent.classify(
                "Test message", "Human", ["SALDO_CONSULTA", "TRANSFERENCIA"]
            )

            assert result == "SALDO_CONSULTA"

    @pytest.mark.asyncio
    async def test_classify_lowercase_converted(self):
        """Test classification converts lowercase to uppercase."""
        with patch("classifier.agent.init_chat_model") as mock_init:
            mock_agent = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "saldo_consulta"
            mock_agent.ainvoke = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_agent

            agent = ClassifierAgent(model="gpt-4")
            result = await agent.classify(
                "Test", "Human", ["SALDO_CONSULTA", "TRANSFERENCIA"]
            )

            assert result == "SALDO_CONSULTA"

    @pytest.mark.asyncio
    async def test_classify_invalid_category_raises_error(self):
        """Test classification fails with invalid category."""
        with patch("classifier.agent.init_chat_model") as mock_init:
            mock_agent = MagicMock()
            mock_response = MagicMock()
            mock_response.content = "INVALID_CATEGORY"
            mock_agent.ainvoke = AsyncMock(return_value=mock_response)
            mock_init.return_value = mock_agent

            agent = ClassifierAgent(model="gpt-4")

            with pytest.raises(ValueError, match="Invalid Category"):
                await agent.classify(
                    "Test", "Human", ["SALDO_CONSULTA", "TRANSFERENCIA"]
                )
