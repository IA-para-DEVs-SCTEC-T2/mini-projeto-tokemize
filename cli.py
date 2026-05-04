"""Tokemize CLI — Ponto de entrada da aplicação.

Expõe o subcomando `analyze` que recebe um caminho de repositório e uma
descrição de tarefa, valida as entradas e orquestra o pipeline de cinco
etapas sequenciais.
"""

from pathlib import Path
from typing import Any, Callable

import typer

from tokemize.core.parser.repository_analyzer import analyze_repository
from tokemize.core.selector.intelligent_selector import select_relevant_files
from tokemize.core.optimizer.compressor import compress_context
from tokemize.core.optimizer.context_saver import save_context
from tokemize.core.context_cache import get_or_update_cache
from tokemize.integrations.llm.llm_dispatcher import dispatch

app = typer.Typer(
    name="tokemize",
    help="Otimização de contexto para LLMs.",
    add_completion=False,
)

STEP_NAMES = {
    "repository_analyzer": "Repository_Analyzer",
    "intelligent_selector": "Intelligent_Selector",
    "compressor": "Compressor",
    "context_saver": "Context_Saver",
    "context_cache": "Context_Cache",
    "llm_dispatcher": "LLM_Dispatcher",
}


def _validate_repo_path(repo_path: str) -> None:
    """Valida existência e tipo do caminho do repositório.

    Args:
        repo_path: Caminho fornecido pelo usuário.

    Raises:
        typer.Exit: Com código 1 em caso de caminho inválido.
    """
    path = Path(repo_path)
    if not path.exists():
        typer.echo(f"Erro: o caminho '{repo_path}' não existe.")
        raise typer.Exit(code=1)
    if not path.is_dir():
        typer.echo(f"Erro: '{repo_path}' não é um diretório válido.")
        raise typer.Exit(code=1)


def _validate_task_description(task_description: str) -> None:
    """Valida conteúdo e comprimento mínimo da descrição da tarefa.

    Args:
        task_description: Descrição fornecida pelo usuário.

    Raises:
        typer.Exit: Com código 1 em caso de descrição inválida.
    """
    stripped = task_description.strip()
    if not stripped:
        typer.echo("Erro: a descrição da tarefa não pode ser vazia.")
        raise typer.Exit(code=1)
    non_whitespace = len(stripped.replace(" ", "").replace("\t", "").replace("\n", ""))
    if non_whitespace < 10:
        typer.echo("Erro: a descrição da tarefa deve ter pelo menos 10 caracteres.")
        raise typer.Exit(code=1)


def _run_step(step_name: str, fn: Callable, *args: Any) -> Any:
    """Executa uma etapa do pipeline com tratamento de exceções padronizado.

    Args:
        step_name: Nome legível da etapa para mensagens de erro.
        fn: Função a ser executada.
        *args: Argumentos posicionais para a função.

    Returns:
        Resultado da função.

    Raises:
        typer.Exit: Com código 2 em caso de exceção.
    """
    try:
        return fn(*args)
    except Exception as exc:
        typer.echo(f"Erro na etapa '{step_name}': {exc}")
        raise typer.Exit(code=2)


@app.command()
def analyze(
    repo_path: str = typer.Argument(..., help="Caminho para o repositório a ser analisado"),
    task_description: str = typer.Argument(..., help="Descrição da tarefa técnica (mínimo 10 caracteres)"),
) -> None:
    """Analisa um repositório e envia uma requisição otimizada ao LLM."""
    _validate_repo_path(repo_path)
    _validate_task_description(task_description)

    typer.echo("[1/6] Analisando repositório...")
    structure = _run_step(STEP_NAMES["repository_analyzer"], analyze_repository, repo_path)
    typer.echo("[2/6] Selecionando arquivos relevantes...")
    context = _run_step(STEP_NAMES["intelligent_selector"], select_relevant_files, structure, task_description)
    typer.echo("[3/6] Comprimindo contexto...")
    compressed = _run_step(STEP_NAMES["compressor"], compress_context, context)
    typer.echo("[4/6] Salvando contexto...")
    saved = _run_step(STEP_NAMES["context_saver"], save_context, compressed)
    typer.echo("[5/6] Verificando cache...")
    cached = _run_step(STEP_NAMES["context_cache"], get_or_update_cache, saved, task_description)
    typer.echo("[6/6] Enviando ao LLM...")
    result = _run_step(STEP_NAMES["llm_dispatcher"], dispatch, cached)
    typer.echo("=== Resultado ===")
    typer.echo(result)


if __name__ == "__main__":
    app()
