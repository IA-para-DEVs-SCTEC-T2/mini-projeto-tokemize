"""Scanner do repositório para o pipeline Tokemize.

Expõe duas interfaces:
- ``scan_repository(repo_path)`` — função de pipeline que retorna ``ScanOutput``
  (compatível com o orquestrador e test_stubs.py)
- ``RepositoryScanner``, ``FileMetadata``, ``ScanResult`` — re-exports do
  scanner avançado em ``core/parser/scanner.py``
"""

from __future__ import annotations

from tokemize.core.parser.scanner import (  # noqa: F401
    DEFAULT_IGNORE_DIRS,
    EXTENSION_TO_LANGUAGE,
    SUPPORTED_EXTENSIONS,
    FileMetadata,
    RepositoryScanner,
    ScanResult,
)
from tokemize.models import ScannedFile, ScanOutput

__all__ = [
    "scan_repository",
    "RepositoryScanner",
    "FileMetadata",
    "ScanResult",
    "DEFAULT_IGNORE_DIRS",
    "SUPPORTED_EXTENSIONS",
    "EXTENSION_TO_LANGUAGE",
]


def scan_repository(repo_path: str) -> ScanOutput:
    """Varre o repositório e retorna metadados dos arquivos encontrados.

    Função de pipeline compatível com o orquestrador. Usa o
    ``RepositoryScanner`` internamente e converte o resultado para
    ``ScanOutput`` / ``ScannedFile``.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório.

    Returns:
        ScanOutput com a lista de arquivos encontrados e contadores de
        totais. Se o diretório estiver vazio, retorna ``ScanOutput`` com
        ``files=[]``, ``total_files=0`` e ``skipped_files=0``.

    Raises:
        NotADirectoryError: Se ``repo_path`` não for um diretório válido.

    Example:
        >>> output = scan_repository(".")
        >>> output.total_files == len(output.files)
        True
    """
    from pathlib import Path

    if not repo_path.strip() or "\x00" in repo_path:
        raise NotADirectoryError(
            f"O caminho fornecido não é um diretório válido: {repo_path}"
        )

    scanner = RepositoryScanner()
    try:
        result = scanner.scan(Path(repo_path))
    except ValueError as exc:
        raise NotADirectoryError(
            f"O caminho fornecido não é um diretório válido: {repo_path}"
        ) from exc

    files: list[ScannedFile] = []
    for fm in result.files:
        files.append(
            ScannedFile(
                path=str(fm.relative_path),
                absolute_path=str(fm.path),
                language=fm.language,
                extension=fm.extension,
                size_bytes=fm.size_bytes,
                line_count=fm.line_count,
            )
        )

    return ScanOutput(
        repo_path=repo_path,
        files=files,
        total_files=result.total_files,
        skipped_files=result.skipped_files,
    )
