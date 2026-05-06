"""Modelo de dados para o prompt final gerado pelo Prompt_Builder."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OptimizedPrompt:
    """Prompt final em Markdown gerado pelo Prompt_Builder.

    Representa o resultado da etapa de geração de prompt, contendo o
    conteúdo completo em Markdown pronto para ser copiado para a área de
    transferência e colado no chatbot da IDE.

    Attributes:
        content: Texto completo do prompt em Markdown.
        task_description: Tarefa original preservada sem modificação.
        token_estimate: Estimativa de tokens do conteúdo, calculada como
            ``len(content.split())``.
    """

    content: str
    task_description: str
    token_estimate: int = 0
