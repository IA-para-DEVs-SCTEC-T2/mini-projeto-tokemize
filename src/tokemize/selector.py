"""Seletor de contexto para o pipeline Tokemize."""

from __future__ import annotations

import logging

from tokemize.models import AnalysisOutput, SelectedFile, SelectionOutput

logger = logging.getLogger(__name__)

# Score de relevância atribuído a todos os arquivos pelo stub.
_STUB_RELEVANCE_SCORE: float = 0.8


def select_relevant(
    analysis_output: AnalysisOutput,
    task: str,
) -> SelectionOutput:
    """Seleciona os arquivos mais relevantes para a tarefa informada.

    Args:
        analysis_output: Resultado da etapa de análise contendo os arquivos
            enriquecidos com metadados estruturais.
        task: Descrição textual da tarefa técnica fornecida pelo usuário.

    Returns:
        SelectionOutput com os arquivos selecionados ordenados por
        ``relevance_score`` decrescente e ``task`` preservada no output.
        Se ``analysis_output.analyzed_files`` estiver vazio, retorna
        ``SelectionOutput(task=task, selected_files=[], total_candidates=0)``.

    Example:
        >>> from tokemize.models import AnalysisOutput
        >>> output = select_relevant(AnalysisOutput(), task="refactor auth")
        >>> output.task
        'refactor auth'
    """
    total_candidates = len(analysis_output.analyzed_files)

    if not analysis_output.analyzed_files:
        return SelectionOutput(
            task=task,
            selected_files=[],
            total_candidates=0,
        )

    selected: list[SelectedFile] = []
    for analyzed in analysis_output.analyzed_files:
        selected.append(
            SelectedFile(
                path=analyzed.path,
                language=analyzed.language,
                content=analyzed.content,
                relevance_score=_STUB_RELEVANCE_SCORE,
            )
        )

    selected.sort(key=lambda f: f.relevance_score, reverse=True)

    return SelectionOutput(
        task=task,
        selected_files=selected,
        total_candidates=total_candidates,
    )
