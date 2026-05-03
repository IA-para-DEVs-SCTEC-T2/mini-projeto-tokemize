"""Seleção inteligente de arquivos do pipeline Tokemize (stub)."""

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
        SelectedContext contendo a descrição da tarefa.
    """
    return SelectedContext(task_description=task_description)
