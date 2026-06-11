import os
from typing import Literal

from langchain.chat_models import BaseChatModel, init_chat_model
from pydantic import BaseModel

from classifier.log import add_log_entry

# from langchain.agents import create_agent

OLLAMA_BASE_URL = os.environ["OLLAMA_BASE_URL"]


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
                    max_tokens=100,
                    temperature=temperature,
                    base_url=OLLAMA_BASE_URL,
                )
            )
        else:
            self._model = self.custom_init_model(
                init_chat_model(model, max_tokens=100, temperature=temperature)
            )

    def custom_init_model(self, model: BaseChatModel):
        model_wth_struct = model.with_structured_output(TouchpointResponse)
        return model_wth_struct

    def _build_prompt(
        self, content: str, actor: str, categories: list[TouchpointItem]
    ) -> str:
        """Returns the prompt for the agent with injections"""
        k = 3
        return f"""\
            # Objetivo
            Analisar a mensagem de um `{
            actor
        }` em um chatbot bancário e identificar até `{
            k
        }` touchpoints correspondentes, usando exclusivamente os touchpoints fornecidos.

            # Contexto
            **Mensagem analisada**
            `{actor}: {content}`

            **Touchpoints disponíveis**
            [{",\n".join([item.model_dump_json() for item in categories])}]


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

            REPOSTA:
        """

    async def classify(
        self, msg: str, actor: str, categories: list[TouchpointItem]
    ) -> str:
        """Classify a message from an actor within a category. Returns the selected category."""
        prompt = self._build_prompt(msg, actor, categories)
        response: TouchpointResponse = await self._model.ainvoke(prompt)

        add_log_entry(actor, msg, self._model_name, response.model_dump(mode="json"))

        if not response.touchpoints:
            return "INVALID-TOUCHPOINT-SYSTEM"

        subtipos = [item.subtipo for item in categories]
        activity = response.touchpoints[0].subtipo
        if activity not in subtipos:
            return "INVALID-TOUCHPOINT-SYSTEM"

        return activity


# class DemocraticClassifierAgent(ClassifierAgent):
#     """Initialize N models and attempts to classify the data, the most voted touchpoints wins."""

#     def __init__(self, llms: list[str], temperature: float = 0.0):
#         # NOTE: trocar a url dos modelos ollama
#         self._models = {}
#         for llm in llms:
#             if "ollama" in llm:
#                 self._models[llm] = init_chat_model(llm, base_url=OLLAMA_BASE_URL)
#             else:
#                 self._models[llm] = init_chat_model(llm)

#     def init_agent(self, model: BaseChatModel):
#         model_wth_struct = model.with_structured_output(TouchpointResponse)
#         return model_wth_struct

#     async def classify(
#         self, msg: str, actor: str, categories: list[TouchpointItem]
#     ) -> str:
#         """Classifica os touchpoints com base em um sistema de voto, cada modelo faz sua classificação e a classe mais votada ganha"""

#         ## Run asyncronous tasks independently and uses
#         import asyncio

#         agents = {name: self.init_agent(model) for name, model in self._models.items()}

#         subtipos = {cat.subtipo for cat in categories}
#         activities: list[str] = []

#         async def _run_one(name: str, model):
#             prompt = self._build_prompt(msg, actor, categories)
#             response: TouchpointResponse = await model.ainvoke(  # pyright: ignore[reportAssignmentType]
#                 prompt
#             )
#             return name, response

#         # Executa as chamadas aos modelos em paralelo e as resume no final
#         tasks = [
#             asyncio.create_task(_run_one(name, model)) for name, model in agents.items()
#         ]
#         results = await asyncio.gather(*tasks, return_exceptions=True)

#         debug_results = {}
#         for result in results:
#             # Se algum modelo falhar, apenas ignoramos e seguimos com os demais
#             if isinstance(result, Exception):
#                 print(f"DEBUG: model invocation failed: {result}")
#                 continue

#             name, response = result  # pyright: ignore[reportGeneralTypeIssues]
#             debug_results[name] = response.model_dump(mode="json")

#             # Ignore models that failed to categorize
#             if len(response.touchpoints) > 0:
#                 activity = response.touchpoints[0].touchpoint
#                 # TODO: podemos usar agentes e definer os touchpoints como
#                 # variantes de enum para aumetar a tolerância a falhas, mas com o
#                 # sistema de votação a chance de falha cai bastante.
#                 if activity in subtipos:
#                     # print(f"DEBUG: {name} -> {activity}")
#                     activities.append(activity)
#                 else:
#                     print(f"DEBUG: {name} produced invalid touchpoint: {activity}")

#         add_log_entry(
#             actor,
#             msg,
#             debug_results,
#         )
#         # If all models failed to categorize a touchpoint we fail
#         if len(activities) == 0:
#             return "INVALID-TOUCHPOINT-SYSTEM"
#         # Uses the most common category
#         return max(set(activities), key=activities.count)
