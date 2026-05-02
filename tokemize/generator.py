"""Stub funcional da etapa de geração do prompt final.

Este módulo implementa a função `generate_prompt`, responsável por montar
o prompt final otimizado combinando o contexto resumido com a descrição
da tarefa fornecida pelo usuário.
"""

from __future__ import annotations

from tokemize.models import GeneratorOutput, SummaryOutput


def generate_prompt(summary_output: SummaryOutput, task: str) -> GeneratorOutput:
    """Monta o prompt final combinando contexto resumido e descrição da tarefa.

    Args:
        summary_output: Resultado da etapa de sumarização contendo o
            conteúdo resumido dos arquivos selecionados.
        task: Descrição textual da tarefa técnica fornecida pelo usuário.

    Returns:
        GeneratorOutput com o prompt final formatado. Se
        ``summary_output.summarized_content`` estiver vazio, retorna
        ``GeneratorOutput(prompt=task, token_count=0)`` — o prompt mínimo
        é a própria tarefa. Caso contrário, o prompt contém tanto o
        contexto quanto a task.

        ``token_count`` é estimado como o número de palavras no prompt
        gerado.

    Example:
        >>> from tokemize.models import SummaryOutput
        >>> output = generate_prompt(SummaryOutput(), task="add tests")
        >>> output.prompt
        'add tests'
    """
    if not summary_output.summarized_content:
        return GeneratorOutput(
            prompt=task,
            token_count=0,
        )

    prompt = (
        f"Context:\n{summary_output.summarized_content}\n\nTask:\n{task}"
    )
    token_count = len(prompt.split())

    return GeneratorOutput(
        prompt=prompt,
        token_count=token_count,
    )
