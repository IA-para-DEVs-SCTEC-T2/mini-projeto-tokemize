"""Seleção de artefatos relevantes do pipeline Tokemize."""

from __future__ import annotations

from tokemize.models.artifact import Artifact
from tokemize.models.file_analysis import FileAnalysis


def select_relevant_artifacts(
    file_analyses: list[FileAnalysis],
    task_description: str,
) -> list[Artifact]:
    """Seleciona os artefatos relevantes a partir das análises de arquivo.

    Extrai todos os artefatos de todos os arquivos analisados. Artefatos
    cujo ``file_path`` esteja vazio recebem o ``relative_path`` do
    ``FileAnalysis`` correspondente.

    Args:
        file_analyses: Lista de FileAnalysis retornadas pelo Repository_Analyzer.
        task_description: Descrição da tarefa técnica a ser realizada.

    Returns:
        Lista plana de Artifact extraídos de todos os arquivos analisados.
    """
    artifacts: list[Artifact] = []
    for fa in file_analyses:
        for artifact in fa.artifacts:
            # Garante que file_path está preenchido
            if not artifact.file_path:
                artifact.file_path = fa.relative_path
            artifacts.append(artifact)
    return artifacts
