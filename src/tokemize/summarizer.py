"""Sumarização de arquivos selecionados para o pipeline Tokemize."""

from __future__ import annotations

from tokemize.models import SelectionOutput, SummaryOutput


def summarize_selected(selection_output: SelectionOutput) -> SummaryOutput:
    """Resume o conteúdo dos arquivos selecionados em um bloco compacto.

    Concatena os caminhos dos arquivos selecionados como conteúdo resumido.

    Args:
        selection_output: Resultado da etapa de seleção contendo os
            arquivos relevantes com seus scores de relevância.

    Returns:
        SummaryOutput com ``summarized_content`` não-vazio quando há
        arquivos selecionados. Se ``selection_output.selected_files``
        estiver vazio, retorna ``SummaryOutput(summarized_content="",
        token_count=0, files_summarized=0)``.

    Example:
        >>> from tokemize.models import SelectionOutput
        >>> output = summarize_selected(SelectionOutput())
        >>> output.summarized_content
        ''
    """
    if not selection_output.selected_files:
        return SummaryOutput(
            summarized_content="",
            token_count=0,
            files_summarized=0,
        )

    summarized_content = "\n".join(f.path for f in selection_output.selected_files)
    token_count = len(summarized_content.split())
    files_summarized = len(selection_output.selected_files)

    return SummaryOutput(
        summarized_content=summarized_content,
        token_count=token_count,
        files_summarized=files_summarized,
    )
