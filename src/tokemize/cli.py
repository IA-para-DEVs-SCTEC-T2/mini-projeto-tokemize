"""Tokemize CLI — Ponto de entrada da aplicação.

Expõe os subcomandos ``toke`` e ``prepare`` que recebem um caminho de
repositório e uma descrição de tarefa, validam as entradas e orquestram
o pipeline de seis etapas sequenciais (sem LLM):

    repository_analyzer -> intelligent_selector -> compressor ->
    context_store -> prompt_builder -> clipboard
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

import typer

from tokemize.core.parser.repository_analyzer import analyze_repository
from tokemize.core.selector.artifact_selector import select_relevant_artifacts
from tokemize.core.optimizer.compressor import compress_context
from tokemize.core.optimizer.context_saver import save_context
from tokemize.core.optimizer.prompt_builder import build_prompt
from tokemize.integrations.clipboard import ClipboardError, copy_to_clipboard

app = typer.Typer(
    name="tokemize",
    help="Otimização de contexto para desenvolvimento de software.",
    add_completion=False,
)

STEP_NAMES = {
    "repository_analyzer": "Repository_Analyzer",
    "intelligent_selector": "Intelligent_Selector",
    "compressor": "Compressor",
    "context_saver": "Context_Saver",
    "prompt_builder": "Prompt_Builder",
    "clipboard": "Clipboard",
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
    non_whitespace = len("".join(stripped.split()))
    if non_whitespace < 3:
        typer.echo("Erro: a descrição da tarefa deve ter pelo menos 3 caracteres.")
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


def _run_pipeline(
    repo_path: str,
    task_description: str,
    print_prompt: bool = False,
    output_file: Optional[str] = None,
) -> None:
    """Orquestra o pipeline de 6 etapas e lida com saída e clipboard.

    Args:
        repo_path: Caminho para o repositório a ser analisado.
        task_description: Descrição da tarefa técnica.
        print_prompt: Se ``True``, imprime o prompt gerado no stdout.
        output_file: Caminho opcional para salvar o prompt em disco.
    """
    _validate_repo_path(repo_path)
    _validate_task_description(task_description)

    typer.echo("[1/6] Analisando repositório...")
    file_analyses = _run_step(
        STEP_NAMES["repository_analyzer"], analyze_repository, repo_path
    )

    typer.echo("[2/6] Selecionando artefatos relevantes...")
    artifacts = _run_step(
        STEP_NAMES["intelligent_selector"],
        select_relevant_artifacts,
        file_analyses,
        task_description,
    )

    typer.echo("[3/6] Comprimindo contexto...")
    compressed = _run_step(STEP_NAMES["compressor"], compress_context, artifacts)

    typer.echo("[4/6] Salvando contexto...")
    context_file_path = _run_step(
        STEP_NAMES["context_saver"],
        save_context,
        compressed.compressed_content,
        task_description,
        repo_path,
    )

    typer.echo("[5/6] Construindo prompt...")
    prompt = _run_step(
        STEP_NAMES["prompt_builder"],
        build_prompt,
        compressed,
        task_description,
        context_file_path,
    )

    # Salva em arquivo se --output foi fornecido
    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt.content, encoding="utf-8")
        typer.echo(f"Prompt salvo em: {output_file}")

    # Imprime no stdout se --print foi fornecido
    if print_prompt:
        typer.echo(prompt.content)

    typer.echo("[6/6] Copiando para clipboard...")
    try:
        copy_to_clipboard(prompt.content)
        typer.echo("Prompt copiado para a area de transferencia.")
    except ClipboardError as exc:
        typer.echo(f"Nao foi possivel copiar para o clipboard: {exc}")


@app.command()
def toke(
    task_description: str = typer.Argument(
        ..., help="Descricao da tarefa tecnica (minimo 3 caracteres)"
    ),
    repo: str = typer.Option(
        ".", "--repo", "-r", help="Caminho para o repositorio a ser analisado"
    ),
    print_prompt: bool = typer.Option(
        False, "--print", "-p", help="Imprime o prompt gerado no stdout"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Salva o prompt em um arquivo"
    ),
) -> None:
    """Gera um prompt otimizado a partir do repositorio e copia para o clipboard."""
    _run_pipeline(repo, task_description, print_prompt=print_prompt, output_file=output)


@app.command()
def prepare(
    repo_path: str = typer.Argument(..., help="Caminho para o repositorio"),
    task_description: str = typer.Argument(
        ..., help="Descricao da tarefa tecnica (minimo 3 caracteres)"
    ),
    print_prompt: bool = typer.Option(
        False, "--print", "-p", help="Imprime o prompt gerado no stdout"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Salva o prompt em um arquivo"
    ),
) -> None:
    """Alias posicional para toke: prepare <repo_path> <task_description>."""
    _run_pipeline(
        repo_path, task_description, print_prompt=print_prompt, output_file=output
    )


if __name__ == "__main__":
    app()
