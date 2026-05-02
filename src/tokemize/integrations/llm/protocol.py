"""Protocolo de interface para clientes de LLM."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Protocolo abstrato para clientes de LLM.

    Define a interface mínima que qualquer cliente de LLM deve implementar
    para ser compatível com o pipeline Tokemize. Implementações concretas
    residem em módulos específicos deste pacote (ex: openai_client.py,
    anthropic_client.py).

    Example:
        >>> class MyLLMClient:
        ...     def complete(self, prompt: str) -> str:
        ...         return "resposta do LLM"
        >>> isinstance(MyLLMClient(), LLMClientProtocol)
        True
    """

    def complete(self, prompt: str) -> str:
        """Envia um prompt ao LLM e retorna a resposta como string.

        Args:
            prompt: Texto do prompt a ser enviado ao modelo.

        Returns:
            Resposta gerada pelo modelo como string.

        Raises:
            Exception: Qualquer exceção de comunicação ou autenticação
                lançada pelo provedor de LLM.
        """
        ...
