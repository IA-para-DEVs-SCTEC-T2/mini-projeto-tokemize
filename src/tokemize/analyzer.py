"""Stub funcional da etapa de análise estrutural dos arquivos.

Este módulo implementa a função `analyze_files`, responsável por enriquecer
cada arquivo varrido com metadados estruturais como tipo, contagem de
artefatos e score de relevância potencial.
"""

from __future__ import annotations

from tokemize.models import AnalyzedFile, AnalysisOutput, ScanOutput


def analyze_files(scan_output: ScanOutput) -> AnalysisOutput:
    """Analisa os arquivos encontrados pelo scanner e enriquece seus metadados.

    Args:
        scan_output: Resultado da etapa de varredura contendo a lista de
            arquivos a serem analisados.

    Returns:
        AnalysisOutput com um ``AnalyzedFile`` por arquivo em
        ``scan_output.files``. Se ``scan_output.files`` estiver vazio,
        retorna ``AnalysisOutput(analyzed_files=[], total_analyzed=0,
        total_skipped=0)``.

    Example:
        >>> from tokemize.models import ScanOutput
        >>> output = analyze_files(ScanOutput(repo_path=".", files=[]))
        >>> output.total_analyzed
        0
    """
    if not scan_output.files:
        return AnalysisOutput(
            analyzed_files=[],
            total_analyzed=0,
            total_skipped=0,
        )

    analyzed: list[AnalyzedFile] = []
    for scanned in scan_output.files:
        analyzed.append(
            AnalyzedFile(
                path=scanned.path,
                language=scanned.language,
                size_bytes=scanned.size_bytes,
                line_count=scanned.line_count,
                file_type="source",
                artifact_count=1,
                content="# stub content",
                relevance_hint=0.5,
            )
        )

    return AnalysisOutput(
        analyzed_files=analyzed,
        total_analyzed=len(analyzed),
        total_skipped=0,
    )
