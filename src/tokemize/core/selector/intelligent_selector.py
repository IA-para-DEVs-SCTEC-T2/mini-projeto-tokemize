"""Seleção inteligente de artefatos por heurística de palavras-chave."""

import re
import unicodedata

from tokemize.models import RepositoryStructure, SelectedContext
from tokemize.models.artifact import Artifact
from tokemize.models.file_analysis import FileAnalysis


def _tokenize(text: str) -> list[str]:
    """Normaliza e tokeniza um texto em palavras-chave.

    Realiza as seguintes transformações em ordem:
    1. Normaliza acentos via NFKD e descarta bytes não-ASCII.
    2. Converte para minúsculas.
    3. Divide por separadores: ``_``, ``-``, ``/``, ``.`` e espaço.
    4. Filtra tokens com comprimento menor que 2.

    Args:
        text: Texto de entrada a ser tokenizado.

    Returns:
        Lista de tokens normalizados com comprimento >= 2.
    """
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    lowered = normalized.lower()
    raw_tokens = re.split(r"[_\-/\.\s]+", lowered)
    return [t for t in raw_tokens if len(t) >= 2]


def _score_artifact(artifact: Artifact, tokens: list[str]) -> int:
    """Calcula a pontuação de relevância de um artefato para um conjunto de tokens.

    Para cada token aplica as seguintes regras de pontuação:
    * ``+3`` se o token está em ``artifact.name.lower()``.
    * ``+2`` se o token está em ``artifact.file_path.lower()``.
    * ``+1`` se o token está nas primeiras 200 caracteres de
      ``artifact.content.lower()``.

    Args:
        artifact: Artefato a ser avaliado.
        tokens: Lista de tokens normalizados extraídos da descrição da tarefa.

    Returns:
        Score total de relevância (inteiro >= 0).
    """
    score = 0
    name_lower = artifact.name.lower()
    path_lower = artifact.file_path.lower()
    content_preview = artifact.content.lower()[:200]

    for token in tokens:
        if token in name_lower:
            score += 3
        if token in path_lower:
            score += 2
        if token in content_preview:
            score += 1

    return score


def select_relevant_artifacts(
    file_analyses: list[FileAnalysis],
    task_description: str,
    top_n: int = 5,
) -> list[Artifact]:
    """Seleciona os artefatos mais relevantes para a tarefa fornecida.

    Executa a seleção em três fases:
    1. Tokenização — tokeniza ``task_description`` com _tokenize.
    2. Scoring — calcula o score de cada artefato com _score_artifact.
    3. Seleção — ordena por score decrescente (sort estável para
       determinismo em empates) e retorna os ``top_n`` artefatos com
       ``score > 0``. Se todos os scores forem zero, aplica fallback
       retornando os ``top_n`` artefatos dos arquivos com maior número
       de artefatos.

    Args:
        file_analyses: Lista de análises de arquivos produzida pelo
            Repository_Analyzer.
        task_description: Descrição da tarefa técnica fornecida pelo usuário.
        top_n: Número máximo de artefatos a retornar. Padrão: 5.

    Returns:
        Lista de artefatos ordenados por relevância decrescente, com no
        máximo ``top_n`` elementos. Retorna lista vazia se não houver
        artefatos em ``file_analyses``.
    """
    tokens = _tokenize(task_description)

    scored: list[tuple[Artifact, int]] = []
    for file_analysis in file_analyses:
        for artifact in file_analysis.artifacts:
            score = _score_artifact(artifact, tokens)
            scored.append((artifact, score))

    if not scored:
        return []

    scored_sorted = sorted(scored, key=lambda x: x[1], reverse=True)
    max_score = scored_sorted[0][1]

    if max_score > 0:
        relevant = [artifact for artifact, score in scored_sorted if score > 0]
        return relevant[:top_n]

    # Fallback: retorna artefatos dos arquivos com maior número de artefatos
    files_by_count = sorted(
        file_analyses,
        key=lambda fa: len(fa.artifacts),
        reverse=True,
    )
    fallback: list[Artifact] = []
    for file_analysis in files_by_count:
        for artifact in file_analysis.artifacts:
            fallback.append(artifact)
            if len(fallback) >= top_n:
                return fallback

    return fallback


def select_relevant_files(
    structure: RepositoryStructure,
    task_description: str,
) -> SelectedContext:
    """Alias de compatibilidade com a CLI anterior.

    Args:
        structure: Estrutura mapeada do repositório pelo Repository_Analyzer.
        task_description: Descrição da tarefa técnica a ser realizada.

    Returns:
        SelectedContext contendo a descrição da tarefa.
    """
    return SelectedContext(task_description=task_description)
