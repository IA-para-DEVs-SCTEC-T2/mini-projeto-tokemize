"""Módulo responsável por gerar o prompt final em Markdown para chatbots de IDE.

Transforma um CompressedContext e uma task_description em um
OptimizedPrompt estruturado, pronto para ser copiado para a área de
transferência e colado no chatbot da IDE.
"""

from __future__ import annotations

from tokemize.models import CompressedContext, OptimizedPrompt


def build_prompt(
    context: CompressedContext,
    task_description: str,
    context_file_path: str | None = None,
) -> OptimizedPrompt:
    """Gera um prompt Markdown estruturado a partir do contexto comprimido.

    Monta o prompt com as seguintes seções, nesta ordem:
    1. Cabeçalho ``# Prompt otimizado pelo Tokemize``
    2. ``## Tarefa`` com a ``task_description`` verbatim
    3. ``## Objetivo`` com instrução derivada da tarefa
    4. ``## Contexto relevante encontrado`` com o conteúdo comprimido
    5. ``## Instrução para a IDE`` com orientações de uso do contexto
    6. ``## Arquivo de contexto`` (apenas quando ``context_file_path`` é fornecido)
       com referências nos formatos Kiro/Cursor e Copilot/Windsurf

    Args:
        context: Contexto comprimido gerado pelo Compressor.
        task_description: Descrição da tarefa técnica, preservada verbatim.
        context_file_path: Caminho relativo ao repositório do arquivo de
            contexto salvo pelo Context_Store. Quando fornecido, o prompt
            inclui a seção ``## Arquivo de contexto`` com referências nos
            formatos ``#[[file:...]]`` (Kiro/Cursor) e ``@...``
            (Copilot/Windsurf). Quando ``None``, o prompt é gerado sem
            essa seção.

    Returns:
        OptimizedPrompt com o conteúdo Markdown completo, a
        ``task_description`` original e a estimativa de tokens calculada
        como ``len(content.split())``.
    """
    content = (
        "# Prompt otimizado pelo Tokemize\n"
        "\n"
        "## Tarefa\n"
        "\n"
        f"{task_description}\n"
        "\n"
        "## Objetivo\n"
        "\n"
        f"Analise o contexto abaixo e {task_description}.\n"
        "\n"
        "## Contexto relevante encontrado\n"
        "\n"
        f"{context.compressed_content}\n"
        "\n"
        "## Instrução para a IDE\n"
        "\n"
        "Use o contexto acima como base principal para responder à tarefa.\n"
        "Foque nos artefatos listados e nos arquivos indicados.\n"
        "Ao propor mudanças:\n"
        "- Explique brevemente a causa provável.\n"
        "- Mostre os arquivos que precisam ser alterados.\n"
        "- Sugira ou atualize testes relacionados.\n"
        "- Evite modificar arquivos fora do contexto listado, a menos que seja necessário.\n"
    )

    if context_file_path is not None:
        content += (
            "\n"
            "## Arquivo de contexto\n"
            "\n"
            "O contexto completo foi salvo em:\n"
            "\n"
            f"- `#[[file:{context_file_path}]]` (Kiro/Cursor)\n"
            f"- `@{context_file_path}` (Copilot/Windsurf)\n"
            "\n"
            "Você pode referenciar esse arquivo diretamente no chatbot da sua IDE.\n"
        )

    token_estimate = len(content.split())

    return OptimizedPrompt(
        content=content,
        task_description=task_description,
        token_estimate=token_estimate,
    )
