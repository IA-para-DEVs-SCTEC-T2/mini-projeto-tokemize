"""Funções auxiliares para geração de dados de teste de métricas.

Fornece construtores para dicts de métricas válidos, relatórios pytest JSON,
relatórios de cobertura JSON e variantes de casos extremos (zero testes,
todos pulados, etc.) usados nos testes da feature test-pipeline-showcase.

Requirements: 2.1–2.9
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Constantes de referência
# ---------------------------------------------------------------------------

VALID_STATUSES: tuple[str, ...] = ("passing", "failing", "unknown")

DEFAULT_LAST_RUN_AT = "2026-05-13T14:30:00Z"


# ---------------------------------------------------------------------------
# Métricas de teste (testMetrics)
# ---------------------------------------------------------------------------


def make_test_metrics(
    *,
    total_tests: int = 42,
    passed: int = 40,
    failed: int = 2,
    skipped: int = 0,
    duration: float = 12.34,
    coverage: float | None = 85.0,
    last_run_at: str | None = DEFAULT_LAST_RUN_AT,
    status: str = "failing",
) -> dict[str, Any]:
    """Cria um dict de métricas de teste válido com valores padrão razoáveis.

    Args:
        total_tests: Número total de testes executados. Padrão: 42.
        passed: Número de testes que passaram. Padrão: 40.
        failed: Número de testes que falharam. Padrão: 2.
        skipped: Número de testes pulados. Padrão: 0.
        duration: Tempo de execução em segundos (2 casas decimais). Padrão: 12.34.
        coverage: Porcentagem de cobertura de código ou None. Padrão: 85.0.
        last_run_at: Timestamp ISO 8601 UTC ou None. Padrão: "2026-05-13T14:30:00Z".
        status: Status da execução ("passing", "failing" ou "unknown"). Padrão: "failing".

    Returns:
        Dict com a estrutura testMetrics conforme o schema do design document.

    Example:
        >>> metrics = make_test_metrics(total_tests=10, passed=10, failed=0, status="passing")
        >>> metrics["status"]
        'passing'
    """
    return {
        "totalTests": total_tests,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": round(duration, 2),
        "coverage": coverage,
        "lastRunAt": last_run_at,
        "status": status,
    }


def make_passing_metrics(
    total_tests: int = 10,
    coverage: float | None = 90.0,
) -> dict[str, Any]:
    """Cria métricas representando uma execução 100% bem-sucedida.

    Args:
        total_tests: Número total de testes. Padrão: 10.
        coverage: Porcentagem de cobertura. Padrão: 90.0.

    Returns:
        Dict de métricas com status "passing", failed=0 e skipped=0.
    """
    return make_test_metrics(
        total_tests=total_tests,
        passed=total_tests,
        failed=0,
        skipped=0,
        duration=5.00,
        coverage=coverage,
        status="passing",
    )


def make_failing_metrics(
    total_tests: int = 10,
    failed: int = 3,
) -> dict[str, Any]:
    """Cria métricas representando uma execução com falhas.

    Args:
        total_tests: Número total de testes. Padrão: 10.
        failed: Número de testes que falharam. Padrão: 3.

    Returns:
        Dict de métricas com status "failing" e pelo menos um teste falhado.
    """
    total_tests = max(0, total_tests)
    failed = max(0, min(failed, total_tests))
    passed = total_tests - failed
    return make_test_metrics(
        total_tests=total_tests,
        passed=passed,
        failed=failed,
        skipped=0,
        duration=8.50,
        coverage=70.0,
        status="failing",
    )


def make_unknown_metrics() -> dict[str, Any]:
    """Cria métricas representando uma execução com status desconhecido.

    Usado quando o pytest falhou ao executar (exit code > 1) ou quando
    não há testes disponíveis.

    Returns:
        Dict de métricas com status "unknown" e campos zerados.
    """
    return make_test_metrics(
        total_tests=0,
        passed=0,
        failed=0,
        skipped=0,
        duration=0.0,
        coverage=None,
        last_run_at=None,
        status="unknown",
    )


# ---------------------------------------------------------------------------
# Variantes de casos extremos
# ---------------------------------------------------------------------------


def make_zero_tests_metrics() -> dict[str, Any]:
    """Cria métricas para uma execução sem nenhum teste coletado.

    Returns:
        Dict de métricas com totalTests=0 e status "unknown".
    """
    return make_test_metrics(
        total_tests=0,
        passed=0,
        failed=0,
        skipped=0,
        duration=0.0,
        coverage=None,
        status="unknown",
    )


def make_all_skipped_metrics(total_tests: int = 5) -> dict[str, Any]:
    """Cria métricas para uma execução onde todos os testes foram pulados.

    Args:
        total_tests: Número de testes pulados. Padrão: 5.

    Returns:
        Dict de métricas com passed=0, failed=0 e skipped=total_tests.
        Status é "passing" pois failed==0 e totalTests>0.
    """
    return make_test_metrics(
        total_tests=total_tests,
        passed=0,
        failed=0,
        skipped=total_tests,
        duration=0.10,
        coverage=None,
        status="passing",
    )


def make_no_coverage_metrics(
    total_tests: int = 10,
    passed: int = 10,
) -> dict[str, Any]:
    """Cria métricas sem informação de cobertura (coverage=None).

    Args:
        total_tests: Número total de testes. Padrão: 10.
        passed: Número de testes que passaram. Padrão: 10.

    Returns:
        Dict de métricas com coverage=None.
    """
    total_tests = max(0, total_tests)
    passed = max(0, min(passed, total_tests))
    failed = total_tests - passed
    return make_test_metrics(
        total_tests=total_tests,
        passed=passed,
        failed=failed,
        skipped=0,
        coverage=None,
        status="passing" if failed == 0 and total_tests > 0 else "failing",
    )


def make_max_boundary_metrics() -> dict[str, Any]:
    """Cria métricas nos limites máximos permitidos pelo schema.

    Returns:
        Dict de métricas com totalTests=999999, duration=86400.0 e coverage=100.0.
    """
    return make_test_metrics(
        total_tests=999999,
        passed=999999,
        failed=0,
        skipped=0,
        duration=86400.0,
        coverage=100.0,
        status="passing",
    )


def make_min_boundary_metrics() -> dict[str, Any]:
    """Cria métricas nos limites mínimos permitidos pelo schema.

    Returns:
        Dict de métricas com todos os contadores zerados e coverage=0.0.
    """
    return make_test_metrics(
        total_tests=0,
        passed=0,
        failed=0,
        skipped=0,
        duration=0.0,
        coverage=0.0,
        last_run_at=None,
        status="unknown",
    )


# ---------------------------------------------------------------------------
# Relatórios pytest JSON
# ---------------------------------------------------------------------------


def make_pytest_report(
    *,
    total: int = 42,
    passed: int = 40,
    failed: int = 2,
    skipped: int = 0,
    duration: float = 12.34,
    exit_code: int = 1,
    include_tests: bool = False,
) -> dict[str, Any]:
    """Cria um relatório pytest JSON válido no formato do pytest-json-report.

    Args:
        total: Número total de testes coletados. Padrão: 42.
        passed: Número de testes que passaram. Padrão: 40.
        failed: Número de testes que falharam. Padrão: 2.
        skipped: Número de testes pulados. Padrão: 0.
        duration: Duração total da execução em segundos. Padrão: 12.34.
        exit_code: Exit code do pytest (0=sucesso, 1=falhas, >1=erro). Padrão: 1.
        include_tests: Se True, inclui lista de testes individuais. Padrão: False.

    Returns:
        Dict com a estrutura de relatório pytest-json-report.

    Example:
        >>> report = make_pytest_report(total=5, passed=5, failed=0, exit_code=0)
        >>> report["summary"]["passed"]
        5
    """
    report: dict[str, Any] = {
        "created": 1747144200.123456,
        "duration": round(duration, 2),
        "exitcode": exit_code,
        "root": "/home/runner/work/mini-projeto-tokemize/mini-projeto-tokemize",
        "environment": {
            "Python": "3.11.9",
            "Platform": "Linux-6.5.0-1025-azure-x86_64-with-glibc2.35",
            "Packages": {
                "pytest": "8.2.0",
                "pytest-json-report": "1.5.0",
                "hypothesis": "6.100.0",
            },
        },
        "summary": {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": total,
            "collected": total,
        },
    }

    if include_tests:
        report["tests"] = _make_test_entries(passed, failed, skipped)

    return report


def _make_test_entries(
    passed: int,
    failed: int,
    skipped: int,
) -> list[dict[str, Any]]:
    """Gera entradas individuais de teste para o relatório pytest.

    Args:
        passed: Número de entradas com outcome "passed".
        failed: Número de entradas com outcome "failed".
        skipped: Número de entradas com outcome "skipped".

    Returns:
        Lista de dicts representando testes individuais.
    """
    entries: list[dict[str, Any]] = []

    for i in range(passed):
        entries.append({
            "nodeid": f"tests/test_example.py::test_passed_{i}",
            "lineno": (i + 1) * 10,
            "outcome": "passed",
            "duration": round(0.05 + i * 0.01, 3),
        })

    for i in range(failed):
        entries.append({
            "nodeid": f"tests/test_example.py::test_failed_{i}",
            "lineno": (passed + i + 1) * 10,
            "outcome": "failed",
            "duration": round(0.10 + i * 0.01, 3),
            "call": {
                "longrepr": f"AssertionError: test_failed_{i} assertion error",
                "crash": {
                    "path": "tests/test_example.py",
                    "lineno": (passed + i + 1) * 10 + 5,
                    "message": f"AssertionError: test_failed_{i} assertion error",
                },
            },
        })

    for i in range(skipped):
        entries.append({
            "nodeid": f"tests/test_example.py::test_skipped_{i}",
            "lineno": (passed + failed + i + 1) * 10,
            "outcome": "skipped",
            "duration": 0.001,
        })

    return entries


def make_empty_pytest_report() -> dict[str, Any]:
    """Cria um relatório pytest para uma execução sem testes coletados.

    Returns:
        Dict de relatório pytest com total=0 e exit_code=0.
    """
    return make_pytest_report(
        total=0,
        passed=0,
        failed=0,
        skipped=0,
        duration=0.0,
        exit_code=0,
    )


def make_all_passed_pytest_report(total: int = 10) -> dict[str, Any]:
    """Cria um relatório pytest onde todos os testes passaram.

    Args:
        total: Número total de testes. Padrão: 10.

    Returns:
        Dict de relatório pytest com passed=total e exit_code=0.
    """
    return make_pytest_report(
        total=total,
        passed=total,
        failed=0,
        skipped=0,
        duration=round(total * 0.5, 2),
        exit_code=0,
    )


def make_all_skipped_pytest_report(total: int = 5) -> dict[str, Any]:
    """Cria um relatório pytest onde todos os testes foram pulados.

    Args:
        total: Número de testes pulados. Padrão: 5.

    Returns:
        Dict de relatório pytest com skipped=total e exit_code=0.
    """
    return make_pytest_report(
        total=total,
        passed=0,
        failed=0,
        skipped=total,
        duration=0.10,
        exit_code=0,
    )


def make_error_pytest_report() -> dict[str, Any]:
    """Cria um relatório pytest representando erro de execução (exit code > 1).

    Returns:
        Dict de relatório pytest com exit_code=2 e summary zerado.
    """
    return make_pytest_report(
        total=0,
        passed=0,
        failed=0,
        skipped=0,
        duration=0.0,
        exit_code=2,
    )


# ---------------------------------------------------------------------------
# Relatórios de cobertura JSON
# ---------------------------------------------------------------------------


def make_coverage_report(
    *,
    percent_covered: float = 85.0,
    num_statements: int = 1000,
    covered_lines: int | None = None,
    missing_lines: int | None = None,
) -> dict[str, Any]:
    """Cria um relatório de cobertura JSON válido no formato do coverage.py.

    Args:
        percent_covered: Porcentagem de cobertura total. Padrão: 85.0.
        num_statements: Número total de statements. Padrão: 1000.
        covered_lines: Linhas cobertas. Calculado automaticamente se None.
        missing_lines: Linhas não cobertas. Calculado automaticamente se None.

    Returns:
        Dict com a estrutura de relatório coverage.py JSON.

    Example:
        >>> report = make_coverage_report(percent_covered=90.0)
        >>> report["totals"]["percent_covered"]
        90.0
    """
    if covered_lines is None:
        covered_lines = int(num_statements * percent_covered / 100)
    if missing_lines is None:
        missing_lines = num_statements - covered_lines

    return {
        "meta": {
            "version": "7.4.4",
            "timestamp": "2026-05-13T14:30:00.000000",
            "branch_coverage": False,
            "show_contexts": False,
        },
        "totals": {
            "covered_lines": covered_lines,
            "num_statements": num_statements,
            "percent_covered": round(percent_covered, 2),
            "percent_covered_display": f"{int(percent_covered)}%",
            "missing_lines": missing_lines,
            "excluded_lines": 0,
        },
        "files": {},
    }


def make_full_coverage_report() -> dict[str, Any]:
    """Cria um relatório de cobertura com 100% de cobertura.

    Returns:
        Dict de relatório de cobertura com percent_covered=100.0.
    """
    return make_coverage_report(
        percent_covered=100.0,
        num_statements=500,
        covered_lines=500,
        missing_lines=0,
    )


def make_zero_coverage_report() -> dict[str, Any]:
    """Cria um relatório de cobertura com 0% de cobertura.

    Returns:
        Dict de relatório de cobertura com percent_covered=0.0.
    """
    return make_coverage_report(
        percent_covered=0.0,
        num_statements=500,
        covered_lines=0,
        missing_lines=500,
    )


def make_malformed_coverage_report() -> dict[str, Any]:
    """Cria um relatório de cobertura malformado (sem campo 'totals').

    Usado para testar o tratamento de erros quando o relatório está corrompido.

    Returns:
        Dict sem a chave "totals" esperada pelo coletor de métricas.
    """
    return {
        "meta": {
            "version": "7.4.4",
            "timestamp": "2026-05-13T14:30:00.000000",
        },
        # "totals" ausente intencionalmente para simular relatório malformado
        "files": {},
    }


def make_malformed_pytest_report() -> dict[str, Any]:
    """Cria um relatório pytest malformado (sem campo 'summary').

    Usado para testar o tratamento de erros quando o relatório está corrompido.

    Returns:
        Dict sem a chave "summary" esperada pelo coletor de métricas.
    """
    return {
        "created": 1747144200.123456,
        "duration": 5.0,
        "exitcode": 0,
        # "summary" ausente intencionalmente para simular relatório malformado
        "tests": [],
    }
