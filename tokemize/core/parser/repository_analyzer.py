"""Módulo de análise de repositório do pipeline Tokemize.

Este módulo expõe a função `analyze_repository`, responsável por mapear
a estrutura de um repositório local e retornar um objeto `RepositoryStructure`.
A implementação atual é um stub — a lógica real será adicionada em outro spec.
"""

from tokemize.models import RepositoryStructure


def analyze_repository(repo_path: str) -> RepositoryStructure:
    """Analisa a estrutura de um repositório local.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório.

    Returns:
        RepositoryStructure contendo o caminho raiz e, futuramente, a lista
        de arquivos e metadados do repositório.
    """
    return RepositoryStructure(root_path=repo_path)
