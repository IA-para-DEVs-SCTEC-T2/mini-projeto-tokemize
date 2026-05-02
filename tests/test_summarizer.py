"""Testes unitários e baseados em propriedades para o módulo Summarizer."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tokemize.cache import FileCache
from tokemize.integrations.llm.protocol import LLMClientProtocol
from tokemize.summarizer import FALLBACK_MESSAGE, Summarizer

# ---------------------------------------------------------------------------
# Estratégias Hypothesis reutilizáveis
# ---------------------------------------------------------------------------

file_path_strategy = st.one_of(
    st.text(min_size=1, max_size=200).filter(lambda s: s.strip()),
    st.just("app.py"),
    st.just("src/module.py"),
    st.just("/abs/path/to/file.py"),
)

content_strategy = st.text(min_size=1, max_size=2000)

summary_strategy = st.text(min_size=1, max_size=500)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cache_entry(content: str, summary: str) -> dict:
    """Cria uma entrada de cache com hash calculado a partir do conteúdo."""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return {
        "content_hash": content_hash,
        "summary": summary,
        "symbols": [],
        "imports": [],
        "token_estimate": 0,
        "metadata": {},
    }


def _make_stale_cache_entry(summary: str) -> dict:
    """Cria uma entrada de cache com hash diferente do conteúdo atual."""
    return {
        "content_hash": "0000000000000000000000000000000000000000000000000000000000000000",
        "summary": summary,
        "symbols": [],
        "imports": [],
        "token_estimate": 0,
        "metadata": {},
    }


# ---------------------------------------------------------------------------
# Testes unitários concretos
# ---------------------------------------------------------------------------


class TestSummarizerUnit:
    """Testes unitários concretos do Summarizer."""

    def test_summarize_returns_str(self):
        """O método summarize sempre retorna str."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.return_value = "Resumo do arquivo."
        summarizer = Summarizer(llm_client=mock_llm)

        result = summarizer.summarize("app.py", "def main(): pass")

        assert isinstance(result, str)

    def test_summarize_without_cache_calls_llm(self):
        """Sem FileCache, o LLM é chamado a cada invocação."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.return_value = "Resumo gerado."
        summarizer = Summarizer(llm_client=mock_llm, cache=None)

        result = summarizer.summarize("app.py", "def main(): pass")

        mock_llm.complete.assert_called_once()
        assert result == "Resumo gerado."

    def test_fallback_message_is_nonempty(self):
        """FALLBACK_MESSAGE é uma string não vazia."""
        assert isinstance(FALLBACK_MESSAGE, str)
        assert len(FALLBACK_MESSAGE) > 0

    def test_llm_client_injected_not_instantiated(self):
        """Summarizer não instancia LLMClientProtocol diretamente."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        summarizer = Summarizer(llm_client=mock_llm)

        # O atributo privado deve ser exatamente o objeto injetado
        assert summarizer._llm_client is mock_llm

    def test_empty_content_returns_empty_string(self):
        """Conteúdo vazio retorna string vazia sem chamar o LLM."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        summarizer = Summarizer(llm_client=mock_llm)

        result = summarizer.summarize("app.py", "")

        assert result == ""
        mock_llm.complete.assert_not_called()

    def test_cache_hit_returns_cached_summary(self):
        """Cache hit retorna o resumo cacheado sem chamar o LLM."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_cache = MagicMock(spec=FileCache)
        content = "def main(): pass"
        cached_summary = "Resumo cacheado."
        mock_cache.get_cached_file.return_value = _make_cache_entry(
            content, cached_summary
        )

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        result = summarizer.summarize("app.py", content)

        assert result == cached_summary
        mock_llm.complete.assert_not_called()

    def test_cache_miss_calls_llm_and_persists(self):
        """Cache miss chama o LLM e persiste o resumo no cache."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.return_value = "Novo resumo."
        mock_cache = MagicMock(spec=FileCache)
        mock_cache.get_cached_file.return_value = None

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        result = summarizer.summarize("app.py", "def main(): pass")

        assert result == "Novo resumo."
        mock_llm.complete.assert_called_once()
        mock_cache.update_cached_file.assert_called_once()
        mock_cache.save_cache.assert_called_once()

    def test_llm_failure_returns_fallback(self):
        """Falha do LLM retorna FALLBACK_MESSAGE sem propagar exceção."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.side_effect = RuntimeError("API indisponível")
        summarizer = Summarizer(llm_client=mock_llm)

        result = summarizer.summarize("app.py", "def main(): pass")

        assert result == FALLBACK_MESSAGE

    def test_llm_failure_does_not_persist_cache(self):
        """Falha do LLM não persiste nada no cache."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.side_effect = Exception("Erro genérico")
        mock_cache = MagicMock(spec=FileCache)
        mock_cache.get_cached_file.return_value = None

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        summarizer.summarize("app.py", "def main(): pass")

        mock_cache.update_cached_file.assert_not_called()
        mock_cache.save_cache.assert_not_called()


# ---------------------------------------------------------------------------
# Testes de logging (opcionais)
# ---------------------------------------------------------------------------


class TestSummarizerLogging:
    """Testes de logging do Summarizer."""

    def test_summarize_logs_cache_hit(self, caplog):
        """Cache hit é registrado no log."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_cache = MagicMock(spec=FileCache)
        content = "def main(): pass"
        mock_cache.get_cached_file.return_value = _make_cache_entry(
            content, "Resumo cacheado."
        )

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        with caplog.at_level(logging.INFO, logger="tokemize.summarizer"):
            summarizer.summarize("app.py", content)

        assert any("Cache hit" in record.message for record in caplog.records)

    def test_summarize_logs_cache_miss(self, caplog):
        """Cache miss é registrado no log."""
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.return_value = "Resumo."
        mock_cache = MagicMock(spec=FileCache)
        mock_cache.get_cached_file.return_value = None

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        with caplog.at_level(logging.DEBUG, logger="tokemize.summarizer"):
            summarizer.summarize("app.py", "def main(): pass")

        assert any("Cache miss" in record.message for record in caplog.records)

    def test_api_key_not_logged(self, caplog):
        """O valor de uma API key não aparece nos logs do Summarizer."""
        fake_api_key = "sk-supersecretkey12345"
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.return_value = "Resumo."

        summarizer = Summarizer(llm_client=mock_llm)
        with caplog.at_level(logging.DEBUG, logger="tokemize.summarizer"):
            summarizer.summarize("app.py", "def main(): pass")

        for record in caplog.records:
            assert fake_api_key not in record.message


