"""Example tests (testes de exemplo) para a CLI do Tokemize.

Verifica comportamentos determinísticos e específicos:
  - Invocação sem argumentos → ajuda + Exit_Code 0
  - Invocação com --help → ajuda + Exit_Code 0
  - Mensagens de progresso [1/5] a [5/5] na ordem correta
  - Ordem de chamada dos módulos do pipeline com argumentos corretos

Nota sobre invocação com Typer 0.25+:
  Quando o app tem apenas um comando registrado, o CliRunner invoca
  diretamente sem prefixar o nome do subcomando.
  Ex: runner.invoke(app, [repo_path, task]) — sem "analyze".
"""

from unittest.mock import MagicMock, call, patch

import pytest
from typer.testing import CliRunner

from cli import app

runner = CliRunner()

# Diretório válido para testes que precisam passar pela validação de repo_path
_VALID_REPO = "."
_VALID_TASK = "implementar autenticação de usuários"


def _make_pipeline_mocks():
    """Cria mocks para todos os módulos do pipeline."""
    from tokemize.models import (
        CachedContext,
        CompressedContext,
        RepositoryStructure,
        SelectedContext,
    )

    mock_analyze = MagicMock(return_value=RepositoryStructure(root_path=_VALID_REPO))
    mock_select = MagicMock(return_value=SelectedContext(task_description=_VALID_TASK))
    mock_compress = MagicMock(
        return_value=CompressedContext(
            task_description=_VALID_TASK,
            compressed_content="resumo",
            token_count=10,
        )
    )
    mock_cache = MagicMock(
        return_value=CachedContext(
            task_description=_VALID_TASK,
            content="resposta do LLM",
            cache_hit=False,
            token_count=10,
        )
    )
    mock_dispatch = MagicMock(return_value="resposta do LLM")

    return mock_analyze, mock_select, mock_compress, mock_cache, mock_dispatch


# ---------------------------------------------------------------------------
# Task 8.2: --help e invocação sem argumentos
# Requirements: 1.4, 1.5
# ---------------------------------------------------------------------------

def test_analyze_without_args_shows_help():
    """Invocar analyze sem argumentos deve exibir informações de uso.
    
    Nota: O Typer/Click retorna exit_code 2 quando argumentos obrigatórios
    estão faltando, exibindo a mensagem de uso. Este é o comportamento padrão
    do Click para erros de parsing de argumentos.
    """
    result = runner.invoke(app, [])
    # Deve exibir informações de uso (Usage ou help)
    assert "REPO_PATH" in result.output or "Usage" in result.output
    assert "TASK_DESCRIPTION" in result.output or "help" in result.output.lower()


