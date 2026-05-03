"""Stub de análise de repositório — compatibilidade com cli.py."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FileInfo:
    """Informações sobre um arquivo do repositório.

    Attributes:
        path: Caminho relativo ao repositório.
        language: Linguagem de programação detectada.
        size_bytes: Tamanho do arquivo em bytes.
    """

    path: str
    language: str
    size_bytes: int


@dataclass
class RepositoryStructure:
    """Estrutura mapeada do repositório.

    Attributes:
        root_path: Caminho absoluto da raiz do repositório.
        files: Lista de arquivos encontrados.
        metadata: Metadados adicionais do repositório.
    """

    root_path: str
    files: list[FileInfo] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def analyze_repository(repo_path: str) -> RepositoryStructure:
    """Analisa a estrutura de um repositório local.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório.

    Returns:
        RepositoryStructure contendo o caminho raiz e a lista de arquivos.
    """
    return RepositoryStructure(root_path=repo_path)
