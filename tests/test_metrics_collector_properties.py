"""Property-based tests for the Test Metrics Collector.

Uses Hypothesis to verify universal properties of collect_test_metrics(),
validate_metrics(), and calculate_status() across arbitrary inputs.

Feature: test-pipeline-showcase
Design Properties: 1, 2, 3, 5, 6, 7
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings, strategies as st

# ---------------------------------------------------------------------------
# Import path setup — script lives in .github/scripts/, not a package
# ---------------------------------------------------------------------------

_SCRIPTS_DIR = Path(__file__).parent.parent / ".github" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from collect_test_metrics import (  # noqa: E402
    calculate_status,
    collect_test_metrics,
    validate_metrics,
)


# ---------------------------------------------------------------------------
# Composite generators
# ---------------------------------------------------------------------------


@st.composite
def pytest_report_strategy(draw: st.DrawFn) -> dict:
    """Generate a valid pytest JSON report dict.

    Constraints:
    - total ∈ [0, 1000]
    - passed + failed + skipped == total (skipped fills the remainder)
    - duration ∈ [0.0, 3600.0]
    - exitcode ∈ {0, 1, 2}
    """
    total = draw(st.integers(min_value=0, max_value=1000))
    passed = draw(st.integers(min_value=0, max_value=total))
    remaining = total - passed
    failed = draw(st.integers(min_value=0, max_value=remaining))
    skipped = remaining - failed
    duration = draw(st.floats(min_value=0.0, max_value=3600.0, allow_nan=False, allow_infinity=False))
    exit_code = draw(st.sampled_from([0, 1, 2]))

    return {
        "created": 1747144200.0,
        "duration": duration,
        "exitcode": exit_code,
        "root": "/tmp/project",
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "collected": total,
        },
    }


@st.composite
def coverage_report_strategy(draw: st.DrawFn) -> dict:
    """Generate a valid coverage.py JSON report dict.

    Constraints:
    - percent_covered ∈ [0.0, 100.0]
    """
    percent = draw(st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False))
    return {
        "meta": {"version": "7.4.4"},
        "totals": {
            "percent_covered": percent,
            "num_statements": 1000,
            "covered_lines": int(percent * 10),
            "missing_lines": 1000 - int(percent * 10),
            "excluded_lines": 0,
        },
        "files": {},
    }


@st.composite
def valid_test_metrics_strategy(draw: st.DrawFn) -> dict:
    """Generate a valid test metrics dict respecting all field constraints.

    Constraints:
    - totalTests ∈ [0, 999999]
    - passed, failed, skipped ∈ [0, totalTests]
    - duration ∈ [0.0, 86400.0]
    - coverage ∈ [0.0, 100.0] | None
    - status ∈ {"passing", "failing", "unknown"}
    """
    total = draw(st.integers(min_value=0, max_value=999_999))
    passed = draw(st.integers(min_value=0, max_value=total))
    remaining = total - passed
    failed = draw(st.integers(min_value=0, max_value=remaining))
    skipped = remaining - failed
    duration = draw(st.floats(min_value=0.0, max_value=86_400.0, allow_nan=False, allow_infinity=False))
    coverage = draw(
        st.one_of(
            st.none(),
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        )
    )
    status = draw(st.sampled_from(["passing", "failing", "unknown"]))

    return {
        "totalTests": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration": duration,
        "coverage": coverage,
        "lastRunAt": None,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Property 1: Metrics Extraction Correctness
# ---------------------------------------------------------------------------

# Feature: test-pipeline-showcase, Property 1: Metrics Extraction Correctness
@given(
    pytest_report=pytest_report_strategy(),
    coverage_report=st.one_of(st.none(), coverage_report_strategy()),
)
@settings(max_examples=100)
def test_metrics_extraction_correctness(
    pytest_report: dict,
    coverage_report: dict | None,
) -> None:
    """For any valid pytest report and optional coverage report, collect_test_metrics()
    SHALL correctly extract all metric fields matching the source data.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.6**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Write pytest report to a temp file
        pytest_json_path = tmp_path / "pytest-report.json"
        pytest_json_path.write_text(json.dumps(pytest_report), encoding="utf-8")

        # Optionally write coverage report
        coverage_json_path: str | None = None
        if coverage_report is not None:
            cov_path = tmp_path / "coverage.json"
            cov_path.write_text(json.dumps(coverage_report), encoding="utf-8")
            coverage_json_path = str(cov_path)

        exit_code = pytest_report["exitcode"]
        result = collect_test_metrics(str(pytest_json_path), coverage_json_path, exit_code)

    summary = pytest_report["summary"]

    # totalTests, passed, failed, skipped must match source
    assert result["totalTests"] == summary["total"], (
        f"totalTests mismatch: expected {summary['total']}, got {result['totalTests']}"
    )
    assert result["passed"] == summary["passed"], (
        f"passed mismatch: expected {summary['passed']}, got {result['passed']}"
    )
    assert result["failed"] == summary["failed"], (
        f"failed mismatch: expected {summary['failed']}, got {result['failed']}"
    )
    assert result["skipped"] == summary["skipped"], (
        f"skipped mismatch: expected {summary['skipped']}, got {result['skipped']}"
    )

    # coverage must match source when provided
    if coverage_report is not None:
        expected_coverage = coverage_report["totals"]["percent_covered"]
        assert result["coverage"] is not None, "coverage should not be None when report is provided"
        assert abs(result["coverage"] - expected_coverage) < 1e-6, (
            f"coverage mismatch: expected {expected_coverage}, got {result['coverage']}"
        )
    else:
        assert result["coverage"] is None, "coverage should be None when no report is provided"

    assert result["duration"] == round(pytest_report["duration"], 2), (
        f"duration mismatch: expected {round(pytest_report['duration'], 2)}, got {result['duration']}"
    )
    assert result["status"] == calculate_status(summary["failed"], summary["total"], exit_code), (
        "status mismatch with calculate_status() rule"
    )
    last_run_at = result.get("lastRunAt")
    assert isinstance(last_run_at, str) and _ISO8601_UTC_RE.match(last_run_at), (
        f"lastRunAt={last_run_at!r} does not match ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ"
    )


