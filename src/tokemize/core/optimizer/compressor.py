"""Compressão de contexto do pipeline Tokemize (stub)."""

from __future__ import annotations

from tokemize.models import CompressedContext, SelectedContext


def compress_context(artifacts: list) -> CompressedContext:
    """Comprime e resume os artefatos selecionados.

    Args:
        artifacts: Lista de artefatos selecionados pelo Artifact_Selector.

    Returns:
        CompressedContext com conteúdo vazio e zero tokens (stub).
    """
    return CompressedContext(
        task_description="",
        compressed_content="",
        token_count=0,
    )


def compress_context_from_selected(context: SelectedContext) -> CompressedContext:
    """Comprime e resume o contexto selecionado (compatibilidade legada).

    Args:
        context: Contexto selecionado pelo Intelligent_Selector.

    Returns:
        CompressedContext com conteúdo vazio e zero tokens (stub).
    """
    return CompressedContext(
        task_description=context.task_description,
        compressed_content="",
        token_count=0,
    )
