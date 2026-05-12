"""Persistência do contexto comprimido em disco (stub).

Etapa intermediária do pipeline CLI que salva o contexto comprimido em
um arquivo antes de enviá-lo ao LLM, permitindo auditoria e reuso.
"""

from __future__ import annotations

from tokemize.models import CompressedContext, SavedContext


def save_context(
    content: str,
    task_description: str,
    repo_path: str,
) -> str | None:
    """Persiste o conteúdo do contexto em disco e retorna o caminho do arquivo.

    Args:
        content: Conteúdo comprimido a ser salvo.
        task_description: Descrição da tarefa técnica (usada para nomear o arquivo).
        repo_path: Caminho do repositório analisado.

    Returns:
        Caminho do arquivo salvo, ou ``None`` se o conteúdo estiver vazio
        (stub — retorna caminho padrão sem I/O real).
    """
    if not content:
        return None
    slug = "-".join(task_description.lower().split())[:50]
    return f".tokemize/context/{slug}.md"


def save_context_model(compressed: CompressedContext) -> SavedContext:
    """Persiste o contexto comprimido e retorna um SavedContext (legado).

    Args:
        compressed: Contexto comprimido gerado pelo Compressor.

    Returns:
        SavedContext com o caminho do arquivo salvo (stub).
    """
    context_file_path = "outputs/context_pack.md"
    return SavedContext(
        task_description=compressed.task_description,
        compressed_content=compressed.compressed_content,
        token_count=compressed.token_count,
        context_file_path=context_file_path,
    )
