# tokemize.models — Modelos de dados do pipeline
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
    """Estrutura mapeada do repositório pelo Repository_Analyzer.

    Attributes:
        root_path: Caminho absoluto da raiz do repositório.
        files: Lista de arquivos encontrados.
        metadata: Metadados adicionais do repositório.
    """

    root_path: str
    files: list[FileInfo] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SelectedContext:
    """Contexto selecionado pelo Intelligent_Selector.

    Attributes:
        task_description: Descrição da tarefa original.
        selected_files: Arquivos selecionados como relevantes.
        relevance_scores: Pontuação de relevância por arquivo.
    """

    task_description: str
    selected_files: list[FileInfo] = field(default_factory=list)
    relevance_scores: dict[str, float] = field(default_factory=dict)


@dataclass
class CompressedContext:
    """Contexto comprimido pelo Compressor.

    Attributes:
        task_description: Descrição da tarefa original.
        compressed_content: Conteúdo comprimido/resumido.
        token_count: Estimativa de tokens do conteúdo comprimido.
    """

    task_description: str
    compressed_content: str
    token_count: int


@dataclass
class CachedContext:
    """Contexto verificado/atualizado pelo Context_Cache.

    Attributes:
        task_description: Descrição da tarefa original.
        content: Conteúdo final a ser enviado ao LLM.
        cache_hit: Indica se o resultado veio do cache.
        token_count: Estimativa de tokens do conteúdo.
    """

    task_description: str
    content: str
    cache_hit: bool
    token_count: int