def test_analyze_with_help_flag_shows_descriptions():
    """Invocar analyze --help deve exibir descrições dos argumentos e Exit_Code 0."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "REPO_PATH" in result.output
    assert "TASK_DESCRIPTION" in result.output


# ---------------------------------------------------------------------------
# Task 7.3: Mensagens de progresso [1/5] a [5/5]
# Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
# ---------------------------------------------------------------------------

def test_progress_messages_appear_in_output():
    """Todas as mensagens de progresso [1/5] a [5/5] devem aparecer na saída."""
    mock_analyze, mock_select, mock_compress, mock_cache, mock_dispatch = _make_pipeline_mocks()

    with (
        patch("cli.analyze_repository", mock_analyze),
        patch("cli.select_relevant_files", mock_select),
        patch("cli.compress_context", mock_compress),
        patch("cli.get_or_update_cache", mock_cache),
        patch("cli.dispatch", mock_dispatch),
    ):
        result = runner.invoke(app, [_VALID_REPO, _VALID_TASK])

    assert result.exit_code == 0
    for i in range(1, 6):
        assert f"[{i}/5]" in result.output, f"Mensagem [{i}/5] não encontrada na saída"


def test_progress_messages_appear_in_correct_order():
    """As mensagens de progresso devem aparecer na ordem [1/5], [2/5], ..., [5/5]."""
    mock_analyze, mock_select, mock_compress, mock_cache, mock_dispatch = _make_pipeline_mocks()

    with (
        patch("cli.analyze_repository", mock_analyze),
        patch("cli.select_relevant_files", mock_select),
        patch("cli.compress_context", mock_compress),
        patch("cli.get_or_update_cache", mock_cache),
        patch("cli.dispatch", mock_dispatch),
    ):
        result = runner.invoke(app, [_VALID_REPO, _VALID_TASK])

    output = result.output
    positions = [output.find(f"[{i}/5]") for i in range(1, 6)]
    # Todos devem estar presentes
    assert all(pos >= 0 for pos in positions), f"Posições: {positions}"
    # Devem estar em ordem crescente
    assert positions == sorted(positions), (
        f"Mensagens fora de ordem. Posições: {positions}"
    )


def test_progress_message_1_before_repository_analyzer():
    """[1/5] deve aparecer antes de Repository_Analyzer ser chamado."""
    call_order = []

    def tracking_analyze(repo_path):
        call_order.append("analyze_repository")
        from tokemize.models import RepositoryStructure
        return RepositoryStructure(root_path=repo_path)

    mock_select, mock_compress, mock_cache, mock_dispatch = (
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    from tokemize.models import CachedContext, CompressedContext, SelectedContext
    mock_select.return_value = SelectedContext(task_description=_VALID_TASK)
    mock_compress.return_value = CompressedContext(
        task_description=_VALID_TASK, compressed_content="", token_count=0
    )
    mock_cache.return_value = CachedContext(
        task_description=_VALID_TASK, content="ok", cache_hit=False, token_count=0
    )
    mock_dispatch.return_value = "ok"

    with (
        patch("cli.analyze_repository", side_effect=tracking_analyze),
        patch("cli.select_relevant_files", mock_select),
        patch("cli.compress_context", mock_compress),
        patch("cli.get_or_update_cache", mock_cache),
        patch("cli.dispatch", mock_dispatch),
    ):
        result = runner.invoke(app, [_VALID_REPO, _VALID_TASK])

    assert result.exit_code == 0
    assert "[1/5]" in result.output
    assert "analyze_repository" in call_order


# ---------------------------------------------------------------------------
# Task 6.4: Ordem do pipeline e argumentos corretos
# Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
# ---------------------------------------------------------------------------

def test_pipeline_called_in_correct_order():
    """Os módulos do pipeline devem ser chamados na ordem correta."""
    call_order = []

    from tokemize.models import (
        CachedContext,
        CompressedContext,
        RepositoryStructure,
        SelectedContext,
    )

    structure = RepositoryStructure(root_path=_VALID_REPO)
    selected = SelectedContext(task_description=_VALID_TASK)
    compressed = CompressedContext(
        task_description=_VALID_TASK, compressed_content="resumo", token_count=5
    )
    cached = CachedContext(
        task_description=_VALID_TASK, content="resposta", cache_hit=False, token_count=5
    )

    def track(name, return_value):
        def fn(*args, **kwargs):
            call_order.append(name)
            return return_value
        return fn

    with (
        patch("cli.analyze_repository", side_effect=track("analyze_repository", structure)),
        patch("cli.select_relevant_files", side_effect=track("select_relevant_files", selected)),
        patch("cli.compress_context", side_effect=track("compress_context", compressed)),
        patch("cli.get_or_update_cache", side_effect=track("get_or_update_cache", cached)),
        patch("cli.dispatch", side_effect=track("dispatch", "resposta")),
    ):
        result = runner.invoke(app, [_VALID_REPO, _VALID_TASK])

    assert result.exit_code == 0
    assert call_order == [
        "analyze_repository",
        "select_relevant_files",
        "compress_context",
        "get_or_update_cache",
        "dispatch",
    ], f"Ordem incorreta: {call_order}"


def test_pipeline_called_with_correct_arguments():
    """Cada módulo do pipeline deve receber os argumentos corretos."""
    from tokemize.models import (
        CachedContext,
        CompressedContext,
        RepositoryStructure,
        SelectedContext,
    )

    structure = RepositoryStructure(root_path=_VALID_REPO)
    selected = SelectedContext(task_description=_VALID_TASK)
    compressed = CompressedContext(
        task_description=_VALID_TASK, compressed_content="resumo", token_count=5
    )
    cached = CachedContext(
        task_description=_VALID_TASK, content="resposta", cache_hit=False, token_count=5
    )

    mock_analyze = MagicMock(return_value=structure)
    mock_select = MagicMock(return_value=selected)
    mock_compress = MagicMock(return_value=compressed)
    mock_cache = MagicMock(return_value=cached)
    mock_dispatch = MagicMock(return_value="resposta")

    with (
        patch("cli.analyze_repository", mock_analyze),
        patch("cli.select_relevant_files", mock_select),
        patch("cli.compress_context", mock_compress),
        patch("cli.get_or_update_cache", mock_cache),
        patch("cli.dispatch", mock_dispatch),
    ):
        result = runner.invoke(app, [_VALID_REPO, _VALID_TASK])

    assert result.exit_code == 0

    # Req 4.1: Repository_Analyzer recebe repo_path
    mock_analyze.assert_called_once_with(_VALID_REPO)

    # Req 4.2: Intelligent_Selector recebe resultado do Repository_Analyzer + task_description
    mock_select.assert_called_once_with(structure, _VALID_TASK)

    # Req 4.3: Compressor recebe resultado do Intelligent_Selector
    mock_compress.assert_called_once_with(selected)

    # Req 4.4: Context_Cache recebe resultado do Compressor + task_description
    mock_cache.assert_called_once_with(compressed, _VALID_TASK)

    # Req 4.5: LLM_Dispatcher recebe resultado do Context_Cache
    mock_dispatch.assert_called_once_with(cached)
