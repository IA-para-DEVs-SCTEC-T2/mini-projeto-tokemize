"""Seleção de artefatos relevantes do pipeline Tokemize."""

from __future__ import annotations

from tokemize.core.selector.intelligent_selector import (
    select_relevant_artifacts as select_intelligent_artifacts,
)
from tokemize.models.artifact import Artifact
from tokemize.models.file_analysis import FileAnalysis


def select_relevant_artifacts(
    file_analyses: list[FileAnalysis],
    task_description: str,
) -> list[Artifact]:
    """Seleciona os artefatos relevantes a partir das análises de arquivo.

    Normaliza os artefatos cujo ``file_path`` esteja vazio e delega a
    seleção por relevância ao seletor inteligente.

    Args:
        file_analyses: Lista de FileAnalysis retornadas pelo Repository_Analyzer.
        task_description: Descrição da tarefa técnica a ser realizada.

    Returns:
        Lista de Artifact filtrados por relevância para a tarefa.
    """
    for fa in file_analyses:
        for artifact in fa.artifacts:
            # Garante que file_path está preenchido
            if not artifact.file_path:
                artifact.file_path = fa.relative_path

    return select_intelligent_artifacts(file_analyses, task_description)