# ---------------------------------------------------------------------------
# Property 2: Test Metrics Validation
# ---------------------------------------------------------------------------

# Feature: test-pipeline-showcase, Property 2: Test Metrics Validation
@given(metrics=valid_test_metrics_strategy())
@settings(max_examples=100)
def test_metrics_validation(metrics: dict) -> None:
    """For any test metrics object, validate_metrics() SHALL produce a result
    where all fields satisfy their spec constraints.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8**
    """
    result = validate_metrics(metrics)

    total = result["totalTests"]
    assert 0 <= total <= 999_999, f"totalTests out of range: {total}"

    assert 0 <= result["passed"] <= total, (
        f"passed={result['passed']} out of [0, totalTests={total}]"
    )
    assert 0 <= result["failed"] <= total, (
        f"failed={result['failed']} out of [0, totalTests={total}]"
    )
    assert 0 <= result["skipped"] <= total, (
        f"skipped={result['skipped']} out of [0, totalTests={total}]"
    )

    assert 0.0 <= result["duration"] <= 86_400.0, (
        f"duration={result['duration']} out of [0.0, 86400.0]"
    )

    if result["coverage"] is not None:
        assert 0.0 <= result["coverage"] <= 100.0, (
            f"coverage={result['coverage']} out of [0.0, 100.0]"
        )

    assert result["status"] in {"passing", "failing", "unknown"}, (
        f"status={result['status']!r} not in valid set"
    )


# ---------------------------------------------------------------------------
# Property 3: Status Calculation Correctness
# ---------------------------------------------------------------------------

# Feature: test-pipeline-showcase, Property 3: Status Calculation Correctness
@given(
    failed=st.integers(min_value=0, max_value=999_999),
    total_tests=st.integers(min_value=0, max_value=999_999),
    exit_code=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100)
def test_status_calculation_correctness(
    failed: int,
    total_tests: int,
    exit_code: int,
) -> None:
    """For any (failed, total_tests, exit_code) combination, calculate_status()
    SHALL return the correct status value.

    Rules:
    - exit_code > 1  → "unknown"
    - failed > 0     → "failing"
    - failed == 0 AND total_tests > 0 → "passing"
    - total_tests == 0 → "unknown"

    **Validates: Requirements 5.9, 5.10, 5.11**
    """
    status = calculate_status(failed, total_tests, exit_code)

    if exit_code > 1:
        assert status == "unknown", (
            f"exit_code={exit_code} > 1 should yield 'unknown', got {status!r}"
        )
    elif failed > 0:
        assert status == "failing", (
            f"failed={failed} > 0 should yield 'failing', got {status!r}"
        )
    elif total_tests > 0:
        assert status == "passing", (
            f"failed=0, total_tests={total_tests} > 0 should yield 'passing', got {status!r}"
        )
    else:
        # total_tests == 0 and exit_code <= 1 and failed == 0
        assert status == "unknown", (
            f"total_tests=0 should yield 'unknown', got {status!r}"
        )


# ---------------------------------------------------------------------------
# Property 7: Duration Precision
# ---------------------------------------------------------------------------

