"""Entrypoint raiz compatível da CLI do Tokemize.

O console script oficial usa ``tokemize.cli:app``. Este módulo mantém a
interface posicional legada ``cli.py <repo_path> <task_description>`` usada por
testes e integrações antigas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import typer

from tokemize.core.context_cache import get_or_update_cache
from tokemize.core.optimizer.compressor import compress_context
from tokemize.core.optimizer.context_saver import save_context_model as save_context
from tokemize.core.parser.repository_analyzer import analyze_repository
from tokemize.core.selector.intelligent_selector import select_relevant_files

app = typer.Typer(
    name="tokemize",
    help="Otimização de contexto para desenvolvimento de software.",
    add_completion=False,
)

STEP_NAMES = {
    "analyze_repository": "Repository_Analyzer",
    "select_relevant_files": "Intelligent_Selector",
    "compress_context": "Compressor",
    "save_context": "Context_Saver",
    "get_or_update_cache": "Context_Cache",
    "dispatch": "LLM_Dispatcher",
}


def dispatch(content: str) -> str:
    """Compatibilidade legada para a etapa de despacho LLM."""
    return content


def _validate_repo_path(repo_path: str) -> None:
    path = Path(repo_path)
    if not path.exists():
        typer.echo(f"Erro: o caminho '{repo_path}' não existe.")
        raise typer.Exit(code=1)
    if not path.is_dir():
        typer.echo(f"Erro: '{repo_path}' não é um diretório válido.")
        raise typer.Exit(code=1)


def _validate_task_description(task_description: str) -> None:
    stripped = task_description.strip()
    if not stripped:
        typer.echo("Erro: a descrição da tarefa não pode ser vazia.")
        raise typer.Exit(code=1)
    if len("".join(stripped.split())) < 10:
        typer.echo("Erro: a descrição da tarefa deve ter pelo menos 10 caracteres.")
        raise typer.Exit(code=1)


def _run_step(step_name: str, fn: Callable[..., Any], *args: Any) -> Any:
    try:
        return fn(*args)
    except Exception as exc:
        typer.echo(f"Erro na etapa '{step_name}': {exc}")
        raise typer.Exit(code=2)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    repo_path: str = typer.Argument(..., help="Caminho para o repositório"),
    task_description: str = typer.Argument(..., help="Descrição da tarefa técnica"),
) -> None:
    """Executa o pipeline legado posicional."""
    if ctx.invoked_subcommand is not None:
        return

    _validate_repo_path(repo_path)
    _validate_task_description(task_description)

    structure = _run_step(
        STEP_NAMES["analyze_repository"], analyze_repository, repo_path
    )
    selected = _run_step(
        STEP_NAMES["select_relevant_files"],
        select_relevant_files,
        structure,
        task_description,
    )
    compressed = _run_step(STEP_NAMES["compress_context"], compress_context, selected)
    saved = _run_step(STEP_NAMES["save_context"], save_context, compressed)
    cached = _run_step(
        STEP_NAMES["get_or_update_cache"],
        get_or_update_cache,
        saved,
        task_description,
    )
    result = _run_step(STEP_NAMES["dispatch"], dispatch, cached.content)

    typer.echo("=== Resultado ===")
    typer.echo(result)


if __name__ == "__main__":
    app()