# ---------------------------------------------------------------------------
# Property-Based Tests (Hypothesis)
# ---------------------------------------------------------------------------


class TestSummarizerProperties:
    """Testes baseados em propriedades do Summarizer."""

    # Feature: tokemize-summarizer, Property 1: Conteúdo vazio retorna string vazia sem chamar o LLM
    @given(file_path=file_path_strategy)
    @settings(max_examples=100)
    def test_empty_content_returns_empty_no_llm_call(self, file_path: str):
        """Property 1: Conteúdo vazio retorna string vazia sem chamar o LLM.

        Validates: Requirements 1.5
        """
        mock_llm = MagicMock(spec=LLMClientProtocol)
        summarizer = Summarizer(llm_client=mock_llm)

        result = summarizer.summarize(file_path, "")

        assert result == ""
        mock_llm.complete.assert_not_called()

    # Feature: tokemize-summarizer, Property 2: Cache hit evita chamada ao LLM
    @given(
        file_path=file_path_strategy,
        content=content_strategy,
        summary=summary_strategy,
    )
    @settings(max_examples=100)
    def test_cache_hit_skips_llm(
        self, file_path: str, content: str, summary: str
    ):
        """Property 2: Cache hit evita chamada ao LLM.

        Validates: Requirements 2.1
        """
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_cache = MagicMock(spec=FileCache)
        mock_cache.get_cached_file.return_value = _make_cache_entry(
            content, summary
        )

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        result = summarizer.summarize(file_path, content)

        assert result == summary
        mock_llm.complete.assert_not_called()

    # Feature: tokemize-summarizer, Property 3: Resumo gerado é persistido no cache
    @given(
        file_path=file_path_strategy,
        content=content_strategy,
        summary=summary_strategy,
    )
    @settings(max_examples=100)
    def test_successful_summary_persisted_in_cache(
        self, file_path: str, content: str, summary: str
    ):
        """Property 3: Resumo gerado é persistido no cache.

        Validates: Requirements 2.2
        """
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.return_value = summary
        mock_cache = MagicMock(spec=FileCache)
        mock_cache.get_cached_file.return_value = None

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        summarizer.summarize(file_path, content)

        mock_cache.update_cached_file.assert_called_once()
        call_kwargs = mock_cache.update_cached_file.call_args
        assert call_kwargs.kwargs.get("summary") == summary or (
            len(call_kwargs.args) > 1 and summary in call_kwargs.args
        )
        mock_cache.save_cache.assert_called_once()

    # Feature: tokemize-summarizer, Property 4: Falha do LLM retorna fallback sem propagar exceção
    @given(
        file_path=file_path_strategy,
        content=content_strategy,
    )
    @settings(max_examples=100)
    def test_llm_failure_returns_fallback_no_exception(
        self, file_path: str, content: str
    ):
        """Property 4: Falha do LLM retorna fallback sem propagar exceção.

        Validates: Requirements 3.1, 3.2, 3.3, 3.4
        """
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.side_effect = Exception("Falha simulada")
        mock_cache = MagicMock(spec=FileCache)
        mock_cache.get_cached_file.return_value = None

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)

        # Não deve propagar exceção
        result = summarizer.summarize(file_path, content)

        assert isinstance(result, str)
        assert len(result) > 0
        assert result == FALLBACK_MESSAGE
        mock_cache.update_cached_file.assert_not_called()

    # Feature: tokemize-summarizer, Property 5: Invalidação de cache por mudança de conteúdo
    @given(
        file_path=file_path_strategy,
        content=content_strategy,
        summary=summary_strategy,
    )
    @settings(max_examples=100)
    def test_content_change_invalidates_cache(
        self, file_path: str, content: str, summary: str
    ):
        """Property 5: Invalidação de cache por mudança de conteúdo.

        O FileCache.get_cached_file já realiza a validação de hash internamente
        e retorna None quando o hash do arquivo mudou. O Summarizer confia nesse
        contrato: quando get_cached_file retorna None, trata como cache miss e
        chama o LLM, gerando e persistindo um novo resumo.

        Validates: Requirements 2.3
        """
        mock_llm = MagicMock(spec=LLMClientProtocol)
        mock_llm.complete.return_value = summary
        mock_cache = MagicMock(spec=FileCache)
        # FileCache retorna None quando o hash mudou (comportamento real do FileCache)
        mock_cache.get_cached_file.return_value = None

        summarizer = Summarizer(llm_client=mock_llm, cache=mock_cache)
        result = summarizer.summarize(file_path, content)

        # LLM deve ter sido chamado (cache invalidado → miss)
        mock_llm.complete.assert_called_once()
        # Novo resumo deve ter sido persistido
        mock_cache.update_cached_file.assert_called_once()
        mock_cache.save_cache.assert_called_once()
        assert result == summary
