"""Análise de repositório do pipeline Tokemize.

<<<<<<< HEAD
Orquestra o RepositoryScanner e o TreeSitterAnalyzer para varrer um
repositório local e extrair artefatos sintáticos de cada arquivo de
código-fonte suportado.
"""

from pathlib import Path

from tokemize.core.parser.scanner import DEFAULT_IGNORE_DIRS, RepositoryScanner
from tokemize.core.parser.tree_sitter_analyzer import (
    TreeSitterAnalyzer,
    UnsupportedLanguageError,
)
from tokemize.models import FileInfo, RepositoryStructure
from tokemize.models.artifact import Artifact
from tokemize.models.file_analysis import FileAnalysis


def analyze_repository(repo_path: str) -> RepositoryStructure:
    """Analisa a estrutura de um repositório local e extrai artefatos sintáticos.

    Varre recursivamente o diretório ``repo_path`` usando o
    RepositoryScanner, ignorando diretórios como ``.git``, ``node_modules``,
    ``__pycache__``, ``.venv`` e ``dist``. Para cada arquivo encontrado,
    tenta extrair artefatos (funções, classes, métodos e imports) via
    TreeSitterAnalyzer.

    Arquivos com linguagem não suportada pelo Tree-sitter recebem
    ``language="unknown"`` e ``artifacts=[]`` — nenhuma exceção é propagada
    para arquivos individuais.
=======
from __future__ import annotations

from tokemize.models import RepositoryStructure


def analyze_repository(repo_path: str) -> list:
    """Analisa a estrutura de um repositório local.
>>>>>>> 135f5f4 (feat(task005): teste task005)

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
        repo_path: Caminho absoluto ou relativo para a raiz do repositório
            a ser analisado.

    Returns:
        RepositoryStructure com a lista de arquivos encontrados e metadados.

    Example:
        >>> structure = analyze_repository(".")
        >>> for f in structure.files:
        ...     print(f.path, f.language)
    """
    scanner = RepositoryScanner(ignore_dirs=set(DEFAULT_IGNORE_DIRS))
    analyzer = TreeSitterAnalyzer()

    scan_result = scanner.scan(Path(repo_path))

    files: list[FileInfo] = []
    file_analyses: list[FileAnalysis] = []

    for file_meta in scan_result.files:
        try:
            artifacts: list[Artifact] = analyzer.analyze(file_meta.path)
            language: str = file_meta.language
        except UnsupportedLanguageError:
            artifacts = []
            language = "unknown"

        file_analyses.append(
            FileAnalysis(
                relative_path=str(file_meta.relative_path),
                language=language,
                artifacts=artifacts,
                line_count=file_meta.line_count,
                size_bytes=file_meta.size_bytes,
            )
        )

        files.append(
            FileInfo(
                path=str(file_meta.relative_path),
                language=language,
                size_bytes=file_meta.size_bytes,
            )
        )

    return RepositoryStructure(
        root_path=repo_path,
        files=files,
        metadata={"file_analyses": file_analyses},
    )
