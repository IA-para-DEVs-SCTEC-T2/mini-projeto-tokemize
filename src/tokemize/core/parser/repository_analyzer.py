"""Análise de repositório do pipeline Tokemize (stub)."""

from tokemize.models import RepositoryStructure


def analyze_repository(repo_path: str) -> RepositoryStructure:
    """Analisa a estrutura de um repositório local.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório.

    Returns:
        RepositoryStructure contendo o caminho raiz e a lista de arquivos.
    """
    return RepositoryStructure(root_path=repo_path)
