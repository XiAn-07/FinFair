import json
from pathlib import Path

import pytest

from scripts.run_benchmark import evaluate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tests" / "fixtures" / "benchmark_cases.json"
PAYLOAD = json.loads(DATASET.read_text(encoding="utf-8"))


def test_benchmark_has_required_case_structure():
    cases = PAYLOAD["cases"]
    assert len(cases) >= 12
    assert PAYLOAD["dataset"]["case_count"] == len(cases)
    assert all(case.get("source") for case in cases)
    assert all(case.get("category") for case in cases)
    assert all("expected_fields" in case for case in cases)
    assert all("expected_findings" in case for case in cases)


@pytest.mark.parametrize("case", PAYLOAD["cases"], ids=lambda case: case["case_id"])
def test_benchmark_case(case):
    one_case_dataset = {
        "dataset": {**PAYLOAD["dataset"], "case_count": 1},
        "cases": [case],
    }
    temp_path = ROOT / "tmp" / f"benchmark_{case['case_id']}.json"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_text(
        json.dumps(one_case_dataset, ensure_ascii=False), encoding="utf-8"
    )
    try:
        report = evaluate_dataset(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)

    assert report["evaluation"]["failed_cases"] == 0, report["case_results"][0][
        "failures"
    ]


def test_benchmark_metrics_keep_denominators_and_failures():
    report = evaluate_dataset(DATASET)

    assert report["evaluation"]["case_count"] == 12
    assert report["evaluation"]["passed_cases"] == 12
    assert report["evaluation"]["failed_cases"] == 0
    for metric in report["metrics"].values():
        assert "formula" in metric
        assert "numerator" in metric
        assert "denominator" in metric
        assert "value" in metric
    assert len(report["case_results"]) == 12
    assert report["limitations"]
