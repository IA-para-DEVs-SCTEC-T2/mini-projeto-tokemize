"""Módulo de despacho para LLM do pipeline Tokemize.

Este módulo expõe a função `dispatch`, responsável por enviar o contexto
otimizado ao LLM e retornar a resposta gerada. A implementação atual é um
stub — a lógica real será adicionada em outro spec.
"""

from tokemize.models import CachedContext


def dispatch(cached_context: CachedContext) -> str:
    """Envia o contexto otimizado ao LLM e retorna a resposta.

    Args:
        cached_context: Contexto verificado/atualizado pelo Context_Cache,
            pronto para ser enviado ao LLM.

    Returns:
        String contendo a resposta gerada pelo LLM. O stub retorna
        diretamente o conteúdo do contexto em cache.
    """
    return cached_context.content
