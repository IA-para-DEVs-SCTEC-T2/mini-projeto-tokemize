"""Modelo de dados para o resultado da análise de um arquivo de código-fonte."""

from __future__ import annotations

from dataclasses import dataclass, field

from tokemize.models.artifact import Artifact


@dataclass
class FileAnalysis:
    """Resultado da análise de um arquivo de código-fonte.

    Representa a saída do Repository_Analyzer para um único arquivo,
    contendo os artefatos sintáticos extraídos pelo Tree-sitter e os
    metadados do arquivo.

    Attributes:
        relative_path: Caminho relativo à raiz do repositório.
        language: Linguagem detectada (ex: ``"python"``, ``"unknown"``).
        artifacts: Lista de artefatos extraídos pelo Tree-sitter (funções,
            classes, métodos e imports). Vazia se a linguagem não for
            suportada.
        line_count: Número de linhas do arquivo.
        size_bytes: Tamanho do arquivo em bytes.
    """

    relative_path: str
    language: str
    artifacts: list[Artifact] = field(default_factory=list)
    line_count: int = 0
    size_bytes: int = 0
