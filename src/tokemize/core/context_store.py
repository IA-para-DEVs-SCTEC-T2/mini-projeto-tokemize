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
        slug = _generate_slug(task_description) or "context"
        date = datetime.now().strftime("%Y%m%d")
        filename = f"{slug}-{date}.md"
        context_dir = Path(repo_path) / ".tokemize" / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        (context_dir / filename).write_text(compressed_content, encoding="utf-8")
        return f".tokemize/context/{filename}"
    except OSError:
        return None
