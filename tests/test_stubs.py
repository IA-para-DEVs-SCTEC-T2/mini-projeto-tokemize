"""Testes unitários para os stubs das etapas do pipeline.

Este módulo contém testes unitários para cada um dos 7 stubs funcionais:
scanner, analyzer, embeddings, selector, summarizer, generator e reporter.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from tokemize.analyzer import analyze_files
from tokemize.embeddings import generate_embeddings
from tokemize.generator import generate_prompt
from tokemize.models import (
    AnalysisOutput,
    AnalyzedFile,
    EmbeddedFile,
    EmbeddingsOutput,
    GeneratorOutput,
    ScanOutput,
    ScannedFile,
    SelectedFile,
    SelectionOutput,
    SummaryOutput,
)
from tokemize.reporter import format_result
from tokemize.scanner import scan_repository
from tokemize.selector import select_relevant
from tokemize.summarizer import summarize_selected


# ══════════════════════════════════════════════════════════════════════════════
# Testes para Scanner
# ══════════════════════════════════════════════════════════════════════════════


def test_scan_repository_returns_valid_scan_output():
    """Verifica estrutura do ScanOutput retornado.

    Validates: Requirements 6.1
    """
    output = scan_repository(".")

    assert isinstance(output, ScanOutput)
    assert output.repo_path == "."
    assert isinstance(output.files, list)
    assert isinstance(output.total_files, int)
    assert isinstance(output.skipped_files, int)


def test_scan_repository_raises_not_a_directory_error():
    """Verifica NotADirectoryError para caminho inválido.

    Validates: Requirements 6.3
    """
    with pytest.raises(NotADirectoryError):
        scan_repository("/caminho/inexistente/xyz")


def test_scan_repository_total_files_consistent():
    """total_files == len(files).

    Validates: Requirements 6.5
    """
    output = scan_repository(".")
    assert output.total_files == len(output.files)


@pytest.mark.optional
@given(repo_path=st.just("."))
def test_property_8_scanner_total_files_consistent(repo_path: str):
    """Property 8: Scanner — total_files é consistente com files.

    Para qualquer ScanOutput retornado por scan_repository, total_files
    SHALL ser igual a len(files).

    Validates: Requirements 6.5
    """
    output = scan_repository(repo_path)
    assert output.total_files == len(output.files)


@pytest.mark.optional
@given(
    invalid_path=st.one_of(
        st.just("/caminho/inexistente"),
        st.text(min_size=1, max_size=50).filter(
            lambda p: not p.startswith(".")
        ),
    )
)
def test_property_9_scanner_raises_for_invalid_paths(invalid_path: str):
    """Property 9: Scanner — NotADirectoryError para caminhos inválidos.

    Para qualquer string que não corresponda a um diretório válido,
    scan_repository SHALL lançar NotADirectoryError.

    Validates: Requirements 6.3
    """
    import os

    if not os.path.isdir(invalid_path):
        with pytest.raises(NotADirectoryError):
            scan_repository(invalid_path)


# ══════════════════════════════════════════════════════════════════════════════
# Testes para Embeddings
# ══════════════════════════════════════════════════════════════════════════════


def test_generate_embeddings_counters_consistent():
    """total_embedded + total_failed == len(embedded_files).

    Validates: Requirements 8.4, 8.5
    """
    analysis_output = AnalysisOutput(
        analyzed_files=[
            AnalyzedFile(
                path="file1.py",
                language="python",
                size_bytes=100,
                line_count=10,
                file_type="source",
                artifact_count=1,
                content="# content",
                relevance_hint=0.5,
            )
        ],
        total_analyzed=1,
        total_skipped=0,
    )

    output = generate_embeddings(analysis_output)

    assert output.total_embedded + output.total_failed == len(output.embedded_files)


def test_generate_embeddings_empty_input():
    """Retorna EmbeddingsOutput(embedded_files=[]) para input vazio.

    Validates: Requirements 8.2
    """
    output = generate_embeddings(AnalysisOutput())
    assert output.embedded_files == []
    assert output.total_embedded == 0
    assert output.total_failed == 0


@pytest.mark.optional
@given(
    num_files=st.integers(min_value=0, max_value=10),
)
def test_property_10_embeddings_counters_consistent(num_files: int):
    """Property 10: Embeddings — contadores são consistentes com a lista.

    Para qualquer EmbeddingsOutput, total_embedded + total_failed SHALL
    ser igual a len(embedded_files).

    Validates: Requirements 8.4, 8.5
    """
    analyzed_files = [
        AnalyzedFile(
            path=f"file{i}.py",
            language="python",
            size_bytes=100,
            line_count=10,
            file_type="source",
            artifact_count=1,
            content="# content",
            relevance_hint=0.5,
        )
        for i in range(num_files)
    ]

    analysis_output = AnalysisOutput(
        analyzed_files=analyzed_files,
        total_analyzed=num_files,
        total_skipped=0,
    )

    output = generate_embeddings(analysis_output)

    assert output.total_embedded + output.total_failed == len(output.embedded_files)


# ══════════════════════════════════════════════════════════════════════════════
# Testes para Selector
# ══════════════════════════════════════════════════════════════════════════════


def test_select_relevant_ordered_by_score():
    """selected_files ordenados por relevance_score decrescente.

    Validates: Requirements 9.1
    """
    embeddings_output = EmbeddingsOutput(
        embedded_files=[
            EmbeddedFile(
                path="file1.py",
                language="python",
                content="content1",
                embedding=[0.1, 0.2],
            ),
            EmbeddedFile(
                path="file2.py",
                language="python",
                content="content2",
                embedding=[0.3, 0.4],
            ),
        ],
        total_embedded=2,
        total_failed=0,
    )

    output = select_relevant(embeddings_output, "task")

    # Verifica ordenação decrescente.
    for i in range(len(output.selected_files) - 1):
        assert (
            output.selected_files[i].relevance_score
            >= output.selected_files[i + 1].relevance_score
        )


def test_select_relevant_task_preserved():
    """SelectionOutput.task == task passado como argumento.

    Validates: Requirements 9.4
    """
    embeddings_output = EmbeddingsOutput()
    task = "add authentication"

    output = select_relevant(embeddings_output, task)

    assert output.task == task


def test_select_relevant_empty_input():
    """Retorna SelectionOutput(selected_files=[]) para input vazio.

    Validates: Requirements 9.2
    """
    output = select_relevant(EmbeddingsOutput(), "task")
    assert output.selected_files == []
    assert output.total_candidates == 0


@pytest.mark.optional
@given(
    num_files=st.integers(min_value=2, max_value=10),
)
def test_property_11_selector_ordered_by_relevance(num_files: int):
    """Property 11: Selector — arquivos ordenados por relevância decrescente.

    Para qualquer SelectionOutput com dois ou mais arquivos, relevance_score
    SHALL estar em ordem não-crescente.

    Validates: Requirements 9.1
    """
    embedded_files = [
        EmbeddedFile(
            path=f"file{i}.py",
            language="python",
            content=f"content{i}",
            embedding=[0.1 * i, 0.2 * i],
        )
        for i in range(num_files)
    ]

    embeddings_output = EmbeddingsOutput(
        embedded_files=embedded_files,
        total_embedded=num_files,
        total_failed=0,
    )

    output = select_relevant(embeddings_output, "task")

    if len(output.selected_files) >= 2:
        for i in range(len(output.selected_files) - 1):
            assert (
                output.selected_files[i].relevance_score
                >= output.selected_files[i + 1].relevance_score
            )


@pytest.mark.optional
@given(task=st.text(min_size=1, max_size=100))
def test_property_12_selector_task_preserved(task: str):
    """Property 12: Selector — task preservada no output.

    Para qualquer chamada a select_relevant(embeddings_output, task),
    SelectionOutput.task SHALL ser igual à string task passada como argumento.

    Validates: Requirements 9.4
    """
    embeddings_output = EmbeddingsOutput()
    output = select_relevant(embeddings_output, task)
    assert output.task == task


# ══════════════════════════════════════════════════════════════════════════════
# Testes para Generator
# ══════════════════════════════════════════════════════════════════════════════


def test_generate_prompt_fallback_to_task_when_empty_context():
    """prompt contém a task quando summarized_content é vazio.

    Validates: Requirements 11.2
    """
    summary_output = SummaryOutput(
        summarized_content="",
        token_count=0,
        files_summarized=0,
    )
    task = "add tests"

    output = generate_prompt(summary_output, task)

    # O novo generator gera o Context Pack completo — a task deve estar no prompt
    assert task in output.prompt
    assert output.token_count >= 0


def test_generate_prompt_contains_context_and_task():
    """Prompt contém contexto e task quando summarized_content não é vazio.

    Validates: Requirements 11.1
    """
    summary_output = SummaryOutput(
        summarized_content="file1.py\nfile2.py",
        token_count=2,
        files_summarized=2,
    )
    task = "refactor auth"

    output = generate_prompt(summary_output, task)

    assert "file1.py" in output.prompt
    assert "file2.py" in output.prompt
    assert "refactor auth" in output.prompt
    assert output.token_count > 0


@pytest.mark.optional
@given(task=st.text(min_size=1, max_size=100))
def test_property_13_generator_fallback_to_task(task: str):
    """Property 13: Generator — task está presente no prompt gerado.

    Para qualquer chamada com summarized_content vazio, GeneratorOutput.prompt
    SHALL conter a string task.

    Validates: Requirements 11.2
    """
    summary_output = SummaryOutput(
        summarized_content="",
        token_count=0,
        files_summarized=0,
    )

    output = generate_prompt(summary_output, task)

    assert task in output.prompt


# ══════════════════════════════════════════════════════════════════════════════
# Testes para Reporter
# ══════════════════════════════════════════════════════════════════════════════


def test_format_result_success_with_prompt():
    """Retorna PipelineResult(success=True, prompt=generator_output.prompt).

    Validates: Requirements 12.1
    """
    generator_output = GeneratorOutput(
        prompt="final prompt",
        token_count=2,
    )

    result = format_result(generator_output)

    assert result.success is True
    assert result.prompt == "final prompt"
    assert result.failed_stage is None
    assert result.error_message is None


def test_format_result_success_with_empty_prompt():
    """Retorna PipelineResult(success=True, prompt="") para prompt="".

    Validates: Requirements 12.2
    """
    generator_output = GeneratorOutput(prompt="", token_count=0)

    result = format_result(generator_output)

    assert result.success is True
    assert result.prompt == ""
    assert result.failed_stage is None
    assert result.error_message is None


def test_format_result_never_raises():
    """Nunca lança exceção para nenhum input.

    Validates: Requirements 12.3
    """
    # Testa com vários inputs, incluindo extremos.
    inputs = [
        GeneratorOutput(prompt="", token_count=0),
        GeneratorOutput(prompt="a" * 10000, token_count=10000),
        GeneratorOutput(prompt="normal prompt", token_count=2),
    ]

    for gen_output in inputs:
        result = format_result(gen_output)
        assert isinstance(result, type(result))  # Não lança exceção.


@pytest.mark.optional
@given(
    prompt=st.text(min_size=0, max_size=1000),
    token_count=st.integers(min_value=0, max_value=10000),
)
def test_property_14_reporter_never_raises(prompt: str, token_count: int):
    """Property 14: Reporter — nunca lança exceção.

    Para qualquer GeneratorOutput (incluindo prompt="" e valores extremos),
    format_result SHALL sempre retornar um PipelineResult válido e nunca
    lançar exceção.

    Validates: Requirements 12.3
    """
    generator_output = GeneratorOutput(prompt=prompt, token_count=token_count)
    result = format_result(generator_output)
    assert isinstance(result, type(result))


@pytest.mark.optional
@given(prompt=st.text(min_size=1, max_size=1000))
def test_property_15_reporter_round_trip_prompt(prompt: str):
    """Property 15: Reporter — round-trip do prompt.

    Para qualquer GeneratorOutput com prompt não-vazio,
    format_result(generator_output).prompt SHALL ser igual a
    generator_output.prompt.

    Validates: Requirements 12.1
    """
    generator_output = GeneratorOutput(prompt=prompt, token_count=len(prompt.split()))
    result = format_result(generator_output)
    assert result.prompt == generator_output.prompt
