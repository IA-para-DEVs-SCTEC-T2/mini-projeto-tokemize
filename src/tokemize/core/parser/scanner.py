"""Scanner de repositório para o Tokemize.

Percorre um diretório recursivamente, aplica lista de ignores e coleta
metadados dos arquivos de código-fonte válidos.

Melhorias implementadas:
- Proteção explícita contra symlinks recursivos
- Método iter_files() para avaliação preguiçosa (lazy/streaming)
- Documentação de thread-safety
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

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
        char_count: Número de caracteres (codepoints UTF-8) do arquivo.
    """

    path: Path
    relative_path: Path
    language: str
    extension: str
    size_bytes: int
    line_count: int = 0
    char_count: int = 0


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

    Proteção contra symlinks: diretórios que são links simbólicos são ignorados
    por padrão para evitar loops infinitos em repositórios com symlinks recursivos.

    Thread-safety: esta classe é segura para uso em múltiplas threads desde que
    cada thread use sua própria instância. O estado interno (_ignore_dirs,
    _supported_extensions, _max_file_size_bytes) é imutável após a construção.

    Args:
        ignore_dirs: Conjunto de nomes de diretórios a ignorar.
            Mescla com DEFAULT_IGNORE_DIRS se não fornecido.
        supported_extensions: Conjunto de extensões suportadas.
            Usa SUPPORTED_EXTENSIONS por padrão.
        max_file_size_bytes: Tamanho máximo de arquivo em bytes.
            Arquivos maiores são ignorados. Padrão: 1 MB.
        follow_symlinks: Se True, segue links simbólicos de diretórios.
            Padrão: False (proteção contra loops infinitos).

    Example:
        >>> scanner = RepositoryScanner()
        >>> result = scanner.scan(Path("/meu/projeto"))
        >>> for f in result.files:
        ...     print(f.relative_path, f.language)

        >>> # Uso com streaming (baixo uso de memória)
        >>> for metadata in scanner.iter_files(Path("/meu/projeto")):
        ...     print(metadata.relative_path)
    """

    def __init__(
        self,
        ignore_dirs: set[str] | None = None,
        supported_extensions: set[str] | None = None,
        max_file_size_bytes: int = 1024 * 1024,  # 1 MB
        follow_symlinks: bool = False,
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
        self._follow_symlinks = follow_symlinks

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

        Consome iter_files() internamente e materializa o resultado em memória.
        Para repositórios muito grandes, prefira iter_files() diretamente.

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

        for dirpath, dirnames, filenames in os.walk(
            root, topdown=True, followlinks=self._follow_symlinks
        ):
            current_dir = Path(dirpath)

            # Filtrar subdiretórios ignorados in-place (afeta os.walk)
            original_dirs = list(dirnames)
            dirnames[:] = [
                d for d in dirnames
                if not self._should_ignore_dir(d, current_dir)
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

    def iter_files(self, root: Path) -> Generator[FileMetadata, None, None]:
        """Percorre o repositório gerando FileMetadata um a um (lazy/streaming).

        Ideal para repositórios grandes onde carregar todos os metadados em
        memória de uma vez seria custoso. Não acumula resultados internamente.

        Args:
            root: Diretório raiz do repositório a ser varrido.

        Yields:
            FileMetadata para cada arquivo válido encontrado.

        Raises:
            NotADirectoryError: Se `root` não for um diretório válido.

        Example:
            >>> scanner = RepositoryScanner()
            >>> for metadata in scanner.iter_files(Path("/meu/projeto")):
            ...     process(metadata)  # processa um arquivo por vez
        """
        root = root.resolve()
        if not root.is_dir():
            raise NotADirectoryError(
                f"O caminho fornecido não é um diretório válido: {root}"
            )

        logger.info("Iniciando varredura lazy em: %s", root)

        for dirpath, dirnames, filenames in os.walk(
            root, topdown=True, followlinks=self._follow_symlinks
        ):
            current_dir = Path(dirpath)

            dirnames[:] = [
                d for d in dirnames
                if not self._should_ignore_dir(d, current_dir)
            ]

            for filename in filenames:
                file_path = current_dir / filename
                ext = file_path.suffix.lower()

                if ext not in self._supported_extensions:
                    continue

                metadata = self._collect_metadata(file_path, root, ext)
                if metadata is not None:
                    logger.debug("Arquivo encontrado: %s", metadata.relative_path)
                    yield metadata

    def _should_ignore_dir(self, dirname: str, parent: Path) -> bool:
        """Verifica se um diretório deve ser ignorado.

        Ignora diretórios que:
        - Estão na lista de ignores (por nome exato ou padrão wildcard)
        - São links simbólicos quando follow_symlinks=False

        Args:
            dirname: Nome do diretório (não o caminho completo).
            parent: Diretório pai, usado para verificar se é symlink.

        Returns:
            True se o diretório deve ser ignorado.
        """
        # Verificação de symlink — evita loops infinitos
        if not self._follow_symlinks:
            full_path = parent / dirname
            if full_path.is_symlink():
                logger.debug(
                    "Diretório symlink ignorado (follow_symlinks=False): %s",
                    full_path,
                )
                return True

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
            FileMetadata ou None se o arquivo não puder ser lido ou exceder
            o limite de tamanho.
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
            char_count = self._count_chars(file_path)
            language = EXTENSION_TO_LANGUAGE.get(ext, "unknown")

            return FileMetadata(
                path=file_path,
                relative_path=file_path.relative_to(root),
                language=language,
                extension=ext,
                size_bytes=size,
                line_count=line_count,
                char_count=char_count,
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

    def _count_chars(self, file_path: Path) -> int:
        """Conta o número de caracteres (codepoints UTF-8) de um arquivo.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Número de caracteres ou 0 em caso de erro de leitura.
        """
        try:
            return len(file_path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, PermissionError):
            return 0
