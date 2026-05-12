"""Construção do prompt otimizado para envio ao LLM (stub).

Monta o documento Markdown final a partir do contexto comprimido,
da descrição da tarefa e do caminho do arquivo de contexto salvo.
"""

from __future__ import annotations

from tokemize.models import CompressedContext, OptimizedPrompt


def build_prompt(
    compressed: CompressedContext,
    task_description: str,
    context_file_path: str | None,
) -> OptimizedPrompt:
    """Constrói o prompt otimizado a partir do contexto comprimido.

    Args:
        compressed: Contexto comprimido gerado pelo Compressor.
        task_description: Descrição da tarefa técnica fornecida pelo usuário.
        context_file_path: Caminho do arquivo de contexto salvo em disco,
            ou ``None`` se não foi salvo.

    Returns:
        OptimizedPrompt com o conteúdo Markdown do prompt e a estimativa
        de tokens (stub).
    """
    lines = ["# Prompt otimizado pelo Tokemize", "", "## Tarefa", "", task_description, ""]

    if compressed.compressed_content:
        lines += ["## Contexto", "", compressed.compressed_content, ""]

    if context_file_path:
        lines += [f"<!-- context_file: {context_file_path} -->", ""]

    content = "\n".join(lines)
    token_estimate = len(content.split())

    return OptimizedPrompt(
        content=content,
        task_description=task_description,
        token_estimate=token_estimate,
    )
