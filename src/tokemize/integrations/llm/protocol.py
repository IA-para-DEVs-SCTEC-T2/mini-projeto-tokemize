"""Protocolo de interface comum para clientes de LLM na camada integrations/llm/."""

from typing import Protocol


class LLMClientProtocol(Protocol):
    """Protocolo que define a interface comum para todos os clientes de LLM.

    Qualquer classe que implemente o método ``complete`` com a assinatura
    correta é estruturalmente compatível com este protocolo (duck typing),
    sem necessidade de herança explícita.

    Example:
        >>> class MyClient:
        ...     def complete(self, prompt: str) -> str:
        ...         return "resposta"
        >>> def use_client(client: LLMClientProtocol) -> str:
        ...     return client.complete("olá")
    """

    def complete(self, prompt: str) -> str:
        """Envia um prompt ao LLM e retorna a resposta como str.

        Args:
            prompt: Texto de entrada para o modelo.

        Returns:
            Texto da resposta gerada pelo modelo.
        """
        ...
