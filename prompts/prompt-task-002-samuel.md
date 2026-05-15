# Tarefa: Samuel — Repository Analyzer + Intelligent Selector

## Contexto

Você está trabalhando no projeto **Tokemize**, uma ferramenta CLI em Python 3.11+ que analisa repositórios locais e gera prompts otimizados para chatbots de IDE.

O pipeline principal é:
```
repository_analyzer → intelligent_selector → compressor → context_store → prompt_builder → clipboard
```

O projeto usa Tree-sitter para análise sintática de código. Os módulos `RepositoryScanner`, `TreeSitterAnalyzer` e `UnsupportedLanguageError` já existem em `src/tokemize/core/parser/`.

Os modelos `FileAnalysis` e `Artifact` já foram criados por outro membro da equipe em `src/tokemize/models/`.

## Sua responsabilidade

Você é responsável por **reimplementar** dois módulos que atualmente são stubs:
1. `src/tokemize/core/parser/repository_analyzer.py`
2. `src/tokemize/core/selector/intelligent_selector.py`

---

## 1. `src/tokemize/core/parser/repository_analyzer.py`

Substitua o conteúdo atual pelo seguinte:

```python
"""Análise de repositório do pipeline Tokemize.

Orquestra o RepositoryScanner e o TreeSitterAnalyzer para varrer um
repositório local e extrair artefatos sintáticos de cada arquivo de
código-fonte suportado.
"""

from __future__ import annotations

from pathlib import Path

from tokemize.core.parser.scanner import DEFAULT_IGNORE_DIRS, RepositoryScanner
from tokemize.core.parser.tree_sitter_analyzer import (
    TreeSitterAnalyzer,
    UnsupportedLanguageError,
)
from tokemize.models.artifact import Artifact
from tokemize.models.file_analysis import FileAnalysis


def analyze_repository(repo_path: str) -> list[FileAnalysis]:
    """Analisa a estrutura de um repositório local e extrai artefatos sintáticos.

    Varre recursivamente o diretório ``repo_path`` usando o
    RepositoryScanner, ignorando diretórios como ``.git``, ``node_modules``,
    ``__pycache__``, ``.venv`` e ``dist``. Para cada arquivo encontrado,
    tenta extrair artefatos (funções, classes, métodos e imports) via
    TreeSitterAnalyzer.

    Arquivos com linguagem não suportada pelo Tree-sitter recebem
    ``language="unknown"`` e ``artifacts=[]`` — nenhuma exceção é propagada
    para arquivos individuais.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório
            a ser analisado.

    Returns:
        Lista de FileAnalysis, uma entrada por arquivo de código-fonte
        encontrado. Arquivos com linguagem não suportada são incluídos
        com ``artifacts=[]``.

    Example:
        >>> analyses = analyze_repository(".")
        >>> for fa in analyses:
        ...     print(fa.relative_path, fa.language, len(fa.artifacts))
    """
    scanner = RepositoryScanner(ignore_dirs=set(DEFAULT_IGNORE_DIRS))
    analyzer = TreeSitterAnalyzer()

    scan_result = scanner.scan(Path(repo_path))

    file_analyses: list[FileAnalysis] = []

    for file_meta in scan_result.files:
        try:
            artifacts: list[Artifact] = analyzer.analyze(file_meta.path)
            language: str = file_meta.language
        except UnsupportedLanguageError:
            artifacts = []
            language = "unknown"

        file_analyses.append(
            FileAnalysis(
                relative_path=str(file_meta.relative_path),
                language=language,
                artifacts=artifacts,
                line_count=file_meta.line_count,
                size_bytes=file_meta.size_bytes,
            )
        )

    return file_analyses
```

---

## 2. `src/tokemize/core/selector/intelligent_selector.py`

Substitua o conteúdo atual pelo seguinte:

```python
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
```

---

## Verificação

Após implementar, rode:

```bash
python -c "
from tokemize.core.parser.repository_analyzer import analyze_repository
from tokemize.core.selector.intelligent_selector import select_relevant_artifacts
print('imports OK')
"
```

Deve imprimir `imports OK` sem erros.
