"""Stub funcional da etapa de seleção de arquivos relevantes.

Este módulo implementa a função `select_relevant`, responsável por
selecionar e ranquear os arquivos mais relevantes para a tarefa informada
com base em similaridade semântica.
"""

from __future__ import annotations

from tokemize.models import EmbeddingsOutput, SelectedFile, SelectionOutput

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

    # Garante ordenação decrescente por relevance_score.
    selected.sort(key=lambda f: f.relevance_score, reverse=True)

    return SelectionOutput(
        task=task,
        selected_files=selected,
        total_candidates=total_candidates,
    )
