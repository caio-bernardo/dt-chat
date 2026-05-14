from bancobot.agent import BancoAgentBuilder


def no_rag():
    """A bancobot with no RAG capabilities"""
    bancobot = BancoAgentBuilder()
    return bancobot
