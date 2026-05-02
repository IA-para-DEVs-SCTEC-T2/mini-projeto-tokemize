"""Ponto de entrada público do scanner do Tokemize.

Re-exporta RepositoryScanner, FileMetadata e ScanResult do módulo interno
para satisfazer o entregável src/tokemize/scanner.py e manter a estrutura
de pacotes em core/parser/.

Uso:
    from tokemize.scanner import RepositoryScanner, FileMetadata, ScanResult
"""

from tokemize.core.parser.scanner import (  # noqa: F401
    DEFAULT_IGNORE_DIRS,
    EXTENSION_TO_LANGUAGE,
    SUPPORTED_EXTENSIONS,
    FileMetadata,
    RepositoryScanner,
    ScanResult,
)

__all__ = [
    "RepositoryScanner",
    "FileMetadata",
    "ScanResult",
    "DEFAULT_IGNORE_DIRS",
    "SUPPORTED_EXTENSIONS",
    "EXTENSION_TO_LANGUAGE",
]
