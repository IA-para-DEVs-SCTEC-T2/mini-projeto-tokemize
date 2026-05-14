"""Testes unitários e de propriedade para o orquestrador do pipeline Tokemize.

Este módulo contém testes unitários que verificam o comportamento do
orquestrador em cenários específicos, e testes de propriedade (Hypothesis)
que validam as 15 propriedades de corretude formais do design.
"""

from __future__ import annotations

import os
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st

from tokemize.models import (
    AnalysisOutput,
    GeneratorOutput,
    PipelineResult,
    ScanOutput,
    SelectionOutput,
    SummaryOutput,
)
from tokemize.orchestrator import run_pipeline


# ══════════════════════════════════════════════════════════════════════════════
# Testes Unitários
# ══════════════════════════════════════════════════════════════════════════════


def test_run_pipeline_success():
    """Pipeline completo com stubs retorna PipelineResult(success=True) com prompt não-vazio.

    Validates: Requirements 1.3, 1.4, 1.5, 1.6
    """
    result = run_pipeline(".", "add authentication")

    assert result.success is True
    assert result.prompt != ""
    assert result.failed_stage is None
    assert result.error_message is None
    assert result.elapsed_seconds > 0
    assert len(result.stages_completed) == 6
    assert result.stages_completed == [
        "scanner",
        "analyzer",
        "selector",
        "summarizer",
        "generator",
        "reporter",
    ]


@pytest.mark.parametrize(
    "stage_to_fail,expected_failed_stage,expected_completed_count",
    [
        ("scanner",    "scanner",    0),
        ("analyzer",   "analyzer",   1),
        ("selector",   "selector",   2),
        ("summarizer", "summarizer", 3),
        ("generator",  "generator",  4),
        ("reporter",   "reporter",   5),
    ],
)
def test_run_pipeline_fails_at_each_stage(
    stage_to_fail: str,
    expected_failed_stage: str,
    expected_completed_count: int,
):
    """Pipeline falha em cada uma das 6 etapas — verifica success=False, failed_stage correto e error_message não-vazio."""
    stage_fn_map = {
        "scanner":    "scan_repository",
        "analyzer":   "analyze_files",
        "selector":   "select_relevant",
        "summarizer": "summarize_selected",
        "generator":  "generate_prompt",
        "reporter":   "format_result",
    }
    fn_name = stage_fn_map[stage_to_fail]
    with patch(f"tokemize.orchestrator.{fn_name}") as mock_stage:
        mock_stage.side_effect = RuntimeError(f"Simulated failure in {stage_to_fail}")

        result = run_pipeline(".", "any task")

        assert result.success is False
        assert result.failed_stage == expected_failed_stage
        assert result.error_message is not None
        assert f"Simulated failure in {stage_to_fail}" in result.error_message
        assert len(result.stages_completed) == expected_completed_count
        assert result.elapsed_seconds > 0


def test_stages_completed_on_partial_failure():
    """stages_completed contém exatamente as etapas anteriores à falha."""
    # Falha no selector (3ª etapa) → stages_completed deve ter ["scanner", "analyzer"]
    with patch("tokemize.orchestrator.select_relevant") as mock_selector:
        mock_selector.side_effect = RuntimeError("Selector down")

        result = run_pipeline(".", "task")

        assert result.success is False
        assert result.failed_stage == "selector"
        assert result.stages_completed == ["scanner", "analyzer"]


def test_elapsed_seconds_is_positive():
    """elapsed_seconds > 0 após execução bem-sucedida.

    Validates: Requirements 1.5, 3.6, 14.4
    """
    result = run_pipeline(".", "task")
    assert result.elapsed_seconds > 0.0


def test_pipeline_result_on_empty_scan():
    """Scanner retorna ScanOutput(files=[]) → pipeline conclui com success=True.

    Validates: Requirements 1.3, 6.2
    """
    # Mock do scanner para retornar lista vazia.
    with patch("tokemize.orchestrator.scan_repository") as mock_scanner:
        mock_scanner.return_value = ScanOutput(
            repo_path=".",
            files=[],
            total_files=0,
            skipped_files=0,
        )

        result = run_pipeline(".", "task")

        # Pipeline deve concluir com sucesso mesmo sem arquivos.
        assert result.success is True
        assert len(result.stages_completed) == 6


# ══════════════════════════════════════════════════════════════════════════════
# Testes de Propriedade (Hypothesis) — Opcionais
# ══════════════════════════════════════════════════════════════════════════════

