"""Cliente concreto para o provedor de LLM Groq.

Implementa ``LLMClientProtocol`` via duck typing, carregando credenciais
exclusivamente via variável de ambiente e propagando exceções do SDK sem
capturá-las.
"""

import logging
import os

from dotenv import load_dotenv

import groq

logger = logging.getLogger(__name__)

DEFAULT_MODEL: str = "llama3-8b-8192"
ENV_API_KEY: str = "GROQ_API_KEY"
ENV_MODEL: str = "GROQ_MODEL"


class GroqClient:
    """Cliente concreto para o provedor Groq, compatível com LLMClientProtocol.

    Carrega a ``GROQ_API_KEY`` via ``python-dotenv`` e valida na construção
    (fail-fast). O modelo é resolvido com precedência: parâmetro do construtor
    → variável de ambiente ``GROQ_MODEL`` → ``DEFAULT_MODEL``.

    O ``GroqClient`` não herda explicitamente de ``LLMClientProtocol``; a
    compatibilidade é garantida por duck typing (``typing.Protocol``).

    Args:
        model: Identificador do modelo Groq. Se omitido, usa ``GROQ_MODEL``
            do ambiente ou o padrão ``"llama3-8b-8192"``.

    Raises:
        EnvironmentError: Se ``GROQ_API_KEY`` não estiver definida ou estiver
            vazia.
        ValueError: Se o ``model`` fornecido for uma string vazia.

    Example:
        >>> import os
        >>> os.environ["GROQ_API_KEY"] = "minha-chave"
        >>> client = GroqClient()
        >>> # client.complete("Resuma este texto...")
    """

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()

        # Validação antecipada: string vazia é inválida
        if model is not None and not model:
            raise ValueError(
                "O parâmetro 'model' não pode ser uma string vazia. "
                f"Use None para o padrão ('{DEFAULT_MODEL}') ou forneça um model_id válido."
            )

        # Resolução do model com precedência de três camadas:
        # 1. parâmetro do construtor → 2. GROQ_MODEL env → 3. DEFAULT_MODEL
        if model is not None:
            self._model: str = model
        else:
            env_model = os.getenv(ENV_MODEL)
            self._model = env_model if env_model else DEFAULT_MODEL

        api_key = os.getenv(ENV_API_KEY)
        if not api_key:
            raise EnvironmentError(
                f"Variável de ambiente '{ENV_API_KEY}' não definida ou vazia. "
                "Defina-a no arquivo .env ou no ambiente do sistema."
            )

        self._client: groq.Groq = groq.Groq(api_key=api_key)

    def complete(self, prompt: str) -> str:
        """Envia um prompt ao modelo Groq e retorna a completion como str.

        Args:
            prompt: Texto de entrada para o modelo.

        Returns:
            Texto da completion retornado pelo modelo, ou string vazia se a
            API retornar uma completion nula.

        Raises:
            groq.AuthenticationError: Se a API key for inválida ou expirada.
            groq.APIConnectionError: Se houver falha de rede ou timeout.
            groq.RateLimitError: Se o rate limit da API for excedido.
            groq.APIStatusError: Para outros erros HTTP da API Groq.
        """
        logger.debug("Iniciando chamada complete()")
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.choices[0].message.content or ""
            logger.debug("Chamada complete() concluída com sucesso")
            return text
        except Exception as exc:
            logger.error("Falha em complete(): %s", type(exc).__name__)
            raise
