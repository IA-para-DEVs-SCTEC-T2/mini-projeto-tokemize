"""Cache de contexto do pipeline Tokemize (stub)."""

from tokemize.models import CachedContext, CompressedContext


def get_or_update_cache(
    compressed: CompressedContext,
    task_description: str,
) -> CachedContext:
    """Verifica ou atualiza o cache de contexto para a tarefa fornecida.

    Args:
        compressed: Contexto comprimido gerado pelo Compressor.
        task_description: Descrição da tarefa técnica a ser realizada.

    Returns:
        CachedContext com cache_hit=False (stub).
    """
    return CachedContext(
        task_description=task_description,
        content=compressed.compressed_content,
        cache_hit=False,
        token_count=compressed.token_count,
    )
