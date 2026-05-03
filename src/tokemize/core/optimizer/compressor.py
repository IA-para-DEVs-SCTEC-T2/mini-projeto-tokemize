"""Compressão de contexto do pipeline Tokemize (stub)."""

from tokemize.models import CompressedContext, SelectedContext


def compress_context(context: SelectedContext) -> CompressedContext:
    """Comprime e resume o contexto selecionado.

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
