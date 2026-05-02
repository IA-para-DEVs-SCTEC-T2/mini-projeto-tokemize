"""Camada de integração com provedores de LLM.

Exporta o protocolo de interface e os clientes concretos disponíveis.
"""

from tokemize.integrations.llm.protocol import LLMClientProtocol
from tokemize.integrations.llm.groq_client import GroqClient

__all__ = ["LLMClientProtocol", "GroqClient"]
