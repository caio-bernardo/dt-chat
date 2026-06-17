import os

from bancobot.agent import (
    BancoAgentBuilder,
    get_vector_store,
    make_search_documentation_tool,
)
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()


BASE_URL = os.environ["VLLM_BASE_URL"]
API_KEY = os.environ["VLLM_API_KEY"]


def local_model():
    """A bancobot with a local model"""
    bancobot = BancoAgentBuilder()

    deepseek = init_chat_model(
        "bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF:Q6_K_L",
        model_provider="openai",
        base_url=BASE_URL,
        api_key=API_KEY,
    )
    bancobot.model = deepseek
    bancobot.toolkit = [make_search_documentation_tool(get_vector_store())]
    return bancobot
