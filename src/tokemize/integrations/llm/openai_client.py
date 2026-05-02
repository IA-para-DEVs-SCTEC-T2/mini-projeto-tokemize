"""Cliente de LLM para a API OpenAI."""

import logging
import os

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)

_ENV_VAR = "OPENAI_API_KEY"
_DEFAULT_MODEL = "gpt-4o"


class OpenAIClient:
    """Cliente concreto para a API OpenAI (GPT-4o).

    Carrega a chave de API exclusivamente via variável de ambiente
    ``OPENAI_API_KEY``, utilizando ``python-dotenv`` para leitura do
    arquivo ``.env``. Nunca registra o valor da chave em logs.

    Args:
        model: Identificador do modelo OpenAI a ser utilizado.
            Padrão: ``"gpt-4o"``.

    Raises:
        EnvironmentError: Se a variável de ambiente ``OPENAI_API_KEY``
            não estiver definida.

    Example:
        >>> client = OpenAIClient()
        >>> summary = client.complete("Resuma este arquivo...")
    """

    def __init__(self, model: str = _DEFAULT_MODEL) -> None:
        """Inicializa o cliente OpenAI carregando a API key do ambiente.

        Args:
            model: Identificador do modelo OpenAI a ser utilizado.

        Raises:
            EnvironmentError: Se ``OPENAI_API_KEY`` não estiver definida
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
        self._client = OpenAI(api_key=api_key)
        logger.debug("OpenAIClient inicializado com modelo '%s'", model)

    def complete(self, prompt: str) -> str:
        """Envia um prompt ao modelo OpenAI e retorna a resposta.

        Args:
            prompt: Texto do prompt a ser enviado ao modelo.

        Returns:
            Resposta gerada pelo modelo como string.

        Raises:
            openai.OpenAIError: Em caso de falha na comunicação com a API.
        """
        logger.debug("Enviando prompt ao OpenAI (modelo=%s)", self._model)
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
        )
        result: str = response.choices[0].message.content or ""
        logger.debug("Resposta recebida do OpenAI (%d chars)", len(result))
        return result
