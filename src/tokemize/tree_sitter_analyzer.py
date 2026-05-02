"""Ponto de entrada público do analisador Tree-sitter do Tokemize.

Re-exporta TreeSitterAnalyzer, UnsupportedLanguageError, ParseError e
SUPPORTED_LANGUAGES do módulo interno para satisfazer o entregável
src/tokemize/tree_sitter_analyzer.py e manter a estrutura de pacotes
em core/parser/.

Uso:
    from tokemize.tree_sitter_analyzer import TreeSitterAnalyzer
    from tokemize.tree_sitter_analyzer import UnsupportedLanguageError
"""

from tokemize.core.parser.tree_sitter_analyzer import (  # noqa: F401
    ParseError,
    SUPPORTED_LANGUAGES,
    TreeSitterAnalyzer,
    UnsupportedLanguageError,
)

__all__ = [
    "TreeSitterAnalyzer",
    "UnsupportedLanguageError",
    "ParseError",
    "SUPPORTED_LANGUAGES",
]
