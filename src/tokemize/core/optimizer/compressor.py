"""Compressão de contexto do pipeline Tokemize."""

<<<<<<< HEAD
from tokemize.models import CompressedContext
from tokemize.models.artifact import Artifact


def compress_context(artifacts: list[Artifact]) -> CompressedContext:
    """Comprime a lista de artefatos em um contexto compacto em Markdown.

    Agrupa os artefatos por arquivo e gera um bloco Markdown estruturado
    com caminho, linguagem, tipo, nome e linhas de cada artefato.
=======
from __future__ import annotations

from tokemize.models import CompressedContext, SelectedContext


def compress_context(artifacts: list) -> CompressedContext:
    """Comprime e resume os artefatos selecionados.

    Args:
        artifacts: Lista de artefatos selecionados pelo Artifact_Selector.

    Returns:
        CompressedContext com conteúdo vazio e zero tokens (stub).
    """
    return CompressedContext(
        task_description="",
        compressed_content="",
        token_count=0,
    )


def compress_context_from_selected(context: SelectedContext) -> CompressedContext:
    """Comprime e resume o contexto selecionado (compatibilidade legada).
>>>>>>> 135f5f4 (feat(task005): teste task005)

    Args:
        artifacts: Lista de artefatos selecionados pelo Intelligent_Selector.

    Returns:
        CompressedContext com conteúdo Markdown compacto, contagem de tokens
        e contagem de artefatos. Se a lista for vazia, retorna um contexto
        com mensagem de fallback e contagens zeradas.
    """
    if not artifacts:
        return CompressedContext(
            task_description="",
            compressed_content="Nenhum artefato relevante encontrado.",
            token_count=0,
            artifact_count=0,
        )

    # Agrupar artefatos por file_path preservando ordem de inserção
    groups: dict[str, list[Artifact]] = {}
    for artifact in artifacts:
        groups.setdefault(artifact.file_path, []).append(artifact)

    # Gerar blocos Markdown por grupo
    blocks: list[str] = []
    for file_path, artifacts_in_file in groups.items():
        language = artifacts_in_file[0].language
        block = f"### {file_path} ({language})\n"
        for artifact in artifacts_in_file:
            block += (
                f"- [{artifact.type}] {artifact.name} "
                f"(linhas {artifact.start_line}–{artifact.end_line})\n"
            )
        blocks.append(block)

    compressed_content = "".join(blocks)
    token_count = len(compressed_content.split())
    artifact_count = len(artifacts)

    return CompressedContext(
        task_description="",
        compressed_content=compressed_content,
        token_count=token_count,
        artifact_count=artifact_count,
    )
