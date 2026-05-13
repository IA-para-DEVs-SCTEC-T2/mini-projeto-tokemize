"""Tokemize CLI — Ponto de entrada da aplicação.

<<<<<<< HEAD
Expõe os comandos ``toke`` e ``prepare`` que recebem um caminho de repositório
e uma descrição de tarefa, validam as entradas e orquestram o pipeline de seis
etapas sequenciais sem chamada a LLM.

Novo fluxo:
    repository_analyzer → intelligent_selector → compressor → context_store → prompt_builder → clipboard
"""

=======
Expõe os subcomandos ``toke`` e ``prepare`` que recebem um caminho de
repositório e uma descrição de tarefa, validam as entradas e orquestram
o pipeline de seis etapas sequenciais (sem LLM):

    repository_analyzer → intelligent_selector → compressor →
    context_store → prompt_builder → clipboard
"""

from __future__ import annotations

>>>>>>> 135f5f4 (feat(task005): teste task005)
from pathlib import Path
from typing import Any, Callable, Optional

import typer

from tokemize.core.parser.repository_analyzer import analyze_repository
<<<<<<< HEAD
from tokemize.core.selector.intelligent_selector import select_relevant_artifacts
from tokemize.core.optimizer.compressor import compress_context
from tokemize.core.context_store import save_context
from tokemize.core.prompt_builder import build_prompt
from tokemize.integrations.clipboard import copy_to_clipboard, ClipboardError

app = typer.Typer(name="tokemize", add_completion=False)
=======
from tokemize.core.selector.artifact_selector import select_relevant_artifacts
from tokemize.core.optimizer.compressor import compress_context
from tokemize.core.optimizer.context_saver import save_context
from tokemize.core.optimizer.prompt_builder import build_prompt
from tokemize.integrations.clipboard import ClipboardError, copy_to_clipboard

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
    "prompt_builder": "Prompt_Builder",
    "clipboard": "Clipboard",
}
>>>>>>> 135f5f4 (feat(task005): teste task005)


def _validate_repo_path(repo_path: str) -> None:
    """Valida existência e tipo do caminho do repositório.

    Args:
        repo_path: Caminho fornecido pelo usuário.

    Raises:
        typer.Exit: Com código 1 em caso de caminho inválido.
    """
<<<<<<< HEAD
    if not Path(repo_path).exists():
        typer.echo(f"Erro: o caminho '{repo_path}' não existe.", err=True)
        raise typer.Exit(1)
    if not Path(repo_path).is_dir():
        typer.echo(f"Erro: '{repo_path}' não é um diretório válido.", err=True)
        raise typer.Exit(1)
=======
    path = Path(repo_path)
    if not path.exists():
        typer.echo(f"Erro: o caminho '{repo_path}' não existe.")
        raise typer.Exit(code=1)
    if not path.is_dir():
        typer.echo(f"Erro: '{repo_path}' não é um diretório válido.")
        raise typer.Exit(code=1)
>>>>>>> 135f5f4 (feat(task005): teste task005)


def _validate_task_description(task_description: str) -> None:
    """Valida conteúdo e comprimento mínimo da descrição da tarefa.

    Args:
        task_description: Descrição fornecida pelo usuário.

    Raises:
        typer.Exit: Com código 1 em caso de descrição inválida.
    """
<<<<<<< HEAD
    if not task_description.strip():
        typer.echo("Erro: a descrição da tarefa não pode ser vazia.", err=True)
        raise typer.Exit(1)
    if len(task_description.strip()) < 3:
        typer.echo("Erro: a descrição da tarefa deve ter pelo menos 3 caracteres.", err=True)
        raise typer.Exit(1)
=======
    stripped = task_description.strip()
    if not stripped:
        typer.echo("Erro: a descrição da tarefa não pode ser vazia.")
        raise typer.Exit(code=1)
    non_whitespace = len("".join(stripped.split()))
    if non_whitespace < 3:
        typer.echo("Erro: a descrição da tarefa deve ter pelo menos 3 caracteres.")
        raise typer.Exit(code=1)
>>>>>>> 135f5f4 (feat(task005): teste task005)


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
<<<<<<< HEAD
    print_output: bool = False,
    output_path: Optional[str] = None,
) -> None:
    """Orquestra as 6 etapas do pipeline sem LLM.

    Etapas:
        1. Repository_Analyzer — analisa o repositório
        2. Intelligent_Selector — seleciona artefatos relevantes
        3. Compressor — compacta o contexto
        4. Context_Store — salva o contexto em .tokemize/context/ (não-fatal)
        5. Prompt_Builder — gera o prompt otimizado com referências ao arquivo
        6. Clipboard — copia para a área de transferência

    Args:
        repo_path: Caminho do repositório a ser analisado.
        task_description: Descrição da tarefa técnica.
        print_output: Se True, exibe o prompt no terminal.
        output_path: Caminho de arquivo para salvar o prompt (opcional).
    """
    typer.echo("[1/6] Analisando repositório atual...")
    file_analyses = _run_step("Repository_Analyzer", analyze_repository, repo_path)

    typer.echo("[2/6] Selecionando contexto relevante...")
    artifacts = _run_step(
        "Intelligent_Selector", select_relevant_artifacts, file_analyses, task_description
    )

    typer.echo("[3/6] Compactando contexto...")
    compressed_ctx = _run_step("Compressor", compress_context, artifacts)

    # Etapa 4: Context_Store — não-fatal, falhas exibem aviso e pipeline continua
    context_file_path: Optional[str] = None
    try:
        context_file_path = save_context(
            compressed_ctx.compressed_content,
            task_description,
            repo_path,
        )
        if context_file_path is not None:
            typer.echo(f"💾 Contexto salvo em: {context_file_path}")
        else:
            typer.echo("⚠️ Não foi possível salvar o contexto em .tokemize/: falha desconhecida")
    except Exception as exc:
        typer.echo(f"⚠️ Não foi possível salvar o contexto em .tokemize/: {exc}")

    typer.echo("[4/6] Gerando prompt otimizado...")
    prompt = _run_step(
        "Prompt_Builder", build_prompt, compressed_ctx, task_description, context_file_path
    )

    typer.echo("[5/6] Copiando para a área de transferência...")
    clipboard_ok = True
    try:
        copy_to_clipboard(prompt.content)
    except ClipboardError:
        clipboard_ok = False
        typer.echo(
            "⚠️ Prompt gerado, mas não foi possível copiar para a área de transferência.\n"
            "Use --print para exibir no terminal ou --output para salvar em arquivo."
        )

    if print_output:
        typer.echo(prompt.content)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt.content, encoding="utf-8")
        typer.echo(f"📄 Prompt salvo em: {output_path}")

    if clipboard_ok:
        typer.echo(
            "✅ Prompt otimizado gerado e copiado para a área de transferência. "
            "Cole agora no chatbot da sua IDE."
        )
    else:
        typer.echo("✅ Prompt otimizado gerado.")
=======
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
        typer.echo("✅ Prompt copiado para a área de transferência.")
    except ClipboardError as exc:
        typer.echo(f"⚠️  não foi possível copiar para o clipboard: {exc}")
>>>>>>> 135f5f4 (feat(task005): teste task005)


@app.command()
def toke(
<<<<<<< HEAD
    task_description: str = typer.Argument(..., help="Descrição da tarefa técnica. Ex: 'corrija o login'"),
    repo: str = typer.Option(".", "--repo", "-r", help="Caminho do repositório. Por padrão, usa o diretório atual."),
    print_output: bool = typer.Option(False, "--print", help="Exibe o prompt gerado no terminal."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Salva o prompt gerado em um arquivo Markdown."),
) -> None:
    """Analisa o repositório atual e gera um prompt otimizado para chatbots de IDE."""
    _validate_repo_path(repo)
    _validate_task_description(task_description)
    _run_pipeline(repo, task_description, print_output, output)
=======
    task_description: str = typer.Argument(
        ..., help="Descrição da tarefa técnica (mínimo 3 caracteres)"
    ),
    repo: str = typer.Option(
        ".", "--repo", "-r", help="Caminho para o repositório a ser analisado"
    ),
    print_prompt: bool = typer.Option(
        False, "--print", "-p", help="Imprime o prompt gerado no stdout"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Salva o prompt em um arquivo"
    ),
) -> None:
    """Gera um prompt otimizado a partir do repositório e copia para o clipboard."""
    _run_pipeline(repo, task_description, print_prompt=print_prompt, output_file=output)
>>>>>>> 135f5f4 (feat(task005): teste task005)


@app.command()
def prepare(
<<<<<<< HEAD
    repo_path: str = typer.Argument(..., help="Caminho do repositório a ser analisado."),
    task_description: str = typer.Argument(..., help="Descrição da tarefa técnica."),
    print_output: bool = typer.Option(False, "--print", help="Exibe o prompt gerado no terminal."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Salva o prompt gerado em um arquivo Markdown."),
) -> None:
    """Analisa um repositório específico e gera um prompt otimizado para chatbots de IDE."""
    _validate_repo_path(repo_path)
    _validate_task_description(task_description)
    _run_pipeline(repo_path, task_description, print_output, output)
=======
    repo_path: str = typer.Argument(..., help="Caminho para o repositório"),
    task_description: str = typer.Argument(
        ..., help="Descrição da tarefa técnica (mínimo 3 caracteres)"
    ),
    print_prompt: bool = typer.Option(
        False, "--print", "-p", help="Imprime o prompt gerado no stdout"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Salva o prompt em um arquivo"
    ),
) -> None:
    """Alias posicional para ``toke``: prepare <repo_path> <task_description>."""
    _run_pipeline(
        repo_path, task_description, print_prompt=print_prompt, output_file=output
    )
>>>>>>> 135f5f4 (feat(task005): teste task005)


if __name__ == "__main__":
    app()
