"""Módulo de seleção inteligente de arquivos do pipeline Tokemize.

Este módulo expõe a função `select_relevant_files`, responsável por selecionar
os arquivos mais relevantes de um repositório para uma determinada tarefa.
A implementação atual é um stub — a lógica real será adicionada em outro spec.
"""

from tokemize.models import RepositoryStructure, SelectedContext


def select_relevant_files(
    structure: RepositoryStructure,
    task_description: str,
) -> SelectedContext:
    """Seleciona os arquivos relevantes do repositório para a tarefa fornecida.

    Args:
        structure: Estrutura mapeada do repositório pelo Repository_Analyzer.
        task_description: Descrição da tarefa técnica a ser realizada.

    Returns:
        SelectedContext contendo a descrição da tarefa e, futuramente, os
        arquivos selecionados com suas pontuações de relevância.
    """
    return SelectedContext(task_description=task_description)
