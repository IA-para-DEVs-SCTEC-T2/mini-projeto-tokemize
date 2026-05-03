"""Stub funcional da etapa de geração de embeddings.

Este módulo implementa a função `generate_embeddings`, responsável por
gerar representações vetoriais dos arquivos analisados para permitir
busca por similaridade semântica na etapa de seleção.
"""

from __future__ import annotations

from tokemize.models import AnalysisOutput, EmbeddedFile, EmbeddingsOutput

# Vetor fictício usado pelo stub para todos os arquivos.
_STUB_EMBEDDING: list[float] = [0.1, 0.2, 0.3]


def generate_embeddings(analysis_output: AnalysisOutput) -> EmbeddingsOutput:
    """Gera vetores de embedding para cada arquivo analisado.

    Args:
        analysis_output: Resultado da etapa de análise contendo os arquivos
            enriquecidos com metadados estruturais.

    Returns:
        EmbeddingsOutput com um ``EmbeddedFile`` por arquivo em
        ``analysis_output.analyzed_files``. Se a lista estiver vazia,
        retorna ``EmbeddingsOutput(embedded_files=[], total_embedded=0,
        total_failed=0)``.

        Invariante garantida: ``total_embedded + total_failed ==
        len(embedded_files)``.

    Example:
        >>> from tokemize.models import AnalysisOutput
        >>> output = generate_embeddings(AnalysisOutput())
        >>> output.total_embedded + output.total_failed == len(output.embedded_files)
        True
    """
    if not analysis_output.analyzed_files:
        return EmbeddingsOutput(
            embedded_files=[],
            total_embedded=0,
            total_failed=0,
        )

    embedded: list[EmbeddedFile] = []
    for analyzed in analysis_output.analyzed_files:
        embedded.append(
            EmbeddedFile(
                path=analyzed.path,
                language=analyzed.language,
                content=analyzed.content,
                embedding=list(_STUB_EMBEDDING),
            )
        )

    total_embedded = sum(1 for f in embedded if f.embedding)
    total_failed = sum(1 for f in embedded if not f.embedding)

    return EmbeddingsOutput(
        embedded_files=embedded,
        total_embedded=total_embedded,
        total_failed=total_failed,
    )
