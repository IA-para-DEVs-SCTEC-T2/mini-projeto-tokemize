"""Cache de contexto do pipeline Tokemize (stub)."""

from tokemize.models import CachedContext, SavedContext


def get_or_update_cache(
    saved: SavedContext,
    task_description: str,
) -> CachedContext:
    """Verifica ou atualiza o cache de contexto para a tarefa fornecida.

    Args:
        saved: Contexto salvo em disco gerado pelo Context_Saver.
        task_description: Descrição da tarefa técnica a ser realizada.

    Returns:
        CachedContext com cache_hit=False e context_file_path propagado (stub).
    """
    return CachedContext(
        task_description=task_description,
        content=saved.compressed_content,
        cache_hit=False,
        token_count=saved.token_count,
        context_file_path=saved.context_file_path,
    )
