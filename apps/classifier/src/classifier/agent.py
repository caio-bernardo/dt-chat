import os
from typing import Literal, Sequence

from langchain.chat_models import BaseChatModel, init_chat_model
from pydantic import BaseModel

from classifier.log import add_log_entry

# from langchain.agents import create_agent

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]
OLLAMA_API_KEY = os.environ["OLLAMA_API_KEY"]

VLLM_BASE_URL = os.environ.get("VLLM_BASE_URL")
VLLM_API_KEY = os.environ.get("VLLM_API_KEY")


class TouchpointItem(BaseModel):
    subtipo: str
    descricao: str
    exemplo: str


class TouchpointField(BaseModel):
    touchpoint: str
    confianca: Literal["alta", "média", "baixa"]


class TouchpointResponse(BaseModel):
    touchpoints: list[TouchpointField]
    explicacao_geral: str


class ClassifierAgent:
    """Agent Model to Classify touchpoints"""

    def __init__(self, model: str, temperature: float = 0.0):
        # Create agent with restrict token usage
        self._model_name = model
        if model.startswith("ollama:"):
            self._model = self.custom_init_model(
                init_chat_model(
                    model,
                    base_url=OLLAMA_BASE_URL,
                    api_key=OLLAMA_API_KEY,
                )
            )
        elif model.startswith("vllm:"):
            self._model = self.custom_init_model(
                init_chat_model(
                    model.removeprefix("vllm:"),
                    model_provider="openai",
                    base_url=VLLM_BASE_URL,
                    api_key=VLLM_API_KEY,
                )
            )
        else:
            self._model = self.custom_init_model(init_chat_model(model))

    def custom_init_model(self, model: BaseChatModel):
        model_wth_struct = model.with_structured_output(TouchpointResponse)
        return model_wth_struct

    def _build_prompt(
        self, content: str, actor: str, categories: Sequence[TouchpointItem]
    ) -> str:
        """Returns the prompt for the agent with injections"""
        k = 3
        return f"""\
        # Objetivo
        Analisar a mensagem de um `{actor}` em um chatbot bancário e identificar até `{
            k
        }` touchpoints correspondentes, usando exclusivamente os touchpoints fornecidos.

        ]

        # Instruções
        - Escolha **até** `{
            k
        }` touchpoints** da lista acima que melhor descrevem a mensagem.
        - Use **exclusivamente** touchpoints presentes em `**Touchpoints disponíveis**`.
        - Se nenhum touchpoint se aplicar perfeitamente, escolha o **mais próximo**.
        - Para cada touchpoint escolhido, atribua um rótulo de confiança: `"alta"`, `"média"` ou `"baixa"`.
        - Liste os touchpoints escolhidos em uma **ordem total e determinística**.
        - Primeiro, ordene por confiança, nesta ordem: `"alta"`, `"média"`, `"baixa"`.
        - Para touchpoints com o mesmo nível de confiança, aplique os seguintes critérios de desempate, nesta ordem:
            1. **Maior aderência à intenção principal da mensagem**: o touchpoint que melhor representa o pedido, problema ou objetivo central do `{
            actor
        }` deve vir antes.
            2. **Maior especificidade**: o touchpoint mais específico ou exato deve vir antes de um touchpoint mais genérico.
            3. **Maior evidência textual**: o touchpoint com menção mais explícita ou direta na mensagem deve vir antes de um touchpoint inferido de forma mais indireta.
            4. **Maior relevância para a ação atual**: o touchpoint relacionado à necessidade imediata do `{
            actor
        }` deve vir antes de contexto, histórico, causa ou informação acessória.
            5. **Desempate final determinístico**: se ainda houver empate, ordene alfabeticamente pelo nome do touchpoint em maiúsculas, ignorando acentos, espaços extras e pontuação.
            - Nunca use ordem arbitrária para touchpoints empatados.
            - Se houver mais candidatos relevantes do que `{k}`, selecione os `{
            k
        }` primeiros após aplicar a ordenação acima.
            - Use **sempre letras maiúsculas** nos nomes dos touchpoints.

            ## Explicação geral
            - Inclua um único campo externo `"explicacao_geral"`, fora da lista de touchpoints.
            - A `"explicacao_geral"` deve justificar, de maneira objetiva e clara:
                - por que os touchpoints escolhidos representam adequadamente a mensagem analisada;
                - por que os níveis de confiança atribuídos são apropriados.
                - A explicação deve ter **no máximo 3 frases e/ou até 100 palavras**.
                - Seja sucinto e objetivo, sem repetições.
                - Não cite regras, não repita instruções e não seja excessivamente genérico.
                - A explicação deve cobrir brevemente **todos os touchpoints selecionados em conjunto**.

        ## Validação de entrada
        - Se `**Touchpoints disponíveis**` estiver vazio, ausente ou malformado;
        - ou se `{k}` não for um inteiro positivo;
        - ou se `**Mensagem analisada**` estiver vazio ou ausente;
        - retorne um objeto JSON válido com:

        ```json
        {{
        "touchpoints": [],
        "explicacao_geral": "Entrada inválida para classificação."
        }}
        ```

        # Restrições de saída
        - Retorne **apenas** um objeto JSON válido, sem qualquer texto adicional fora do JSON.
        - O objeto JSON deve conter **exatamente** os campos exigidos.
        - A ordem dos campos no objeto JSON não é relevante.

        # Formato de saída
        Retorne um objeto JSON válido com a seguinte estrutura:

        ```json
        {{
        "touchpoints": [
        {{
        "touchpoint": "NOME DO TOUCHPOINT EM MAIÚSCULAS",
        "confianca": "alta"
        }}
        ],
        "explicacao_geral": "Justificativa geral breve para a escolha dos touchpoints e dos níveis de confiança."
        }}
        ```

        ## Requisitos do formato
        - O objeto JSON deve conter obrigatoriamente os campos `"touchpoints"` e `"explicacao_geral"`.
        - `"touchpoints"` deve ser uma lista de objetos.
        - Cada objeto em `"touchpoints"` deve conter **exclusivamente** os campos `"touchpoint"` e `"confianca"`.
        - `"touchpoint"` deve ser um dos touchpoints fornecidos em `**Touchpoints disponíveis**`, escrito em letras maiúsculas.
        - `"confianca"` deve ser exatamente um destes valores: `"alta"`, `"média"` ou `"baixa"`.
        - `"explicacao_geral"` deve ficar fora da lista `"touchpoints"` e respeitar o limite de até 3 frases e/ou 100 palavras.

        ## Caso de entrada inválida
        Se nenhum touchpoint for selecionado por entrada inválida, retorne:

        ```json
        {{
        "touchpoints": [],
        "explicacao_geral": "Entrada inválida para classificação."
        }}
        ```

        # Verificação final
        Antes de responder, confirme que:
            - os touchpoints selecionados vieram exclusivamente de `**Touchpoints disponíveis**`;
            - os nomes dos touchpoints estão em maiúsculas;
            - os níveis de confiança são apenas `"alta"`, `"média"` ou `"baixa"`;
            - a lista está ordenada por confiança, de `"alta"` para `"média"` para `"baixa"`;
            - touchpoints com a mesma confiança foram ordenados pelos critérios de desempate definidos: aderência à intenção principal, especificidade, evidência textual, relevância para a ação atual e, por fim, ordem alfabética normalizada;
            - não há explicações individuais por touchpoint;
            - `"explicacao_geral"` está fora da lista, cobre todas as escolhas e respeita o limite de tamanho;
            - a resposta final contém somente o JSON válido solicitado.

        # Contexto
        **Mensagem analisada**
        `{actor}`: `{content}`

        **Touchpoints disponíveis**
        [{",\n".join([item.model_dump_json() for item in categories])}

        REPOSTA:
        """

    def extract_activity(
        self, response: TouchpointResponse, categories: list[TouchpointItem]
    ) -> str:
        if not response.touchpoints:
            return "INVALID-TOUCHPOINT-SYSTEM"
        subtipos = [item.subtipo for item in categories]
        activity = response.touchpoints[0].touchpoint.upper()
        if activity not in subtipos:
            return "INVALID-TOUCHPOINT-SYSTEM"
        return activity

    async def classify(
        self, msg: str, actor: str, categories: list[TouchpointItem]
    ) -> str:
        """Classify a message from an actor within a category. Returns the selected category."""
        prompt = self._build_prompt(msg, actor, categories)
        response: TouchpointResponse = await self._model.ainvoke(prompt)  # pyright: ignore[reportAssignmentType]

        add_log_entry(actor, msg, self._model_name, response.model_dump(mode="json"))

        return self.extract_activity(response, categories)