# Feature: test-pipeline-showcase, Property 7: Duration Precision
@given(
    duration=st.floats(min_value=0.0, max_value=86_400.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=100)
def test_duration_precision(duration: float) -> None:
    """For any float duration, after passing through validate_metrics(), the
    result['duration'] SHALL be rounded to exactly 2 decimal places.

    **Validates: Requirements 2.5**
    """
    metrics = {
        "totalTests": 1,
        "passed": 1,
        "failed": 0,
        "skipped": 0,
        "duration": duration,
        "coverage": None,
        "lastRunAt": None,
        "status": "passing",
    }
    result = validate_metrics(metrics)

    assert round(result["duration"], 2) == result["duration"], (
        f"duration={result['duration']} is not rounded to 2 decimal places"
    )


# ---------------------------------------------------------------------------
# Property 5: Timestamp ISO 8601 UTC Format
# ---------------------------------------------------------------------------

_ISO8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# Feature: test-pipeline-showcase, Property 5: Timestamp ISO 8601 UTC Format
@given(
    pytest_report=pytest_report_strategy(),
)
@settings(max_examples=100)
def test_timestamp_iso8601_utc_format(pytest_report: dict) -> None:
    """collect_test_metrics() SHALL always produce a lastRunAt value matching
    the ISO 8601 UTC format with second precision: YYYY-MM-DDTHH:MM:SSZ.

    **Validates: Requirements 4.4, 5.7**
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        pytest_json_path = Path(tmp_dir) / "pytest-report.json"
        pytest_json_path.write_text(json.dumps(pytest_report), encoding="utf-8")
        result = collect_test_metrics(str(pytest_json_path), None, pytest_report["exitcode"])

    last_run_at = result.get("lastRunAt")
    assert last_run_at is not None, "lastRunAt should not be None"
    assert isinstance(last_run_at, str), f"lastRunAt should be a string, got {type(last_run_at)}"
    assert _ISO8601_UTC_RE.match(last_run_at), (
        f"lastRunAt={last_run_at!r} does not match ISO 8601 UTC format YYYY-MM-DDTHH:MM:SSZ"
    )


# ---------------------------------------------------------------------------
# Property 6: JSON Serialization Round-Trip
# ---------------------------------------------------------------------------

# Feature: test-pipeline-showcase, Property 6: Test Metrics JSON Serialization Round-Trip
@given(metrics=valid_test_metrics_strategy())
@settings(max_examples=100)
def test_json_serialization_round_trip(metrics: dict) -> None:
    """For any valid test metrics dict, serializing to JSON and deserializing
    SHALL produce an equivalent object with all fields preserved and correctly typed.

    **Validates: Requirements 2.7, 8.2**
    """
    # Validate first so we have a well-formed metrics dict
    validated = validate_metrics(metrics)

    # Round-trip through JSON
    serialized = json.dumps(validated)
    deserialized = json.loads(serialized)

    # All keys must be preserved
    assert set(deserialized.keys()) == set(validated.keys()), (
        f"Keys changed after round-trip: {set(validated.keys())} → {set(deserialized.keys())}"
    )

    # Integer fields must remain integers
    for field in ("totalTests", "passed", "failed", "skipped"):
        assert isinstance(deserialized[field], int), (
            f"Field '{field}' should be int after round-trip, got {type(deserialized[field])}"
        )
        assert deserialized[field] == validated[field], (
            f"Field '{field}' value changed: {validated[field]} → {deserialized[field]}"
        )

    # duration must remain a number
    assert isinstance(deserialized["duration"], (int, float)), (
        f"duration should be numeric after round-trip, got {type(deserialized['duration'])}"
    )
    assert deserialized["duration"] == validated["duration"], (
        f"duration changed: {validated['duration']} → {deserialized['duration']}"
    )

    # coverage: None or float
    if validated["coverage"] is None:
        assert deserialized["coverage"] is None, (
            f"coverage should be None after round-trip, got {deserialized['coverage']!r}"
        )
    else:
        assert isinstance(deserialized["coverage"], (int, float)), (
            f"coverage should be numeric after round-trip, got {type(deserialized['coverage'])}"
        )
        assert abs(deserialized["coverage"] - validated["coverage"]) < 1e-9, (
            f"coverage changed: {validated['coverage']} → {deserialized['coverage']}"
        )

    # status must be a string and one of the valid values
    assert isinstance(deserialized["status"], str), (
        f"status should be str after round-trip, got {type(deserialized['status'])}"
    )
    assert deserialized["status"] == validated["status"], (
        f"status changed: {validated['status']!r} → {deserialized['status']!r}"
    )
