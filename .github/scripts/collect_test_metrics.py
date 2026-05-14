"""
Test Metrics Collector for CI/CD Pipeline.

Extracts test metrics from pytest JSON report and coverage JSON report,
then writes a structured test-metrics.json to /tmp/.

Usage:
    python .github/scripts/collect_test_metrics.py \
        --pytest-json pytest-report.json \
        --coverage-json coverage.json \
        --exit-code 0
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("TestMetricsCollector")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OUTPUT_PATH = "/tmp/test-metrics.json"
VALID_STATUSES = {"passing", "failing", "unknown"}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _clamp(value: float, min_value: float, max_value: float) -> float:
    """Return *value* clamped to [min_value, max_value].

    Args:
        value: The value to clamp.
        min_value: Lower bound (inclusive).
        max_value: Upper bound (inclusive).

    Returns:
        The clamped value.
    """
    return max(min_value, min(max_value, value))


def calculate_status(failed: int, total_tests: int, exit_code: int) -> str:
    """Determine the test run status from counts and exit code.

    Args:
        failed: Number of failed tests.
        total_tests: Total number of tests collected.
        exit_code: pytest exit code (0 = all passed, 1 = some failed, >1 = error).

    Returns:
        One of ``"passing"``, ``"failing"``, or ``"unknown"``.
    """
    if exit_code > 1:
        logger.warning(
            "pytest exit code %d indicates an execution error — status set to 'unknown'",
            exit_code,
        )
        return "unknown"

    if failed > 0:
        return "failing"

    if total_tests > 0:
        return "passing"

    return "unknown"


def validate_metrics(metrics: dict) -> dict:
    """Validate and sanitise a metrics dict, applying safe defaults for out-of-range values.

    Args:
        metrics: Raw metrics dictionary to validate.

    Returns:
        A new dictionary with all fields clamped to their valid ranges.
    """
    total = int(_clamp(metrics.get("totalTests", 0), 0, 999_999))
    passed = int(_clamp(metrics.get("passed", 0), 0, total))
    failed = int(_clamp(metrics.get("failed", 0), 0, total))
    skipped = int(_clamp(metrics.get("skipped", 0), 0, total))
    duration = round(float(_clamp(metrics.get("duration", 0.0), 0.0, 86_400.0)), 2)

    raw_coverage = metrics.get("coverage")
    if raw_coverage is None:
        coverage = None
    else:
        try:
            coverage = float(_clamp(float(raw_coverage), 0.0, 100.0))
        except (TypeError, ValueError):
            logger.warning("Invalid coverage value '%s', setting to None", raw_coverage)
            coverage = None

    last_run_at = metrics.get("lastRunAt")

    status = metrics.get("status", "unknown")
    if status not in VALID_STATUSES:
        logger.warning("Invalid status '%s', defaulting to 'unknown'", status)
        status = "unknown"

    return {
        "totalTests": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
        "coverage": coverage,
        "lastRunAt": last_run_at,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Report parsers
# ---------------------------------------------------------------------------


def _parse_pytest_report(pytest_json_path: str) -> dict:
    """Parse a pytest JSON report and return raw metric values.

    Args:
        pytest_json_path: Path to the pytest JSON report file.

    Returns:
        Dictionary with keys: ``total``, ``passed``, ``failed``, ``skipped``,
        ``duration``.  All values default to 0 / 0.0 on error.
    """
    defaults = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "duration": 0.0}

    try:
        with open(pytest_json_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.error("pytest report not found: %s", pytest_json_path)
        return defaults
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse pytest report '%s': %s", pytest_json_path, exc)
        return defaults

    try:
        summary = data["summary"]
        total = int(summary.get("total", 0))
        passed = int(summary.get("passed", 0))
        failed = int(summary.get("failed", 0))
        skipped = int(summary.get("skipped", 0))
    except KeyError as exc:
        logger.warning("Missing key in pytest report summary: %s — using defaults", exc)
        total = passed = failed = skipped = 0

    try:
        duration = float(data.get("duration", 0.0))
    except (TypeError, ValueError):
        logger.warning("Invalid duration in pytest report, defaulting to 0.0")
        duration = 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
    }


def _parse_coverage_report(coverage_json_path: Optional[str]) -> Optional[float]:
    """Parse a coverage JSON report and return the total coverage percentage.

    Args:
        coverage_json_path: Path to the coverage JSON report, or ``None`` if
            coverage was not generated.

    Returns:
        Coverage percentage as a float, or ``None`` if unavailable.
    """
    if not coverage_json_path:
        logger.info("No coverage report path provided — coverage will be null")
        return None

    try:
        with open(coverage_json_path, encoding="utf-8") as fh:
            data = json.load(fh)
        percent = float(data["totals"]["percent_covered"])
        logger.info("Coverage extracted: %.2f%%", percent)
        return percent
    except FileNotFoundError:
        logger.warning("Coverage report not found: %s — coverage will be null", coverage_json_path)
        return None
    except json.JSONDecodeError as exc:
        logger.warning(
            "Failed to parse coverage report '%s': %s — coverage will be null",
            coverage_json_path,
            exc,
        )
        return None
    except KeyError as exc:
        logger.warning(
            "Missing key in coverage report (%s): %s — coverage will be null",
            coverage_json_path,
            exc,
        )
        return None


# ---------------------------------------------------------------------------
# Main collector
# ---------------------------------------------------------------------------


def collect_test_metrics(
    pytest_json_path: str,
    coverage_json_path: Optional[str],
    pytest_exit_code: int,
) -> dict:
    """Collect test metrics from pytest and coverage reports.

    Reads the pytest JSON report and (optionally) the coverage JSON report,
    computes the run status, and writes the result to ``/tmp/test-metrics.json``.

    Args:
        pytest_json_path: Path to the pytest JSON report (``--json-report`` output).
        coverage_json_path: Path to the coverage JSON report (``coverage.json``),
            or ``None`` / empty string if coverage was not generated.
        pytest_exit_code: Exit code returned by pytest.
            0 = all tests passed, 1 = some tests failed, >1 = execution error.

    Returns:
        Dictionary with the following structure::

            {
                "totalTests": int,
                "passed": int,
                "failed": int,
                "skipped": int,
                "duration": float,
                "coverage": float | None,
                "lastRunAt": str,   # ISO 8601 UTC, second precision
                "status": str       # "passing" | "failing" | "unknown"
            }
    """
    logger.info(
        "Collecting test metrics — pytest_json=%s, coverage_json=%s, exit_code=%d",
        pytest_json_path,
        coverage_json_path,
        pytest_exit_code,
    )

    # --- Parse reports -------------------------------------------------------
    pytest_data = _parse_pytest_report(pytest_json_path)
    coverage = _parse_coverage_report(coverage_json_path or None)

    # --- Build raw metrics ---------------------------------------------------
    total_tests = pytest_data["total"]
    passed = pytest_data["passed"]
    failed = pytest_data["failed"]
    skipped = pytest_data["skipped"]
    duration = round(pytest_data["duration"], 2)

    status = calculate_status(failed, total_tests, pytest_exit_code)
    last_run_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    raw_metrics = {
        "totalTests": total_tests,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
        "coverage": coverage,
        "lastRunAt": last_run_at,
        "status": status,
    }

    # --- Validate and sanitise -----------------------------------------------
    metrics = validate_metrics(raw_metrics)

    # --- Write output --------------------------------------------------------
    output_path = Path(OUTPUT_PATH)
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2)
        logger.info(
            "Metrics written to %s — %d tests, %d passed, status=%s",
            OUTPUT_PATH,
            metrics["totalTests"],
            metrics["passed"],
            metrics["status"],
        )
    except OSError as exc:
        logger.error("Failed to write metrics to %s: %s", OUTPUT_PATH, exc)

    return metrics


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured :class:`argparse.ArgumentParser` instance.
    """
    parser = argparse.ArgumentParser(
        description="Collect test metrics from pytest and coverage JSON reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python .github/scripts/collect_test_metrics.py \\\n"
            "      --pytest-json pytest-report.json \\\n"
            "      --coverage-json coverage.json \\\n"
            "      --exit-code 0"
        ),
    )
    parser.add_argument(
        "--pytest-json",
        required=True,
        metavar="PATH",
        help="Path to the pytest JSON report file.",
    )
    parser.add_argument(
        "--coverage-json",
        default=None,
        metavar="PATH",
        help="Path to the coverage JSON report file (optional).",
    )
    parser.add_argument(
        "--exit-code",
        type=int,
        default=0,
        metavar="N",
        help="pytest exit code (0=passed, 1=failures, >1=error). Default: 0.",
    )
    return parser


def main() -> None:
    """CLI entry point for the test metrics collector."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    metrics = collect_test_metrics(
        pytest_json_path=args.pytest_json,
        coverage_json_path=args.coverage_json,
        pytest_exit_code=args.exit_code,
    )

    # Print summary to stdout for CI log visibility
    print(json.dumps(metrics, indent=2))

    # Exit with non-zero only for unexpected errors (exit_code > 1 is handled
    # as "unknown" status, not a script failure)
    sys.exit(0)


if __name__ == "__main__":
    main()
