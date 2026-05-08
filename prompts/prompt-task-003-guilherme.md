# Tarefa: Guilherme — Compressor + Prompt Builder + Context Store

## Contexto

Você está trabalhando no projeto **Tokemize**, uma ferramenta CLI em Python 3.11+ que analisa repositórios locais e gera prompts otimizados para chatbots de IDE.

O pipeline principal é:
```
repository_analyzer → intelligent_selector → compressor → context_store → prompt_builder → clipboard
```

Os modelos `CompressedContext`, `OptimizedPrompt` e `Artifact` já foram criados por outro membro da equipe em `src/tokemize/models/`.

## Sua responsabilidade

Você é responsável por **três módulos do core**:
1. `src/tokemize/core/optimizer/compressor.py` — reimplementar (era stub)
2. `src/tokemize/core/prompt_builder.py` — criar novo
3. `src/tokemize/core/context_store.py` — criar novo

---

## 1. `src/tokemize/core/optimizer/compressor.py`

Substitua o conteúdo atual pelo seguinte:

```python
"""Compressão de contexto do pipeline Tokemize."""

from tokemize.models import CompressedContext
from tokemize.models.artifact import Artifact


def compress_context(artifacts: list[Artifact]) -> CompressedContext:
    """Comprime a lista de artefatos em um contexto compacto em Markdown.

    Agrupa os artefatos por arquivo e gera um bloco Markdown estruturado
    com caminho, linguagem, tipo, nome e linhas de cada artefato.

    Args:
        artifacts: Lista de artefatos selecionados pelo Intelligent_Selector.

    Returns:
        CompressedContext com conteúdo Markdown compacto, contagem de tokens
        e contagem de artefatos. Se a lista for vazia, retorna um contexto
        com mensagem de fallback e contagens zeradas.
    """
    if not artifacts:
        return CompressedContext(
            task_description="",
            compressed_content="Nenhum artefato relevante encontrado.",
            token_count=0,
            artifact_count=0,
        )

    # Agrupar artefatos por file_path preservando ordem de inserção
    groups: dict[str, list[Artifact]] = {}
    for artifact in artifacts:
        groups.setdefault(artifact.file_path, []).append(artifact)

    # Gerar blocos Markdown por grupo
    blocks: list[str] = []
    for file_path, artifacts_in_file in groups.items():
        language = artifacts_in_file[0].language
        block = f"### {file_path} ({language})\n"
        for artifact in artifacts_in_file:
            block += (
                f"- [{artifact.type}] {artifact.name} "
                f"(linhas {artifact.start_line}–{artifact.end_line})\n"
            )
        blocks.append(block)

    compressed_content = "".join(blocks)
    token_count = len(compressed_content.split())
    artifact_count = len(artifacts)

    return CompressedContext(
        task_description="",
        compressed_content=compressed_content,
        token_count=token_count,
        artifact_count=artifact_count,
    )
```

---

## 2. `src/tokemize/core/prompt_builder.py` — arquivo novo

Crie este arquivo:

```python
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
```

---

## 3. `src/tokemize/core/context_store.py` — arquivo novo

Crie este arquivo:

```python
"""Módulo responsável por persistir o contexto compacto em disco.

Salva o compressed_content gerado pelo Compressor em
.tokemize/context/<slug>-<YYYYMMDD>.md dentro do repositório analisado.
O salvamento é não-fatal: qualquer falha de I/O é capturada internamente e
sinalizada pelo retorno None, sem interromper o pipeline.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path


def _generate_slug(task_description: str) -> str:
    """Gera um slug normalizado a partir da task_description.

    Aplica, nesta ordem:
    1. Normalização Unicode NFD para decompor acentos.
    2. Remoção de caracteres da categoria "Mn" (marcas de combinação/acentos).
    3. Conversão para lowercase.
    4. Substituição de espaços e separadores por hífens.
    5. Remoção de caracteres não alfanuméricos (exceto hífens).
    6. Colapso de hífens consecutivos em um único hífen.
    7. Remoção de hífens no início e no fim.
    8. Truncamento em 40 caracteres.

    Args:
        task_description: Descrição da tarefa fornecida pelo usuário.

    Returns:
        Slug normalizado com no máximo 40 caracteres, contendo apenas
        [a-z0-9-], sem hífens consecutivos, sem hífens nas extremidades.
    """
    nfd = unicodedata.normalize("NFD", task_description)
    without_accents = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    lowered = without_accents.lower()
    with_hyphens = re.sub(r"[ _\-/\.]+", "-", lowered)
    only_alnum_hyphen = re.sub(r"[^a-z0-9\-]", "", with_hyphens)
    collapsed = re.sub(r"-{2,}", "-", only_alnum_hyphen)
    stripped = collapsed.strip("-")
    return stripped[:40]


def save_context(
    compressed_content: str,
    task_description: str,
    repo_path: str,
) -> str | None:
    """Salva o contexto compacto em .tokemize/context/ dentro do repo_path.

    Cria o diretório .tokemize/context/ se não existir, gera o nome do
    arquivo a partir do slug da task_description e da data atual, e salva
    o compressed_content com encoding UTF-8.

    Args:
        compressed_content: Conteúdo compacto gerado pelo Compressor.
        task_description: Descrição da tarefa, usada para gerar o slug.
        repo_path: Caminho do repositório (já validado pelo CLI).

    Returns:
        Caminho relativo ao repo_path do arquivo salvo (ex:
        ".tokemize/context/corrigir-login-20250115.md"), ou None se
        qualquer erro de I/O ocorrer.
    """
    try:
        slug = _generate_slug(task_description)
        date = datetime.now().strftime("%Y%m%d")
        filename = f"{slug}-{date}.md"
        context_dir = Path(repo_path) / ".tokemize" / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        (context_dir / filename).write_text(compressed_content, encoding="utf-8")
        return f".tokemize/context/{filename}"
    except OSError:
        return None
```

---

## Verificação

Após implementar, rode:

```bash
python -c "
from tokemize.core.optimizer.compressor import compress_context
from tokemize.core.prompt_builder import build_prompt
from tokemize.core.context_store import save_context, _generate_slug
print(_generate_slug('corrija o login'))
print('imports OK')
"
```

Deve imprimir `corrija-o-login` e `imports OK`.
