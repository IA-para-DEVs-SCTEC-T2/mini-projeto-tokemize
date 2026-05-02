"""Módulo de compressão de contexto do pipeline Tokemize.

Este módulo expõe a função `compress_context`, responsável por resumir e
comprimir o contexto selecionado para reduzir o número de tokens enviados
ao LLM. A implementação atual é um stub — a lógica real será adicionada
em outro spec.
"""

from tokemize.models import CompressedContext, SelectedContext


def compress_context(context: SelectedContext) -> CompressedContext:
    """Comprime e resume o contexto selecionado.

    Args:
        context: Contexto selecionado pelo Intelligent_Selector, contendo
            os arquivos relevantes e suas pontuações de relevância.

    Returns:
        CompressedContext com o conteúdo comprimido e a estimativa de tokens.
        O stub retorna conteúdo vazio com zero tokens.
    """
    return CompressedContext(
        task_description=context.task_description,
        compressed_content="",
        token_count=0,
    )
