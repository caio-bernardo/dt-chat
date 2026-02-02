from langchain.chat_models import init_chat_model


class ClassifierAgent:
    def __init__(self, model: str, temperature: float = 0.0):
        # Create agent with restrict token usage
        self.agent = init_chat_model(model, max_tokens=100, temperature=temperature)

    def _build_prompt(self, content: str, actor: str, categories: list[str]) -> str:
        return f"""\
                Analise a seguinte mensagem de um {actor.lower()} em um chatbot bancário e identifique
                o TOUCHPOINT correspondente usando EXCLUSIVAMENTE os touchpoints listados abaixo.

                MENSAGEM:
                {actor}: {content}

                TOUCHPOINTS DISPONÍVEIS:
                {"\n".join(categories)}

                INSTRUÇÕES:
                - Escolha APENAS UM touchpoint da lista acima que melhor descreve a mensagem
                - Se nenhum touchpoint se aplicar perfeitamente, escolha o mais próximo
                - Use SEMPRE letras maiúsculas
                - Retorne APENAS o nome do touchpoint, sem explicações adicionais

                TOUCHPOINT:"""

    async def classify(self, msg: str, actor: str, categories: list[str]) -> str:
        """Classify a message from actor within a category. Returns the selected category."""
        prompt = self._build_prompt(msg, actor, categories)
        response = await self.agent.ainvoke(prompt)
        category = str(response.content).strip().strip("'").strip('"').upper()
        if category not in categories:
            raise ValueError("Produced Invalid Category.")
        return category
