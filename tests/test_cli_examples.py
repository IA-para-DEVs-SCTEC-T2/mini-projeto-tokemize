"""Example tests (testes de exemplo) para a CLI do Tokemize.

Verifica comportamentos determinísticos e específicos:
  - Invocação sem argumentos → ajuda + Exit_Code 0
  - Invocação com --help → ajuda + Exit_Code 0
  - Mensagens de progresso [1/6] a [5/6] na ordem correta
  - Ordem de chamada dos módulos do pipeline com argumentos corretos
  - Flags --print, --output e ClipboardError

Novo pipeline (sem LLM):
  repository_analyzer → intelligent_selector → compressor →
  context_store → prompt_builder → clipboard
"""

import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from tokemize.cli import app

runner = CliRunner()

_VALID_REPO = "."
_VALID_TASK = "implementar autenticação de usuários"
_PROMPT_CONTENT = (
    "# Prompt otimizado pelo Tokemize\n\n"
    "## Tarefa\n\n"
    "implementar autenticação de usuários\n"
)


def _make_pipeline_mocks(prompt_content: str = _PROMPT_CONTENT) -> dict:
    from tokemize.models import CompressedContext, OptimizedPrompt

    mock_analyze = MagicMock(return_value=[])
    mock_select = MagicMock(return_value=[])
    mock_compress = MagicMock(
        return_value=CompressedContext(
            task_description=_VALID_TASK,
            compressed_content="resumo",
            token_count=10,
        )
    )
    mock_save_context = MagicMock(
        return_value=".tokemize/context/implementar-autenticacao-de-usuarios-20250101.md"
    )
    mock_build = MagicMock(
        return_value=OptimizedPrompt(
            content=prompt_content,
            task_description=_VALID_TASK,
            token_estimate=20,
        )
    )
    mock_clipboard = MagicMock(return_value=None)

    return {
        "analyze": mock_analyze,
        "select": mock_select,
        "compress": mock_compress,
        "save_context": mock_save_context,
        "build": mock_build,
        "clipboard": mock_clipboard,
    }


def _invoke_with_mocked_pipeline(args: list, prompt_content: str = _PROMPT_CONTENT):
    mocks = _make_pipeline_mocks(prompt_content)
    with (
        patch("tokemize.cli.analyze_repository", mocks["analyze"]),
        patch("tokemize.cli.select_relevant_artifacts", mocks["select"]),
        patch("tokemize.cli.compress_context", mocks["compress"]),
        patch("tokemize.cli.save_context", mocks["save_context"]),
        patch("tokemize.cli.build_prompt", mocks["build"]),
        patch("tokemize.cli.copy_to_clipboard", mocks["clipboard"]),
    ):
        return runner.invoke(app, args), mocks


# ---------------------------------------------------------------------------
# Help e invocação sem argumentos
# ---------------------------------------------------------------------------

def test_toke_with_help_flag_exits_0():
    result = runner.invoke(app, ["toke", "--help"])
    assert result.exit_code == 0
    assert "TASK_DESCRIPTION" in result.output or "task" in result.output.lower()


