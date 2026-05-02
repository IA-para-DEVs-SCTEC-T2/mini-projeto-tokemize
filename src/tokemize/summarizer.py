"""Módulo responsável por resumir arquivos relevantes usando LLM."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from tokemize.cache import FileCache
from tokemize.integrations.llm.protocol import LLMClientProtocol

logger = logging.getLogger(__name__)

FALLBACK_MESSAGE: str = "[Resumo indisponível: falha ao contatar o serviço de LLM]"

SUMMARY_PROMPT_TEMPLATE: str = """\
Você é um assistente técnico especializado em análise de código-fonte.
Gere um resumo técnico compacto do arquivo abaixo.
O resumo deve cobrir: propósito do arquivo, estruturas principais (classes, funções,
tipos), dependências externas relevantes e padrões de design utilizados.
Seja objetivo e conciso. Não inclua o código-fonte no resumo.

Arquivo: {file_path}

{content}
"""


class Summarizer:
    """Gera e cacheia resumos técnicos de arquivos de código-fonte via LLM.

    Recebe um caminho de arquivo e seu conteúdo, consulta o ``FileCache``
    antes de chamar a API, e retorna sempre uma ``str`` — seja o resumo
    gerado, o resumo cacheado, ou uma mensagem de fallback controlada em
    caso de falha. O pipeline nunca é interrompido por falhas do LLM.

    Args:
        llm_client: Instância de um cliente de LLM compatível com
            ``LLMClientProtocol``. Nunca instanciado internamente.
        cache: Instância de ``FileCache`` para persistência de resumos.
            Se ``None``, opera sem cache (chama o LLM a cada invocação).

    Example:
        >>> from unittest.mock import MagicMock
        >>> mock_llm = MagicMock()
        >>> mock_llm.complete.return_value = "Resumo do arquivo."
        >>> summarizer = Summarizer(llm_client=mock_llm)
        >>> summarizer.summarize("app.py", "def main(): pass")
        'Resumo do arquivo.'
    """

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        cache: FileCache | None = None,
    ) -> None:
        """Inicializa o Summarizer com injeção de dependência.

        Args:
            llm_client: Cliente de LLM compatível com ``LLMClientProtocol``.
            cache: Instância de ``FileCache`` para cache de resumos.
                Opcional; se ``None``, o cache é desabilitado.
        """
        self._llm_client = llm_client
        self._cache = cache
        logger.debug(
            "Summarizer inicializado (cache=%s)",
            "habilitado" if cache is not None else "desabilitado",
        )

    def summarize(self, file_path: str | Path, content: str) -> str:
        """Gera um resumo técnico compacto de um arquivo de código-fonte.

        Consulta o cache antes de chamar o LLM. Em caso de falha da API,
        retorna uma mensagem de fallback controlada sem propagar a exceção.

        Args:
            file_path: Caminho do arquivo a ser resumido (``str`` ou
                ``pathlib.Path``).
            content: Conteúdo textual do arquivo a ser resumido.

        Returns:
            Resumo técnico gerado pelo LLM, resumo cacheado (se válido),
            string vazia (se ``content`` for vazio), ou
            ``FALLBACK_MESSAGE`` em caso de falha da API.
        """
        path_str = str(file_path)
        logger.info("Iniciando sumarização: '%s'", path_str)

        if not content:
            logger.debug("Conteúdo vazio para '%s', retornando string vazia", path_str)
            return ""

        # Verifica cache
        if self._cache is not None:
            cached_entry = self._cache.get_cached_file(file_path)
            if cached_entry is not None:
                cached_summary: str = cached_entry.get("summary", "")
                if cached_summary:
                    logger.info("Cache hit para '%s'", path_str)
                    return cached_summary
            logger.debug("Cache miss para '%s'", path_str)

        # Chama o LLM
        prompt = SUMMARY_PROMPT_TEMPLATE.format(
            file_path=path_str,
            content=content,
        )

        try:
            summary = self._llm_client.complete(prompt)
            logger.info(
                "Resumo gerado para '%s' (%d chars)", path_str, len(summary)
            )
        except Exception as exc:
            logger.error(
                "Falha ao gerar resumo para '%s': %s",
                path_str,
                type(exc).__name__,
            )
            return FALLBACK_MESSAGE

        # Persiste no cache
        if self._cache is not None:
            self._cache.update_cached_file(file_path, summary=summary)
            self._cache.save_cache()
            logger.debug("Resumo persistido no cache para '%s'", path_str)

        return summary

    @staticmethod
    def _hash_content(content: str) -> str:
        """Calcula o hash SHA-256 de um conteúdo textual.

        Args:
            content: Texto cujo hash será calculado.

        Returns:
            Hash SHA-256 em formato hexadecimal.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