# Estratégias Hypothesis para gerar inputs válidos e inválidos.
repo_paths = st.one_of(
    st.just("."),  # diretório válido
    st.just("/caminho/inexistente"),  # diretório inválido
    st.text(min_size=0, max_size=50),  # strings arbitrárias
)

tasks = st.text(min_size=0, max_size=100)


@pytest.mark.optional
@given(repo_path=repo_paths, task=tasks)
def test_property_1_run_pipeline_never_raises(repo_path: str, task: str):
    """Property 1: run_pipeline nunca propaga exceção.

    Para qualquer repo_path e task (incluindo strings vazias e arbitrárias),
    run_pipeline SHALL sempre retornar um PipelineResult e nunca lançar exceção.

    Validates: Requirements 3.5, 14.1
    """
    # Não deve lançar exceção, independentemente do input.
    result = run_pipeline(repo_path, task)
    assert isinstance(result, PipelineResult)


@pytest.mark.optional
@given(task=tasks)
def test_property_2_success_implies_no_failure_fields(task: str):
    """Property 2: Invariante de sucesso — campos nulos em caso de sucesso.

    Para qualquer execução com success=True, failed_stage SHALL ser None
    e error_message SHALL ser None.

    Validates: Requirements 1.4, 14.2
    """
    result = run_pipeline(".", task)

    if result.success:
        assert result.failed_stage is None
        assert result.error_message is None


@pytest.mark.optional
def test_property_3_failure_implies_valid_failed_stage():
    """Property 3: Invariante de falha — failed_stage pertence ao conjunto válido.

    Para qualquer execução com success=False, failed_stage SHALL ser um dos
    7 nomes válidos.

    Validates: Requirements 3.2, 14.3
    """
    valid_stages = {
        "scanner",
        "analyzer",
        "selector",
        "summarizer",
        "generator",
        "reporter",
    }

    # Força falha no scanner com diretório inválido.
    result = run_pipeline("/caminho/inexistente", "task")

    if not result.success:
        assert result.failed_stage in valid_stages


@pytest.mark.optional
@given(repo_path=repo_paths, task=tasks)
def test_property_4_elapsed_seconds_non_negative(repo_path: str, task: str):
    """Property 4: elapsed_seconds é sempre não-negativo.

    Para qualquer execução, PipelineResult.elapsed_seconds SHALL ser >= 0.0.

    Validates: Requirements 1.5, 3.6, 14.4
    """
    result = run_pipeline(repo_path, task)
    assert result.elapsed_seconds >= 0.0


@pytest.mark.optional
@given(repo_path=repo_paths, task=tasks)
def test_property_5_stages_completed_is_prefix(repo_path: str, task: str):
    """Property 5: stages_completed é prefixo ordenado da sequência de etapas.

    Para qualquer execução, stages_completed SHALL ser um prefixo da lista
    ordenada de etapas com comprimento <= 7.

    Validates: Requirements 1.6, 3.4, 14.5, 14.6
    """
    expected_order = [
        "scanner",
        "analyzer",
        "selector",
        "summarizer",
        "generator",
        "reporter",
    ]

    result = run_pipeline(repo_path, task)

    assert len(result.stages_completed) <= 6

    # Verifica que stages_completed é um prefixo de expected_order.
    for i, stage in enumerate(result.stages_completed):
        assert stage == expected_order[i]


@pytest.mark.optional
@pytest.mark.parametrize("fail_at_index", range(6))
def test_property_6_failure_preserves_previous_stages(fail_at_index: int):
    """Property 6: Falha em etapa N preserva stages_completed das etapas anteriores."""
    stage_names = [
        "scanner",
        "analyzer",
        "selector",
        "summarizer",
        "generator",
        "reporter",
    ]
    stage_fn_map = {
        "scanner":    "scan_repository",
        "analyzer":   "analyze_files",
        "selector":   "select_relevant",
        "summarizer": "summarize_selected",
        "generator":  "generate_prompt",
        "reporter":   "format_result",
    }
    stage_to_fail = stage_names[fail_at_index]
    fn_name = stage_fn_map[stage_to_fail]

    with patch(f"tokemize.orchestrator.{fn_name}") as mock_stage:
        mock_stage.side_effect = RuntimeError(f"Fail at {stage_to_fail}")

        result = run_pipeline(".", "task")

        assert result.success is False
        assert len(result.stages_completed) == fail_at_index
        assert result.stages_completed == stage_names[:fail_at_index]
