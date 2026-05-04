"""Persistência do contexto comprimido em disco (stub).

Etapa intermediária do pipeline CLI que salva o contexto comprimido em
um arquivo antes de enviá-lo ao LLM, permitindo auditoria e reuso.
"""

from __future__ import annotations

from tokemize.models import CompressedContext, SavedContext


def save_context(compressed: CompressedContext) -> SavedContext:
    """Persiste o contexto comprimido em disco e retorna o caminho do arquivo.

    Args:
        compressed: Contexto comprimido gerado pelo Compressor.

    Returns:
        SavedContext com o caminho do arquivo salvo e os dados do contexto
        comprimido (stub — retorna caminho padrão sem I/O real).
    """
    context_file_path = "outputs/context_pack.md"
    return SavedContext(
        task_description=compressed.task_description,
        compressed_content=compressed.compressed_content,
        token_count=compressed.token_count,
        context_file_path=context_file_path,
    )
