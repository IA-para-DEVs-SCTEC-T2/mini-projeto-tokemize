"""Orquestrador central do pipeline Tokemize.

Este módulo implementa a função `run_pipeline`, responsável por coordenar
a execução sequencial das 7 etapas do pipeline de otimização de contexto:
scanner → analyzer → embeddings → selector → summarizer → generator → reporter.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import tokemize.analyzer as analyzer
import tokemize.embeddings as embeddings
import tokemize.generator as generator
import tokemize.reporter as reporter
import tokemize.scanner as scanner
import tokemize.selector as selector
import tokemize.summarizer as summarizer
from tokemize.analyzer import analyze_files
from tokemize.embeddings import generate_embeddings
from tokemize.generator import generate_prompt
from tokemize.models import PipelineResult
from tokemize.reporter import format_result
from tokemize.scanner import scan_repository
from tokemize.selector import select_relevant
from tokemize.summarizer import summarize_selected

logger = logging.getLogger(__name__)


def run_pipeline(repo_path: str, task: str) -> PipelineResult:
    """Executa o pipeline completo de otimização de contexto para LLMs.

    Coordena a execução sequencial das 7 etapas do pipeline, propagando
    dados entre elas, capturando falhas com logging estruturado e retornando
    um ``PipelineResult`` com o resultado final e metadados de execução.

    O orquestrador nunca propaga exceções — sempre retorna um
    ``PipelineResult``, com ``success=True`` em caso de sucesso ou
    ``success=False`` com ``failed_stage`` e ``error_message`` em caso de
    falha.

    Args:
        repo_path: Caminho absoluto ou relativo para a raiz do repositório
            a ser analisado.
        task: Descrição textual da tarefa técnica fornecida pelo usuário.

    Returns:
        PipelineResult com ``success=True`` e ``prompt`` preenchido se todas
        as 7 etapas foram concluídas sem erro, ou ``success=False`` com
        ``failed_stage`` e ``error_message`` se alguma etapa falhou.

        ``elapsed_seconds`` contém o tempo total de execução medido com
        ``time.perf_counter()``. ``stages_completed`` contém a lista de
        nomes das etapas concluídas com sucesso, na ordem de execução.

    Example:
        >>> result = run_pipeline(".", "add authentication")
        >>> result.success
        True
        >>> len(result.stages_completed)
        7
    """
    start_time = time.perf_counter()
    stages_completed: list[str] = []

    pipeline_stages: list[tuple[str, Any, bool]] = [
        ("scanner", scan_repository, False),
        ("analyzer", analyze_files, False),
        ("embeddings", generate_embeddings, False),
        ("selector", select_relevant, True),
        ("summarizer", summarize_selected, False),
        ("generator", generate_prompt, True),
        ("reporter", format_result, False),
    ]

    current_output: Any = None

    for stage_name, stage_fn, needs_task in pipeline_stages:
        logger.info("Iniciando etapa: %s", stage_name)
        stage_start = time.perf_counter()

        try:
            if stage_name == "scanner":
                current_output = stage_fn(repo_path)
            elif needs_task:
                current_output = stage_fn(current_output, task)
            else:
                current_output = stage_fn(current_output)

            stages_completed.append(stage_name)
            stage_elapsed = time.perf_counter() - stage_start
            logger.info(
                "Etapa concluída: %s | tempo=%.3fs",
                stage_name,
                stage_elapsed,
            )

        except Exception as exc:
            logger.error(
                "Falha na etapa '%s': %s",
                stage_name,
                exc,
                exc_info=True,
            )
            elapsed = time.perf_counter() - start_time
            return PipelineResult(
                success=False,
                prompt="",
                failed_stage=stage_name,
                error_message=str(exc),
                elapsed_seconds=elapsed,
                stages_completed=stages_completed,
            )

    result: PipelineResult = current_output
    result.elapsed_seconds = time.perf_counter() - start_time
    result.stages_completed = stages_completed
    return result
