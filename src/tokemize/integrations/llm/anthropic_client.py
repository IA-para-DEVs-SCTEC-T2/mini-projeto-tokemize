"""Cliente de LLM para a API Anthropic."""

import logging
import os

import anthropic
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_ENV_VAR = "ANTHROPIC_API_KEY"
_DEFAULT_MODEL = "claude-sonnet-4-5"
_MAX_TOKENS = 1024


class AnthropicClient:
    """Cliente concreto para a API Anthropic (Claude).

    Carrega a chave de API exclusivamente via variável de ambiente
    ``ANTHROPIC_API_KEY``, utilizando ``python-dotenv`` para leitura do
    arquivo ``.env``. Nunca registra o valor da chave em logs.

    Args:
        model: Identificador do modelo Anthropic a ser utilizado.
            Padrão: ``"claude-sonnet-4-5"``.
        max_tokens: Número máximo de tokens na resposta. Padrão: ``1024``.

    Raises:
        EnvironmentError: Se a variável de ambiente ``ANTHROPIC_API_KEY``
            não estiver definida.

    Example:
        >>> client = AnthropicClient()
        >>> summary = client.complete("Resuma este arquivo...")
    """

    def __init__(
        self,
        model: str = _DEFAULT_MODEL,
        max_tokens: int = _MAX_TOKENS,
    ) -> None:
        """Inicializa o cliente Anthropic carregando a API key do ambiente.

        Args:
            model: Identificador do modelo Anthropic a ser utilizado.
            max_tokens: Número máximo de tokens na resposta.

        Raises:
            EnvironmentError: Se ``ANTHROPIC_API_KEY`` não estiver definida
                no ambiente ou no arquivo ``.env``.
        """
        load_dotenv()
        api_key = os.getenv(_ENV_VAR)
        if not api_key:
            raise EnvironmentError(
                f"Variável de ambiente '{_ENV_VAR}' não está definida. "
                "Defina-a no arquivo .env ou no ambiente do sistema."
            )
        self._model = model
        self._max_tokens = max_tokens
        self._client = anthropic.Anthropic(api_key=api_key)
        logger.debug("AnthropicClient inicializado com modelo '%s'", model)

    def complete(self, prompt: str) -> str:
        """Envia um prompt ao modelo Anthropic e retorna a resposta.

        Args:
            prompt: Texto do prompt a ser enviado ao modelo.

        Returns:
            Resposta gerada pelo modelo como string.

        Raises:
            anthropic.APIError: Em caso de falha na comunicação com a API.
        """
        logger.debug("Enviando prompt ao Anthropic (modelo=%s)", self._model)
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        result: str = message.content[0].text if message.content else ""
        logger.debug("Resposta recebida do Anthropic (%d chars)", len(result))
        return result
