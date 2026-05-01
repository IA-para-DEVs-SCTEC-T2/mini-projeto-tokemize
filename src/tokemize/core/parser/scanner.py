"""Scanner de repositório para o Tokemize.

Percorre um diretório recursivamente, aplica lista de ignores e coleta
metadados dos arquivos de código-fonte válidos.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Diretórios ignorados por padrão
DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        ".github",
        ".kiro",
        ".venv",
        "venv",
        "env",
        ".env",
        "node_modules",
        "dist",
        "build",
        ".cache",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        "coverage",
        ".tox",
        "eggs",
        ".eggs",
        "*.egg-info",
        "target",        # Java/Maven
        "out",           # Java/Gradle
        ".idea",
        ".vscode",
        "outputs",
    }
)

# Extensões de arquivo suportadas para análise
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".java", ".js", ".ts"}
)

# Mapeamento de extensão para linguagem
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".java": "java",
    ".js": "javascript",
    ".ts": "typescript",
}


@dataclass
class FileMetadata:
    """Metadados de um arquivo de código-fonte encontrado pelo scanner.

    Attributes:
        path: Caminho absoluto do arquivo.
        relative_path: Caminho relativo à raiz do repositório.
        language: Linguagem detectada pela extensão.
        extension: Extensão do arquivo (ex: ".py").
        size_bytes: Tamanho do arquivo em bytes.
        line_count: Número de linhas do arquivo.
    """

    path: Path
    relative_path: Path
    language: str
    extension: str
    size_bytes: int
    line_count: int = 0


@dataclass
class ScanResult:
    """Resultado de uma varredura de repositório.

    Attributes:
        root: Diretório raiz varrido.
        files: Lista de metadados dos arquivos encontrados.
        ignored_dirs: Conjunto de diretórios ignorados durante a varredura.
        total_files: Total de arquivos válidos encontrados.
        skipped_files: Total de arquivos ignorados (extensão não suportada).
    """

    root: Path
    files: list[FileMetadata] = field(default_factory=list)
    ignored_dirs: set[str] = field(default_factory=set)
    total_files: int = 0
    skipped_files: int = 0


class RepositoryScanner:
    """Percorre um repositório e coleta metadados dos arquivos de código.

    Aplica uma lista de diretórios e extensões a ignorar, retornando apenas
    arquivos de código-fonte válidos com seus metadados.

    Args:
        ignore_dirs: Conjunto de nomes de diretórios a ignorar.
            Mescla com DEFAULT_IGNORE_DIRS se não fornecido.
        supported_extensions: Conjunto de extensões suportadas.
            Usa SUPPORTED_EXTENSIONS por padrão.
        max_file_size_bytes: Tamanho máximo de arquivo em bytes.
            Arquivos maiores são ignorados. Padrão: 1 MB.

    Example:
        >>> scanner = RepositoryScanner()
        >>> result = scanner.scan(Path("/meu/projeto"))
        >>> for f in result.files:
        ...     print(f.relative_path, f.language)
    """

    def __init__(
        self,
        ignore_dirs: set[str] | None = None,
        supported_extensions: set[str] | None = None,
        max_file_size_bytes: int = 1024 * 1024,  # 1 MB
    ) -> None:
        self._ignore_dirs: frozenset[str] = (
            DEFAULT_IGNORE_DIRS | frozenset(ignore_dirs)
            if ignore_dirs
            else DEFAULT_IGNORE_DIRS
        )
        self._supported_extensions: frozenset[str] = (
            frozenset(supported_extensions)
            if supported_extensions
            else SUPPORTED_EXTENSIONS
        )
        self._max_file_size_bytes = max_file_size_bytes

    @property
    def ignore_dirs(self) -> frozenset[str]:
        """Conjunto de diretórios ignorados pelo scanner."""
        return self._ignore_dirs

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Conjunto de extensões suportadas pelo scanner."""
        return self._supported_extensions

    def scan(self, root: Path) -> ScanResult:
        """Percorre o repositório a partir de `root` e coleta metadados.

        Args:
            root: Diretório raiz do repositório a ser varrido.

        Returns:
            ScanResult com a lista de arquivos válidos e estatísticas.

        Raises:
            NotADirectoryError: Se `root` não for um diretório válido.
        """
        root = root.resolve()
        if not root.is_dir():
            raise NotADirectoryError(
                f"O caminho fornecido não é um diretório válido: {root}"
            )

        result = ScanResult(root=root)
        logger.info("Iniciando varredura em: %s", root)

        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            current_dir = Path(dirpath)

            # Filtrar subdiretórios ignorados in-place (afeta os.walk)
            original_dirs = list(dirnames)
            dirnames[:] = [
                d for d in dirnames if not self._should_ignore_dir(d)
            ]

            ignored = set(original_dirs) - set(dirnames)
            result.ignored_dirs.update(ignored)

            for filename in filenames:
                file_path = current_dir / filename
                ext = file_path.suffix.lower()

                if ext not in self._supported_extensions:
                    result.skipped_files += 1
                    continue

                metadata = self._collect_metadata(file_path, root, ext)
                if metadata is None:
                    result.skipped_files += 1
                    continue

                result.files.append(metadata)
                result.total_files += 1
                logger.debug("Arquivo encontrado: %s", metadata.relative_path)

        logger.info(
            "Varredura concluída: %d arquivos válidos, %d ignorados",
            result.total_files,
            result.skipped_files,
        )
        return result

    def _should_ignore_dir(self, dirname: str) -> bool:
        """Verifica se um diretório deve ser ignorado.

        Args:
            dirname: Nome do diretório (não o caminho completo).

        Returns:
            True se o diretório deve ser ignorado.
        """
        if dirname in self._ignore_dirs:
            return True
        # Suporte a padrões com wildcard simples (ex: "*.egg-info")
        for pattern in self._ignore_dirs:
            if "*" in pattern:
                prefix = pattern.replace("*", "")
                if dirname.endswith(prefix) or dirname.startswith(
                    prefix.strip(".")
                ):
                    return True
        return False

    def _collect_metadata(
        self, file_path: Path, root: Path, ext: str
    ) -> FileMetadata | None:
        """Coleta metadados de um arquivo.

        Args:
            file_path: Caminho absoluto do arquivo.
            root: Diretório raiz para calcular o caminho relativo.
            ext: Extensão do arquivo.

        Returns:
            FileMetadata ou None se o arquivo não puder ser lido.
        """
        try:
            stat = file_path.stat()
            size = stat.st_size

            if size > self._max_file_size_bytes:
                logger.warning(
                    "Arquivo ignorado por exceder tamanho máximo (%d bytes): %s",
                    self._max_file_size_bytes,
                    file_path,
                )
                return None

            line_count = self._count_lines(file_path)
            language = EXTENSION_TO_LANGUAGE.get(ext, "unknown")

            return FileMetadata(
                path=file_path,
                relative_path=file_path.relative_to(root),
                language=language,
                extension=ext,
                size_bytes=size,
                line_count=line_count,
            )
        except (OSError, PermissionError) as exc:
            logger.warning("Não foi possível ler o arquivo %s: %s", file_path, exc)
            return None

    def _count_lines(self, file_path: Path) -> int:
        """Conta o número de linhas de um arquivo.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Número de linhas ou 0 em caso de erro de leitura.
        """
        try:
            with open(file_path, "rb") as f:
                return sum(1 for _ in f)
        except (OSError, PermissionError):
            return 0
