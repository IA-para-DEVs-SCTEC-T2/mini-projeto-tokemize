"""Orquestrador central do pipeline Tokemize.

Coordena a execução sequencial das 5 etapas do pipeline:
scanner → analyzer → selector → generator → reporter.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from tokemize.analyzer import analyze_files
from tokemize.generator import generate_prompt
from tokemize.models import PipelineResult
from tokemize.reporter import format_result
from tokemize.scanner import scan_repository
from tokemize.selector import select_relevant
from tokemize.summarizer import summarize_selected

logger = logging.getLogger(__name__)


def run_pipeline(repo_path: str, task: str) -> PipelineResult:
    """Executa o pipeline completo de otimização de contexto.

    Coordena a execução sequencial das 5 etapas do pipeline, propagando
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
        as etapas foram concluídas sem erro, ou ``success=False`` com
        ``failed_stage`` e ``error_message`` se alguma etapa falhou.

    Example:
        >>> result = run_pipeline(".", "add authentication")
        >>> result.success
        True
    """
    start_time = time.perf_counter()
    stages_completed: list[str] = []

    pipeline_stages: list[tuple[str, Any, bool]] = [
        ("scanner",    scan_repository,    False),
        ("analyzer",   analyze_files,      False),
        ("selector",   select_relevant,    True),
        ("summarizer", summarize_selected, False),
        ("generator",  generate_prompt,    True),
        ("reporter",   format_result,      False),
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
            logger.info(
                "Etapa concluída: %s | tempo=%.3fs",
                stage_name,
                time.perf_counter() - stage_start,
            )

        except Exception as exc:
            logger.error("Falha na etapa '%s': %s", stage_name, exc, exc_info=True)
            return PipelineResult(
                success=False,
                prompt="",
                failed_stage=stage_name,
                error_message=str(exc),
                elapsed_seconds=time.perf_counter() - start_time,
                stages_completed=stages_completed,
            )

    result: PipelineResult = current_output
    result.elapsed_seconds = time.perf_counter() - start_time
    result.stages_completed = stages_completed
    return result