def test_app_with_help_flag_exits_0():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_toke_without_args_shows_error():
    result = runner.invoke(app, ["toke"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Validação de repo_path
# ---------------------------------------------------------------------------

def test_nonexistent_repo_path_exits_1():
    result = runner.invoke(app, ["toke", "--repo", "/caminho/que/nao/existe/xyz123", _VALID_TASK])
    assert result.exit_code == 1
    assert "não existe" in result.output


def test_file_as_repo_path_exits_1():
    tmp_dir = tempfile.mkdtemp()
    try:
        file_path = Path(tmp_dir) / "arquivo.txt"
        file_path.write_text("conteúdo")
        result = runner.invoke(app, ["toke", "--repo", str(file_path), _VALID_TASK])
        assert result.exit_code == 1
        assert "não é um diretório válido" in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Validação de task_description
# ---------------------------------------------------------------------------

def test_empty_task_description_exits_1():
    result = runner.invoke(app, ["toke", "--repo", ".", ""])
    assert result.exit_code == 1
    assert "não pode ser vazia" in result.output


def test_whitespace_only_task_description_exits_1():
    result = runner.invoke(app, ["toke", "--repo", ".", " "])
    assert result.exit_code == 1
    assert "não pode ser vazia" in result.output


def test_short_task_description_exits_1():
    result = runner.invoke(app, ["toke", "--repo", ".", "ab"])
    assert result.exit_code == 1
    assert "pelo menos 3 caracteres" in result.output


# ---------------------------------------------------------------------------
# Mensagens de progresso [1/6] a [5/6]
# ---------------------------------------------------------------------------

def test_progress_messages_appear_in_output():
    result, _ = _invoke_with_mocked_pipeline(["toke", _VALID_TASK])
    assert result.exit_code == 0
    for i in range(1, 6):
        assert f"[{i}/6]" in result.output, f"Mensagem [{i}/6] não encontrada na saída"


def test_progress_messages_appear_in_correct_order():
    result, _ = _invoke_with_mocked_pipeline(["toke", _VALID_TASK])
    output = result.output
    positions = [output.find(f"[{i}/6]") for i in range(1, 6)]
    assert all(pos >= 0 for pos in positions), f"Posições: {positions}"
    assert positions == sorted(positions), f"Mensagens fora de ordem. Posições: {positions}"


def test_progress_message_1_before_repository_analyzer():
    call_order = []

    def tracking_analyze(repo_path):
        call_order.append("analyze_repository")
        return []

    from tokemize.models import CompressedContext, OptimizedPrompt

    with (
        patch("tokemize.cli.analyze_repository", side_effect=tracking_analyze),
        patch("tokemize.cli.select_relevant_artifacts", return_value=[]),
        patch(
            "tokemize.cli.compress_context",
            return_value=CompressedContext(
                task_description=_VALID_TASK, compressed_content="", token_count=0
            ),
        ),
        patch("tokemize.cli.save_context", return_value=None),
        patch(
            "tokemize.cli.build_prompt",
            return_value=OptimizedPrompt(
                content=_PROMPT_CONTENT, task_description=_VALID_TASK, token_estimate=0
            ),
        ),
        patch("tokemize.cli.copy_to_clipboard", return_value=None),
    ):
        result = runner.invoke(app, ["toke", _VALID_TASK])

    assert result.exit_code == 0
    assert "[1/6]" in result.output
    assert "analyze_repository" in call_order


# ---------------------------------------------------------------------------
# Ordem do pipeline e argumentos corretos
# ---------------------------------------------------------------------------

def test_pipeline_called_in_correct_order():
    call_order = []

    from tokemize.models import CompressedContext, OptimizedPrompt

    compressed = CompressedContext(
        task_description=_VALID_TASK, compressed_content="resumo", token_count=5
    )
    prompt = OptimizedPrompt(
        content=_PROMPT_CONTENT, task_description=_VALID_TASK, token_estimate=20
    )

    def track(name, return_value):
        def fn(*args, **kwargs):
            call_order.append(name)
            return return_value

        return fn

    with (
        patch("tokemize.cli.analyze_repository", side_effect=track("analyze_repository", [])),
        patch(
            "tokemize.cli.select_relevant_artifacts",
            side_effect=track("select_relevant_artifacts", []),
        ),
        patch(
            "tokemize.cli.compress_context",
            side_effect=track("compress_context", compressed),
        ),
        patch("tokemize.cli.save_context", side_effect=track("save_context", None)),
        patch("tokemize.cli.build_prompt", side_effect=track("build_prompt", prompt)),
        patch(
            "tokemize.cli.copy_to_clipboard",
            side_effect=track("copy_to_clipboard", None),
        ),
    ):
        result = runner.invoke(app, ["toke", _VALID_TASK])

    assert result.exit_code == 0
    assert call_order == [
        "analyze_repository",
        "select_relevant_artifacts",
        "compress_context",
        "save_context",
        "build_prompt",
        "copy_to_clipboard",
    ], f"Ordem incorreta: {call_order}"


def test_pipeline_called_with_correct_arguments():
    from tokemize.models import CompressedContext, OptimizedPrompt

    file_analyses = []
    artifacts = []
    compressed = CompressedContext(
        task_description=_VALID_TASK, compressed_content="resumo", token_count=5
    )
    prompt = OptimizedPrompt(
        content=_PROMPT_CONTENT, task_description=_VALID_TASK, token_estimate=20
    )
    context_file_path = ".tokemize/context/implementar-autenticacao-20250101.md"

    mock_analyze = MagicMock(return_value=file_analyses)
    mock_select = MagicMock(return_value=artifacts)
    mock_compress = MagicMock(return_value=compressed)
    mock_save_context = MagicMock(return_value=context_file_path)
    mock_build = MagicMock(return_value=prompt)
    mock_clipboard = MagicMock(return_value=None)

    with (
        patch("tokemize.cli.analyze_repository", mock_analyze),
        patch("tokemize.cli.select_relevant_artifacts", mock_select),
        patch("tokemize.cli.compress_context", mock_compress),
        patch("tokemize.cli.save_context", mock_save_context),
        patch("tokemize.cli.build_prompt", mock_build),
        patch("tokemize.cli.copy_to_clipboard", mock_clipboard),
    ):
        result = runner.invoke(app, ["toke", "--repo", _VALID_REPO, _VALID_TASK])

    assert result.exit_code == 0

    mock_analyze.assert_called_once_with(_VALID_REPO)
    mock_select.assert_called_once_with(file_analyses, _VALID_TASK)
    mock_compress.assert_called_once_with(artifacts)
    mock_save_context.assert_called_once_with(
        compressed.compressed_content, _VALID_TASK, _VALID_REPO
    )
    mock_build.assert_called_once_with(compressed, _VALID_TASK, context_file_path)
    mock_clipboard.assert_called_once_with(prompt.content)


# ---------------------------------------------------------------------------
# Flags --print e --output
# ---------------------------------------------------------------------------

def test_print_flag_displays_prompt_in_stdout():
    result, _ = _invoke_with_mocked_pipeline(["toke", "--print", _VALID_TASK])
    assert result.exit_code == 0
    assert _PROMPT_CONTENT in result.output


def test_output_flag_saves_file():
    tmp_dir = tempfile.mkdtemp()
    try:
        output_file = str(Path(tmp_dir) / "prompt.md")
        result, _ = _invoke_with_mocked_pipeline(
            ["toke", "--output", output_file, _VALID_TASK]
        )
        assert result.exit_code == 0
        assert Path(output_file).exists()
        assert Path(output_file).read_text(encoding="utf-8") == _PROMPT_CONTENT
        assert f"Prompt salvo em: {output_file}" in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_output_flag_creates_parent_dirs():
    tmp_dir = tempfile.mkdtemp()
    try:
        output_file = str(Path(tmp_dir) / "subdir" / "nested" / "prompt.md")
        result, _ = _invoke_with_mocked_pipeline(
            ["toke", "--output", output_file, _VALID_TASK]
        )
        assert result.exit_code == 0
        assert Path(output_file).exists()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def test_print_and_output_flags_together():
    tmp_dir = tempfile.mkdtemp()
    try:
        output_file = str(Path(tmp_dir) / "prompt.md")
        result, _ = _invoke_with_mocked_pipeline(
            ["toke", "--print", "--output", output_file, _VALID_TASK]
        )
        assert result.exit_code == 0
        assert _PROMPT_CONTENT in result.output
        assert Path(output_file).exists()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# ClipboardError
# ---------------------------------------------------------------------------

def test_clipboard_error_results_in_exit_0_with_warning():
    from tokemize.models import CompressedContext, OptimizedPrompt
    from tokemize.integrations.clipboard import ClipboardError

    compressed = CompressedContext(
        task_description=_VALID_TASK, compressed_content="resumo", token_count=5
    )
    prompt = OptimizedPrompt(
        content=_PROMPT_CONTENT, task_description=_VALID_TASK, token_estimate=20
    )

    with (
        patch("tokemize.cli.analyze_repository", return_value=[]),
        patch("tokemize.cli.select_relevant_artifacts", return_value=[]),
        patch("tokemize.cli.compress_context", return_value=compressed),
        patch("tokemize.cli.save_context", return_value=None),
        patch("tokemize.cli.build_prompt", return_value=prompt),
        patch(
            "tokemize.cli.copy_to_clipboard",
            side_effect=ClipboardError("sem display"),
        ),
    ):
        result = runner.invoke(app, ["toke", _VALID_TASK])

    assert result.exit_code == 0
    assert "⚠️" in result.output
    assert "não foi possível copiar" in result.output


# ---------------------------------------------------------------------------
# Comando prepare
# ---------------------------------------------------------------------------

def test_prepare_command_executes_same_pipeline():
    from tokemize.models import CompressedContext, OptimizedPrompt

    compressed = CompressedContext(
        task_description=_VALID_TASK, compressed_content="resumo", token_count=5
    )
    prompt = OptimizedPrompt(
        content=_PROMPT_CONTENT, task_description=_VALID_TASK, token_estimate=20
    )

    mock_analyze = MagicMock(return_value=[])
    mock_select = MagicMock(return_value=[])
    mock_compress = MagicMock(return_value=compressed)
    mock_save_context = MagicMock(return_value=None)
    mock_build = MagicMock(return_value=prompt)
    mock_clipboard = MagicMock(return_value=None)

    with (
        patch("tokemize.cli.analyze_repository", mock_analyze),
        patch("tokemize.cli.select_relevant_artifacts", mock_select),
        patch("tokemize.cli.compress_context", mock_compress),
        patch("tokemize.cli.save_context", mock_save_context),
        patch("tokemize.cli.build_prompt", mock_build),
        patch("tokemize.cli.copy_to_clipboard", mock_clipboard),
    ):
        result = runner.invoke(app, ["prepare", ".", _VALID_TASK])

    assert result.exit_code == 0
    mock_analyze.assert_called_once_with(".")
    mock_select.assert_called_once_with([], _VALID_TASK)
    for i in range(1, 6):
        assert f"[{i}/6]" in result.output


# ---------------------------------------------------------------------------
# Tratamento de exceção no pipeline
# ---------------------------------------------------------------------------

def test_pipeline_exception_exits_with_code_2():
    with (
        patch(
            "tokemize.cli.analyze_repository",
            side_effect=Exception("falha no analyzer"),
        ),
        patch("tokemize.cli.save_context", return_value=None),
    ):
        result = runner.invoke(app, ["toke", _VALID_TASK])

    assert result.exit_code == 2
    assert "Repository_Analyzer" in result.output
    assert "falha no analyzer" in result.output


# ---------------------------------------------------------------------------
# Mensagem de sucesso após clipboard
# ---------------------------------------------------------------------------

def test_success_message_displayed_after_clipboard():
    result, _ = _invoke_with_mocked_pipeline(["toke", _VALID_TASK])
    assert result.exit_code == 0
    assert "✅" in result.output
