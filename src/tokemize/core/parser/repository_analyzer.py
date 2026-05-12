"""Análise de repositório do pipeline Tokemize (stub)."""

from __future__ import annotations

from tokemize.models import RepositoryStructure


def analyze_repository(repo_path: str) -> list:
    """Analisa a estrutura de um repositório local.

    Percorre o repositório e retorna uma lista de análises de arquivo
    com metadados e artefatos extraídos.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório.

    Returns:
        Lista de análises de arquivo (stub — retorna lista vazia).
    """
    return []


def analyze_repository_structure(repo_path: str) -> RepositoryStructure:
    """Retorna a estrutura mapeada do repositório (compatibilidade legada).

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório.

    Returns:
        RepositoryStructure contendo o caminho raiz e a lista de arquivos.
    """
    return RepositoryStructure(root_path=repo_path)
