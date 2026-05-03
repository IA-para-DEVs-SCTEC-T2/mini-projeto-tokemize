"""Stub funcional da etapa de formatação do resultado final.

Este módulo implementa a função `format_result`, responsável por formatar
e estruturar o output do gerador em um ``PipelineResult`` pronto para
retorno à CLI.
"""

from __future__ import annotations

from tokemize.models import GeneratorOutput, PipelineResult


def format_result(generator_output: GeneratorOutput) -> PipelineResult:
    """Formata o output do gerador em um PipelineResult estruturado.

    Nunca lança exceção para nenhum input, incluindo ``prompt=""``.

    Args:
        generator_output: Resultado da etapa de geração contendo o prompt
            final e a estimativa de tokens.

    Returns:
        PipelineResult com ``success=True``, ``prompt`` igual a
        ``generator_output.prompt``, ``failed_stage=None`` e
        ``error_message=None``.

    Example:
        >>> from tokemize.models import GeneratorOutput
        >>> result = format_result(GeneratorOutput(prompt="hello"))
        >>> result.success
        True
        >>> result.failed_stage is None
        True
    """
    return PipelineResult(
        success=True,
        prompt=generator_output.prompt,
        failed_stage=None,
        error_message=None,
    )
