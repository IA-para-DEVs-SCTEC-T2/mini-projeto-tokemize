"""Despacho para LLM do pipeline Tokemize (stub)."""

from tokemize.models import CachedContext


def dispatch(cached_context: CachedContext) -> str:
    """Envia o contexto otimizado ao LLM e retorna a resposta.

    Args:
        cached_context: Contexto verificado/atualizado pelo Context_Cache.

    Returns:
        Conteúdo do contexto em cache (stub).
    """
    return cached_context.content
