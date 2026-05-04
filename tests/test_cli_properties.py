"""Property-based tests para a CLI do Tokemize.

Usa Hypothesis para verificar propriedades universais que devem valer
para qualquer input válido ou inválido.

Propriedades testadas:
  Property 1 — Caminhos inexistentes são sempre rejeitados com Exit_Code 1
  Property 2 — Arquivos (não-diretórios) são sempre rejeitados com Exit_Code 1
  Property 3 — Strings de whitespace puro são sempre rejeitadas como task_description
  Property 4 — Descrições com menos de 10 chars não-brancos são sempre rejeitadas
  Property 5 — Descrições válidas nunca são bloqueadas pela validação
  Property 6 — Exceções do pipeline sempre produzem Exit_Code 2
  Property 7 — O resultado do LLM é sempre exibido precedido do cabeçalho correto

Nota sobre mixing Hypothesis + pytest fixtures:
  Hypothesis não suporta misturar parâmetros @given com fixtures pytest na mesma
  assinatura. Testes que precisam de diretórios temporários criam-nos via
  `tempfile.mkdtemp()` e limpam com `shutil.rmtree()` manualmente.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from hypothesis import given, settings
from hypothesis import strategies as st
from typer.testing import CliRunner

from cli import app

runner = CliRunner()

# Mapeamento: nome do patch → nome legível usado nas mensagens de erro
_MODULE_PATCH_TO_STEP_NAME = {
    "cli.analyze_repository": "Repository_Analyzer",
    "cli.select_relevant_files": "Intelligent_Selector",
    "cli.compress_context": "Compressor",
    "cli.save_context": "Context_Saver",
    "cli.get_or_update_cache": "Context_Cache",
    "cli.dispatch": "LLM_Dispatcher",
}

# Descrição válida usada como placeholder quando o foco do teste é outra coisa
_VALID_TASK = "implementar autenticação de usuários"


def _non_whitespace_count(s: str) -> int:
    """Conta caracteres não-brancos em uma string (usando str.split para consistência com cli.py)."""
    # Usa a mesma lógica de cli.py: remove espaço, tab, newline
    # Mas também remove outros whitespace Unicode para evitar falsos positivos
    return len("".join(s.split()))


def _mock_pipeline_success(llm_response: str = "resposta do LLM") -> dict:
    """Retorna dicionário de mocks para todo o pipeline com sucesso."""
    from tokemize.models import (
        CachedContext,
        CompressedContext,
        RepositoryStructure,
        SavedContext,
        SelectedContext,
    )

    return {
        "cli.analyze_repository": MagicMock(
            return_value=RepositoryStructure(root_path="/repo")
        ),
        "cli.select_relevant_files": MagicMock(
            return_value=SelectedContext(task_description=_VALID_TASK)
        ),
        "cli.compress_context": MagicMock(
            return_value=CompressedContext(
                task_description=_VALID_TASK,
                compressed_content="",
                token_count=0,
            )
        ),
        "cli.save_context": MagicMock(
            return_value=SavedContext(
                task_description=_VALID_TASK,
                compressed_content="",
                token_count=0,
                context_file_path="outputs/context_pack.md",
            )
        ),
        "cli.get_or_update_cache": MagicMock(
            return_value=CachedContext(
                task_description=_VALID_TASK,
                content=llm_response,
                cache_hit=False,
                token_count=0,
                context_file_path="outputs/context_pack.md",
            )
        ),
        "cli.dispatch": MagicMock(return_value=llm_response),
    }


def _invoke_with_mocked_pipeline(repo_path: str, task: str, llm_response: str = "ok"):
    """Invoca o comando analyze com todo o pipeline mockado."""
    mocks = _mock_pipeline_success(llm_response)
    with (
        patch("cli.analyze_repository", mocks["cli.analyze_repository"]),
        patch("cli.select_relevant_files", mocks["cli.select_relevant_files"]),
        patch("cli.compress_context", mocks["cli.compress_context"]),
        patch("cli.save_context", mocks["cli.save_context"]),
        patch("cli.get_or_update_cache", mocks["cli.get_or_update_cache"]),
        patch("cli.dispatch", mocks["cli.dispatch"]),
    ):
        return runner.invoke(app, [repo_path, task])


# ---------------------------------------------------------------------------
# Property 1: Caminhos inexistentes são sempre rejeitados com Exit_Code 1
# Validates: Requirements 2.1
# ---------------------------------------------------------------------------

@given(
    st.text(min_size=1).filter(
        lambda p: not Path(p).exists() and not p.startswith("-")
    )
)
@settings(max_examples=100)
def test_nonexistent_path_exits_with_code_1(nonexistent_path: str) -> None:
    """Para qualquer string que não corresponda a um caminho existente,
    a CLI deve encerrar com Exit_Code 1 e exibir o caminho na saída."""
    result = runner.invoke(app, [nonexistent_path, _VALID_TASK])
    assert result.exit_code == 1, (
        f"Esperado exit_code=1, obtido {result.exit_code}. "
        f"Saída: {result.output!r}"
    )
    assert nonexistent_path in result.output


# ---------------------------------------------------------------------------
# Property 2: Arquivos (não-diretórios) são sempre rejeitados com Exit_Code 1
# Validates: Requirements 2.2
# ---------------------------------------------------------------------------

@given(
    st.text(
        min_size=1,
        max_size=40,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_.",
        ),
    )
)
@settings(max_examples=100)
def test_file_path_exits_with_code_1(filename: str) -> None:
    """Para qualquer caminho existente que seja um arquivo (não diretório),
    a CLI deve encerrar com Exit_Code 1 e exibir o caminho na saída."""
    tmp_dir = tempfile.mkdtemp()
    try:
        file_path = Path(tmp_dir) / filename
        try:
            file_path.write_text("conteúdo de teste")
        except (OSError, ValueError):
            return  # Nome inválido no SO — pular

        result = runner.invoke(app, [str(file_path), _VALID_TASK])
        assert result.exit_code == 1, (
            f"Esperado exit_code=1, obtido {result.exit_code}. "
            f"Saída: {result.output!r}"
        )
        assert str(file_path) in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 3: Strings de whitespace puro são sempre rejeitadas como task_description
# Validates: Requirements 3.1
# ---------------------------------------------------------------------------

@given(st.text(alphabet=" \t\n\r", min_size=0))
@settings(max_examples=100)
def test_whitespace_task_description_rejected(whitespace_str: str) -> None:
    """Para qualquer string composta exclusivamente de whitespace (incluindo vazia),
    a CLI deve encerrar com Exit_Code 1 e exibir a mensagem de erro correta."""
    tmp_dir = tempfile.mkdtemp()
    try:
        result = runner.invoke(app, [tmp_dir, whitespace_str])
        assert result.exit_code == 1, (
            f"Esperado exit_code=1, obtido {result.exit_code}. "
            f"Saída: {result.output!r}"
        )
        assert "não pode ser vazia" in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 4: Descrições com menos de 10 chars não-brancos são sempre rejeitadas
# Validates: Requirements 3.2
# ---------------------------------------------------------------------------

@given(
    st.text(min_size=1, max_size=200).filter(
        lambda s: 1 <= _non_whitespace_count(s) <= 9 and not s.startswith("-")
    )
)
@settings(max_examples=100)
def test_short_task_description_rejected(short_desc: str) -> None:
    """Para qualquer string com 1–9 caracteres não-brancos,
    a CLI deve encerrar com Exit_Code 1 e exibir a mensagem de erro correta."""
    tmp_dir = tempfile.mkdtemp()
    try:
        result = runner.invoke(app, [tmp_dir, short_desc])
        assert result.exit_code == 1, (
            f"Esperado exit_code=1, obtido {result.exit_code}. "
            f"Saída: {result.output!r}"
        )
        assert "pelo menos 10 caracteres" in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 5: Descrições válidas nunca são bloqueadas pela validação
# Validates: Requirements 3.3
# ---------------------------------------------------------------------------

@given(
    st.text(min_size=10, max_size=500).filter(
        lambda s: _non_whitespace_count(s) >= 10
    )
)
@settings(max_examples=100)
def test_valid_task_description_passes_validation(valid_desc: str) -> None:
    """Para qualquer string com ≥ 10 chars não-brancos, a validação de
    task_description não deve encerrar com Exit_Code 1 por motivo de validação."""
    tmp_dir = tempfile.mkdtemp()
    try:
        result = _invoke_with_mocked_pipeline(tmp_dir, valid_desc)
        # Não deve falhar com mensagem de validação de task_description
        assert "não pode ser vazia" not in result.output
        assert "pelo menos 10 caracteres" not in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 6: Exceções do pipeline sempre produzem Exit_Code 2
# Validates: Requirements 4.6
# ---------------------------------------------------------------------------

@given(
    st.sampled_from(list(_MODULE_PATCH_TO_STEP_NAME.keys())),
    st.text(min_size=1, max_size=200),
)
@settings(max_examples=100)
def test_pipeline_exception_exits_with_code_2(
    failing_patch: str, error_message: str
) -> None:
    """Para qualquer módulo do pipeline e qualquer mensagem de exceção,
    a CLI deve encerrar com Exit_Code 2 e exibir o nome do módulo e a mensagem."""
    step_name = _MODULE_PATCH_TO_STEP_NAME[failing_patch]
    tmp_dir = tempfile.mkdtemp()
    try:
        mocks = _mock_pipeline_success()
        mocks[failing_patch] = MagicMock(side_effect=Exception(error_message))

        with (
            patch("cli.analyze_repository", mocks["cli.analyze_repository"]),
            patch("cli.select_relevant_files", mocks["cli.select_relevant_files"]),
            patch("cli.compress_context", mocks["cli.compress_context"]),
            patch("cli.save_context", mocks["cli.save_context"]),
            patch("cli.get_or_update_cache", mocks["cli.get_or_update_cache"]),
            patch("cli.dispatch", mocks["cli.dispatch"]),
        ):
            result = runner.invoke(app, [tmp_dir, _VALID_TASK])

        assert result.exit_code == 2, (
            f"Esperado exit_code=2, obtido {result.exit_code}. "
            f"Saída: {result.output!r}"
        )
        assert step_name in result.output
        assert error_message in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Property 7: O resultado do LLM é sempre exibido precedido do cabeçalho correto
# Validates: Requirements 5.6
# ---------------------------------------------------------------------------

@given(st.text(max_size=500).filter(lambda s: "\r" not in s))
@settings(max_examples=100)
def test_llm_result_displayed_with_header(llm_response: str) -> None:
    """Para qualquer string retornada pelo LLM_Dispatcher, a CLI deve exibir
    essa string precedida da linha '=== Resultado ==='.
    
    Nota: strings contendo \\r são filtradas pois o CliRunner normaliza
    carriage returns na saída capturada.
    """
    tmp_dir = tempfile.mkdtemp()
    try:
        result = _invoke_with_mocked_pipeline(tmp_dir, _VALID_TASK, llm_response)
        assert result.exit_code == 0, (
            f"Esperado exit_code=0, obtido {result.exit_code}. "
            f"Saída: {result.output!r}"
        )
        assert "=== Resultado ===" in result.output
        assert llm_response in result.output
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
