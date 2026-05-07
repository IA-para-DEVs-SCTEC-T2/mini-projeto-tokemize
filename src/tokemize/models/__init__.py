"""Modelos de dados compartilhados entre as etapas do pipeline Tokemize.

Define os dataclasses que representam os contratos de interface entre cada
etapa do pipeline: scanner → analyzer → embeddings → selector →
summarizer → generator → reporter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from tokemize.models.artifact import Artifact
from tokemize.models.file_analysis import FileAnalysis
from tokemize.models.optimized_prompt import OptimizedPrompt


# ── Scanner ───────────────────────────────────────────────────────────────────


@dataclass
class ScannedFile:
    """Metadados de um arquivo encontrado pelo scanner.

    Attributes:
        path: Caminho relativo à raiz do repositório.
        absolute_path: Caminho absoluto no sistema de arquivos.
        language: Linguagem detectada (ex: ``"python"``, ``"javascript"``,
            ``"unknown"``).
        extension: Extensão do arquivo incluindo o ponto (ex: ``".py"``).
        size_bytes: Tamanho do arquivo em bytes.
        line_count: Número de linhas do arquivo.
    """

    path: str
    absolute_path: str
    language: str
    extension: str
    size_bytes: int
    line_count: int


@dataclass
class ScanOutput:
    """Resultado da etapa de varredura do repositório.

    Attributes:
        repo_path: Caminho para a raiz do repositório analisado.
        files: Lista de arquivos encontrados com seus metadados.
        total_files: Total de arquivos incluídos em ``files``.
        skipped_files: Total de arquivos ignorados durante a varredura.
    """

    repo_path: str
    files: list[ScannedFile] = field(default_factory=list)
    total_files: int = 0
    skipped_files: int = 0


# ── Analyzer ──────────────────────────────────────────────────────────────────


@dataclass
class AnalyzedFile:
    """Arquivo enriquecido com análise estrutural.

    Attributes:
        path: Caminho relativo à raiz do repositório.
        language: Linguagem detectada (ex: ``"python"``).
        size_bytes: Tamanho do arquivo em bytes.
        line_count: Número de linhas do arquivo.
        file_type: Classificação do arquivo. Um de: ``"source"``,
            ``"config"``, ``"test"``, ``"doc"``, ``"unknown"``.
        artifact_count: Número de artefatos extraídos (funções, classes etc.).
        content: Conteúdo textual completo do arquivo.
        relevance_hint: Score heurístico de relevância potencial no intervalo
            ``[0.0, 1.0]``, calculado antes dos embeddings.
    """

    path: str
    language: str
    size_bytes: int
    line_count: int
    file_type: str
    artifact_count: int
    content: str
    relevance_hint: float


@dataclass
class AnalysisOutput:
    """Resultado da etapa de análise estrutural.

    Attributes:
        analyzed_files: Lista de arquivos enriquecidos com metadados
            estruturais.
        total_analyzed: Total de arquivos analisados com sucesso.
        total_skipped: Total de arquivos ignorados por falha na análise.
    """

    analyzed_files: list[AnalyzedFile] = field(default_factory=list)
    total_analyzed: int = 0
    total_skipped: int = 0


# ── Embeddings ────────────────────────────────────────────────────────────────


@dataclass
class EmbeddedFile:
    """Arquivo com vetor de embedding gerado.

    Attributes:
        path: Caminho relativo à raiz do repositório.
        language: Linguagem detectada (ex: ``"python"``).
        content: Conteúdo textual do arquivo.
        embedding: Vetor de embedding gerado. Lista vazia se a geração
            falhou para este arquivo.
    """

    path: str
    language: str
    content: str
    embedding: list[float] = field(default_factory=list)


@dataclass
class EmbeddingsOutput:
    """Resultado da etapa de geração de embeddings.

    Attributes:
        embedded_files: Lista de arquivos com seus vetores de embedding.
        total_embedded: Total de arquivos com embedding gerado com sucesso
            (``embedding != []``).
        total_failed: Total de arquivos cujo embedding falhou
            (``embedding == []``).
    """

    embedded_files: list[EmbeddedFile] = field(default_factory=list)
    total_embedded: int = 0
    total_failed: int = 0


# ── Selector ──────────────────────────────────────────────────────────────────


@dataclass
class SelectedFile:
    """Arquivo selecionado com score de relevância semântica.

    Attributes:
        path: Caminho relativo à raiz do repositório.
        language: Linguagem detectada (ex: ``"python"``).
        content: Conteúdo textual do arquivo.
        relevance_score: Score de similaridade coseno com a tarefa, no
            intervalo ``[0.0, 1.0]``.
    """

    path: str
    language: str
    content: str
    relevance_score: float


@dataclass
class SelectionOutput:
    """Resultado da etapa de seleção de arquivos relevantes.

    Attributes:
        task: Descrição textual da tarefa técnica fornecida pelo usuário.
        selected_files: Lista de arquivos selecionados, ordenados por
            ``relevance_score`` decrescente.
        total_candidates: Total de arquivos avaliados antes da filtragem.
    """

    task: str = ""
    selected_files: list[SelectedFile] = field(default_factory=list)
    total_candidates: int = 0


# ── Summarizer ────────────────────────────────────────────────────────────────


@dataclass
class SummaryOutput:
    """Resultado da etapa de sumarização e compressão de contexto.

    Attributes:
        summarized_content: Conteúdo resumido e comprimido dos arquivos
            selecionados.
        token_count: Estimativa do número de tokens em
            ``summarized_content``.
        files_summarized: Total de arquivos cujo conteúdo foi incluído em
            ``summarized_content``.
    """

    summarized_content: str = ""
    token_count: int = 0
    files_summarized: int = 0


# ── Generator ─────────────────────────────────────────────────────────────────


@dataclass
class GeneratorOutput:
    """Resultado da etapa de geração do prompt final.

    Attributes:
        prompt: Prompt final formatado e pronto para envio ao LLM.
        token_count: Estimativa do número de tokens no ``prompt`` gerado.
    """

    prompt: str = ""
    token_count: int = 0


# ── Pipeline Result ───────────────────────────────────────────────────────────


@dataclass
class PipelineResult:
    """Resultado completo da execução do pipeline Tokemize.

    Attributes:
        success: ``True`` se todas as 7 etapas foram concluídas sem erro.
        prompt: Prompt final gerado pelo pipeline. Vazio em caso de falha.
        failed_stage: Nome da etapa que falhou, ou ``None`` se sucesso.
            Um de: ``"scanner"``, ``"analyzer"``, ``"embeddings"``,
            ``"selector"``, ``"summarizer"``, ``"generator"``,
            ``"reporter"``.
        error_message: Representação em string da exceção capturada, ou
            ``None`` se sucesso.
        elapsed_seconds: Tempo total de execução do pipeline em segundos,
            medido com ``time.perf_counter()``.
        stages_completed: Lista de nomes das etapas concluídas com sucesso,
            na ordem de execução.
    """

    success: bool = False
    prompt: str = ""
    failed_stage: Optional[str] = None
    error_message: Optional[str] = None
    elapsed_seconds: float = 0.0
    stages_completed: list[str] = field(default_factory=list)


# ── Modelos do pipeline CLI (legado) ─────────────────────────────────────────


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
    metadata: dict = field(default_factory=dict)


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
    relevance_scores: dict = field(default_factory=dict)


@dataclass
class CompressedContext:
    """Contexto comprimido pelo Compressor.

    Attributes:
        task_description: Descrição da tarefa original.
        compressed_content: Conteúdo comprimido/resumido.
        token_count: Estimativa de tokens do conteúdo comprimido.
        artifact_count: Número de artefatos incluídos no contexto comprimido.
    """

    task_description: str
    compressed_content: str
    token_count: int
    artifact_count: int = 0


@dataclass
class SavedContext:
    """Contexto comprimido persistido em disco pelo Context_Saver.

    Attributes:
        task_description: Descrição da tarefa original.
        compressed_content: Conteúdo comprimido/resumido.
        token_count: Estimativa de tokens do conteúdo comprimido.
        context_file_path: Caminho do arquivo onde o contexto foi salvo.
    """

    task_description: str
    compressed_content: str
    token_count: int
    context_file_path: str


@dataclass
class CachedContext:
    """Contexto verificado/atualizado pelo Context_Cache.

    Attributes:
        task_description: Descrição da tarefa original.
        content: Conteúdo final a ser enviado ao LLM.
        cache_hit: Indica se o resultado veio do cache.
        token_count: Estimativa de tokens do conteúdo.
        context_file_path: Caminho do arquivo de contexto salvo em disco.
    """

    task_description: str
    content: str
    cache_hit: bool
    token_count: int
    context_file_path: str = ""
