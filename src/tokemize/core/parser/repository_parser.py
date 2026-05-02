"""Integração entre Scanner e TreeSitterAnalyzer para o Tokemize.

Orquestra o fluxo completo de análise de repositório:
    RepositoryScanner → [FileMetadata] → TreeSitterAnalyzer → [Artifact]

Este módulo é o elo entre as duas camadas de análise, expondo uma interface
única (parse_repository) que recebe um diretório e retorna todos os artefatos
estruturais extraídos dos arquivos de código encontrados.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from tokemize.core.parser.scanner import FileMetadata, RepositoryScanner
from tokemize.core.parser.tree_sitter_analyzer import TreeSitterAnalyzer
from tokemize.models.artifact import Artifact

logger = logging.getLogger(__name__)


@dataclass
class RepositoryParseResult:
    """Resultado completo da análise de um repositório.

    Contém tanto os metadados dos arquivos encontrados pelo scanner quanto
    os artefatos estruturais extraídos pelo analyzer, além de estatísticas
    de execução.

    Attributes:
        root: Diretório raiz analisado.
        files: Lista de metadados dos arquivos encontrados pelo scanner.
        artifacts: Lista de artefatos extraídos pelo analyzer.
        total_files: Total de arquivos válidos encontrados.
        total_artifacts: Total de artefatos extraídos.
        skipped_files: Arquivos ignorados (extensão não suportada ou erro).
        failed_files: Arquivos que falharam na análise sintática.
        elapsed_seconds: Tempo total de execução em segundos.
    """

    root: Path
    files: list[FileMetadata] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    total_files: int = 0
    total_artifacts: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    elapsed_seconds: float = 0.0

    def artifacts_by_file(self) -> dict[str, list[Artifact]]:
        """Agrupa artefatos por caminho de arquivo.

        Returns:
            Dicionário mapeando file_path → lista de Artifact.

        Example:
            >>> result = parse_repository(Path("/repo"))
            >>> by_file = result.artifacts_by_file()
            >>> for path, arts in by_file.items():
            ...     print(path, len(arts))
        """
        grouped: dict[str, list[Artifact]] = {}
        for artifact in self.artifacts:
            grouped.setdefault(artifact.file_path, []).append(artifact)
        return grouped

    def artifacts_by_type(self) -> dict[str, list[Artifact]]:
        """Agrupa artefatos por tipo (function, class, method, import).

        Returns:
            Dicionário mapeando type → lista de Artifact.
        """
        grouped: dict[str, list[Artifact]] = {}
        for artifact in self.artifacts:
            grouped.setdefault(artifact.type, []).append(artifact)
        return grouped

    def artifacts_by_language(self) -> dict[str, list[Artifact]]:
        """Agrupa artefatos por linguagem de programação.

        Returns:
            Dicionário mapeando language → lista de Artifact.
        """
        grouped: dict[str, list[Artifact]] = {}
        for artifact in self.artifacts:
            grouped.setdefault(artifact.language, []).append(artifact)
        return grouped

    def summary(self) -> str:
        """Retorna um resumo legível do resultado da análise.

        Returns:
            String formatada com as principais métricas.
        """
        by_type = self.artifacts_by_type()
        by_lang = self.artifacts_by_language()
        lines = [
            f"Repositório: {self.root}",
            f"Arquivos analisados : {self.total_files}",
            f"Arquivos ignorados  : {self.skipped_files}",
            f"Arquivos com falha  : {self.failed_files}",
            f"Artefatos extraídos : {self.total_artifacts}",
            f"  classes   : {len(by_type.get('class', []))}",
            f"  funções   : {len(by_type.get('function', []))}",
            f"  métodos   : {len(by_type.get('method', []))}",
            f"  imports   : {len(by_type.get('import', []))}",
            f"Linguagens          : {', '.join(sorted(by_lang.keys())) or 'nenhuma'}",
            f"Tempo de execução   : {self.elapsed_seconds:.3f}s",
        ]
        return "\n".join(lines)


class RepositoryParser:
    """Orquestra Scanner + TreeSitterAnalyzer para análise completa de repositório.

    Combina o RepositoryScanner (varredura de arquivos) com o TreeSitterAnalyzer
    (extração de artefatos) em um único fluxo coeso.

    Args:
        scanner: Instância de RepositoryScanner. Cria uma com defaults se None.
        analyzer: Instância de TreeSitterAnalyzer. Cria uma com defaults se None.

    Example:
        >>> parser = RepositoryParser()
        >>> result = parser.parse(Path("/meu/projeto"))
        >>> print(result.summary())
        >>> for artifact in result.artifacts:
        ...     print(artifact.type, artifact.name, artifact.file_path)
    """

    def __init__(
        self,
        scanner: RepositoryScanner | None = None,
        analyzer: TreeSitterAnalyzer | None = None,
    ) -> None:
        self._scanner = scanner or RepositoryScanner()
        self._analyzer = analyzer or TreeSitterAnalyzer()

    @property
    def scanner(self) -> RepositoryScanner:
        """Scanner configurado para este parser."""
        return self._scanner

    @property
    def analyzer(self) -> TreeSitterAnalyzer:
        """Analyzer configurado para este parser."""
        return self._analyzer

    def parse(self, root: Path) -> RepositoryParseResult:
        """Executa o pipeline completo: scan → analyze → resultado.

        1. Scanner percorre o repositório e coleta FileMetadata
        2. Analyzer extrai artefatos de cada arquivo encontrado
        3. Retorna RepositoryParseResult com tudo consolidado

        Args:
            root: Diretório raiz do repositório a ser analisado.

        Returns:
            RepositoryParseResult com arquivos, artefatos e métricas.

        Raises:
            NotADirectoryError: Se `root` não for um diretório válido.
        """
        start = time.perf_counter()
        root = Path(root).resolve()

        logger.info("Iniciando análise do repositório: %s", root)

        # Etapa 1: Scanner
        scan_result = self._scanner.scan(root)
        logger.info(
            "Scanner concluído: %d arquivos encontrados, %d ignorados",
            scan_result.total_files,
            scan_result.skipped_files,
        )

        result = RepositoryParseResult(
            root=root,
            files=scan_result.files,
            total_files=scan_result.total_files,
            skipped_files=scan_result.skipped_files,
        )

        # Etapa 2: Analyzer — processa cada arquivo encontrado
        for file_meta in scan_result.files:
            try:
                artifacts = self._analyzer.analyze(file_meta.path)
                result.artifacts.extend(artifacts)
                logger.debug(
                    "Arquivo '%s': %d artefatos extraídos",
                    file_meta.relative_path,
                    len(artifacts),
                )
            except Exception as exc:  # noqa: BLE001
                result.failed_files += 1
                logger.error(
                    "Falha ao analisar '%s': %s",
                    file_meta.relative_path,
                    exc,
                    exc_info=True,
                )

        result.total_artifacts = len(result.artifacts)
        result.elapsed_seconds = time.perf_counter() - start

        logger.info(
            "Análise concluída: %d artefatos em %.3fs",
            result.total_artifacts,
            result.elapsed_seconds,
        )
        return result

    def parse_streaming(self, root: Path):
        """Versão lazy do parse — gera artefatos à medida que os encontra.

        Usa iter_files() do scanner para não acumular FileMetadata em memória.
        Ideal para repositórios muito grandes.

        Args:
            root: Diretório raiz do repositório.

        Yields:
            Artifact extraído de cada arquivo válido encontrado.

        Raises:
            NotADirectoryError: Se `root` não for um diretório válido.
        """
        root = Path(root).resolve()
        logger.info("Iniciando análise streaming do repositório: %s", root)

        for file_meta in self._scanner.iter_files(root):
            try:
                artifacts = self._analyzer.analyze(file_meta.path)
                yield from artifacts
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Falha ao analisar '%s': %s",
                    file_meta.path,
                    exc,
                    exc_info=True,
                )


def parse_repository(
    root: Path,
    ignore_dirs: set[str] | None = None,
    max_file_size_bytes: int = 1024 * 1024,
) -> RepositoryParseResult:
    """Função de conveniência para análise completa de um repositório.

    Cria um RepositoryParser com configurações opcionais e executa o pipeline.

    Args:
        root: Diretório raiz do repositório a ser analisado.
        ignore_dirs: Diretórios adicionais a ignorar (mescla com os padrões).
        max_file_size_bytes: Tamanho máximo de arquivo em bytes. Padrão: 1 MB.

    Returns:
        RepositoryParseResult com arquivos, artefatos e métricas.

    Example:
        >>> from tokemize.core.parser.repository_parser import parse_repository
        >>> result = parse_repository(Path("/meu/projeto"))
        >>> print(result.summary())
    """
    scanner = RepositoryScanner(
        ignore_dirs=ignore_dirs,
        max_file_size_bytes=max_file_size_bytes,
    )
    parser = RepositoryParser(scanner=scanner)
    return parser.parse(root)
