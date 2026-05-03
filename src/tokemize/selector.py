"""Seletor de contexto para o pipeline Tokemize.

Expõe duas interfaces:
- ``select_relevant(embeddings_output, task)`` — função de pipeline que
  retorna ``SelectionOutput`` (compatível com o orquestrador e test_stubs.py)
- ``ContextSelector`` — classe avançada com suporte a FAISS e embeddings
"""

from __future__ import annotations

import logging

from tokemize.models import EmbeddingsOutput, SelectedFile, SelectionOutput

logger = logging.getLogger(__name__)

# Score de relevância fictício atribuído a todos os arquivos pelo stub.
_STUB_RELEVANCE_SCORE: float = 0.8


def select_relevant(
    embeddings_output: EmbeddingsOutput,
    task: str,
) -> SelectionOutput:
    """Seleciona os arquivos mais relevantes para a tarefa informada.

    Args:
        embeddings_output: Resultado da etapa de embeddings contendo os
            arquivos com seus vetores de representação.
        task: Descrição textual da tarefa técnica fornecida pelo usuário.

    Returns:
        SelectionOutput com os arquivos selecionados ordenados por
        ``relevance_score`` decrescente e ``task`` preservada no output.
        Se ``embeddings_output.embedded_files`` estiver vazio, retorna
        ``SelectionOutput(task=task, selected_files=[], total_candidates=0)``.

    Example:
        >>> from tokemize.models import EmbeddingsOutput
        >>> output = select_relevant(EmbeddingsOutput(), task="refactor auth")
        >>> output.task
        'refactor auth'
    """
    total_candidates = len(embeddings_output.embedded_files)

    if not embeddings_output.embedded_files:
        return SelectionOutput(
            task=task,
            selected_files=[],
            total_candidates=0,
        )

    selected: list[SelectedFile] = []
    for embedded in embeddings_output.embedded_files:
        selected.append(
            SelectedFile(
                path=embedded.path,
                language=embedded.language,
                content=embedded.content,
                relevance_score=_STUB_RELEVANCE_SCORE,
            )
        )

    selected.sort(key=lambda f: f.relevance_score, reverse=True)

    return SelectionOutput(
        task=task,
        selected_files=selected,
        total_candidates=total_candidates,
    )


class ContextSelector:
    """Seleciona e ranqueia arquivos relevantes respeitando o budget de tokens.

    Implementação avançada com suporte a FAISS e embeddings semânticos.

    Args:
        indexer: Instância do indexador FAISS.
        embeddings_client: Cliente de embeddings para gerar vetores.
        relevance_threshold: Score mínimo de relevância (padrão: 0.75).
        top_k: Número máximo de candidatos a recuperar do índice (padrão: 20).
    """

    def __init__(
        self,
        indexer: object,
        embeddings_client: object,
        relevance_threshold: float = 0.75,
        top_k: int = 20,
    ) -> None:
        if not 0.0 <= relevance_threshold <= 1.0:
            raise ValueError(
                f"relevance_threshold deve estar em [0.0, 1.0], recebido {relevance_threshold}"
            )
        self.indexer = indexer
        self.embeddings_client = embeddings_client
        self.relevance_threshold = relevance_threshold
        self.top_k = top_k
        logger.debug(
            "ContextSelector inicializado: threshold=%s, top_k=%s",
            relevance_threshold,
            top_k,
        )

    def select(self, request: str, token_budget: int) -> dict:
        """Seleciona os arquivos mais relevantes dentro do budget de tokens.

        Args:
            request: Descrição da tarefa / query do usuário.
            token_budget: Número máximo de tokens permitidos no contexto.

        Returns:
            Dicionário com ``files_complete``, ``files_summary``,
            ``files_ignored``, ``total_tokens`` e ``formatted_text``.
        """
        logger.info("Iniciando seleção de contexto: budget=%d tokens", token_budget)

        query_vector = self.embeddings_client.embed_text(request)
        candidates = self.indexer.search(query_vector, top_k=self.top_k)

        filtered = [
            (item, score)
            for item, score in candidates
            if score >= self.relevance_threshold
        ]

        if not filtered:
            logger.warning(
                "Nenhum arquivo acima do limiar de relevância %s",
                self.relevance_threshold,
            )
            return {
                "files_complete": [],
                "files_summary": [],
                "files_ignored": [item for item, _ in candidates],
                "total_tokens": 0,
                "formatted_text": "",
            }

        ranked = self._rank_items(filtered)
        selected, ignored = self._accumulate_within_budget(ranked, token_budget)
        total_tokens = sum(item.get("token_count", 0) for item in selected)
        formatted_text = self._format_context(selected)

        logger.info(
            "Seleção concluída: %d arquivos, %d tokens",
            len(selected),
            total_tokens,
        )
        return {
            "files_complete": selected,
            "files_summary": [],
            "files_ignored": ignored,
            "total_tokens": total_tokens,
            "formatted_text": formatted_text,
        }

    def _rank_items(self, candidates: list) -> list:
        return sorted(candidates, key=lambda x: (-x[1], x[0].get("token_count", 0)))

    def _accumulate_within_budget(
        self, ranked_items: list, token_budget: int
    ) -> tuple[list, list]:
        selected, ignored = [], []
        accumulated = 0
        for item, score in ranked_items:
            tokens = item.get("token_count", 0)
            if accumulated + tokens <= token_budget:
                selected.append(item)
                accumulated += tokens
            else:
                ignored.append(item)
        return selected, ignored

    def _format_context(self, items: list) -> str:
        if not items:
            return ""
        parts = []
        for item in items:
            name = item.get("name", "unknown")
            language = item.get("language", "text")
            content = item.get("content", "")
            parts.append(f"### [{language}] — {name}\n```{language}\n{content}\n```")
        return "\n\n".join(parts)
