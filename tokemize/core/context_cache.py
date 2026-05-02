"""Módulo de cache de contexto do pipeline Tokemize.

Este módulo expõe a função `get_or_update_cache`, responsável por verificar
se existe um contexto em cache para a tarefa fornecida e, caso contrário,
armazenar o contexto comprimido para uso futuro. A implementação atual é um
stub — a lógica real será adicionada em outro spec.
"""

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
        CachedContext com o conteúdo final a ser enviado ao LLM. O stub
        sempre retorna `cache_hit=False`, indicando ausência de cache.
    """
    return CachedContext(
        task_description=task_description,
        content=compressed.compressed_content,
        cache_hit=False,
        token_count=compressed.token_count,
    )
