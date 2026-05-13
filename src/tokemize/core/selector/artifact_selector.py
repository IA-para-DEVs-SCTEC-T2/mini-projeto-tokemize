"""Seleção de artefatos relevantes do pipeline Tokemize (stub)."""

from __future__ import annotations


def select_relevant_artifacts(
    file_analyses: list,
    task_description: str,
) -> list:
    """Seleciona os artefatos relevantes a partir das análises de arquivo.

    Args:
        file_analyses: Lista de análises de arquivo retornadas pelo
            Repository_Analyzer.
        task_description: Descrição da tarefa técnica a ser realizada.

    Returns:
        Lista de artefatos selecionados como relevantes para a tarefa
        (stub — retorna a lista de entrada sem filtragem).
    """
    return list(file_analyses)
