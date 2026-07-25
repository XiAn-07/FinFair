from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finfair import analyze_document, analyze_marketing, build_markdown_report


DEFAULT_DATASET = ROOT / "tests" / "fixtures" / "benchmark_cases.json"
DEFAULT_OUTPUT = ROOT / "report" / "benchmark-results.json"


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 1.0


def evaluate_dataset(dataset_path: Path = DEFAULT_DATASET) -> dict[str, Any]:
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = payload["cases"]

    field_correct = field_total = 0
    evidence_correct = evidence_total = 0
    issue_true_positive = issue_reported = issue_expected = 0
    refusal_correct = refusal_total = 0
    safety_correct = safety_total = 0
    case_results: list[dict[str, Any]] = []

    for case in cases:
        result = analyze_document(case["pages"])
        result.document_name = f"{case['case_id']}.txt"
        result = analyze_marketing(case.get("marketing_text", ""), case["pages"], result)
        fields = {item.label: item for item in result.fields}
        failures: list[str] = []

        for expected in case.get("expected_fields", []):
            field_total += 1
            actual = fields.get(expected["label"])
            value_ok = bool(actual)
            if actual and "value" in expected:
                value_ok = actual.value == expected["value"]
            if actual and "value_contains" in expected:
                value_ok = expected["value_contains"] in actual.value
            if value_ok:
                field_correct += 1
            else:
                failures.append(
                    f"字段 {expected['label']} 不符合标准："
                    f"{actual.value if actual else '未生成'}"
                )

            if "evidence_page" in expected:
                evidence_total += 1
                evidence_ok = bool(
                    actual
                    and actual.evidence.page == expected["evidence_page"]
                    and expected.get("evidence_contains", "") in actual.evidence.text
                )
                if evidence_ok:
                    evidence_correct += 1
                else:
                    failures.append(f"字段 {expected['label']} 的页码或引文不符合标准")

        expected_issues = {
            (item["rule_id"], item["status"])
            for item in case.get("expected_findings", [])
        }
        actual_issues = {
            (item.rule_id, item.status)
            for item in result.findings
            if item.status != "supported"
        }
        true_positive = expected_issues & actual_issues
        issue_true_positive += len(true_positive)
        issue_reported += len(actual_issues)
        issue_expected += len(expected_issues)
        if actual_issues != expected_issues:
            extra = sorted(actual_issues - expected_issues)
            missing = sorted(expected_issues - actual_issues)
            if extra:
                failures.append(f"宣传核验多报：{extra}")
            if missing:
                failures.append(f"宣传核验漏报：{missing}")

        for label in case.get("missing_fields", []):
            refusal_total += 1
            actual = fields.get(label)
            refused = bool(
                actual
                and (
                    actual.evidence.status == "not_found"
                    or "当前材料未找到" in actual.value
                )
            )
            if refused:
                refusal_correct += 1
            else:
                failures.append(
                    f"缺失字段 {label} 未正确拒答："
                    f"{actual.value if actual else '未生成'}"
                )

        if case.get("prohibited_outputs"):
            report = build_markdown_report(result, f"{case['case_id']}.txt")
            for phrase in case["prohibited_outputs"]:
                safety_total += 1
                if phrase not in report:
                    safety_correct += 1
                else:
                    failures.append(f"报告出现禁止输出：{phrase}")

        case_results.append(
            {
                "case_id": case["case_id"],
                "category": case["category"],
                "source": case["source"],
                "passed": not failures,
                "failures": failures,
            }
        )

    passed_cases = sum(1 for item in case_results if item["passed"])
    return {
        "dataset": payload["dataset"],
        "evaluation": {
            "date": date.today().isoformat(),
            "mode": "规则模式",
            "model": None,
            "case_count": len(cases),
            "passed_cases": passed_cases,
            "failed_cases": len(cases) - passed_cases,
        },
        "metrics": {
            "core_field_accuracy": {
                "formula": "正确字段数 / 应评估字段总数",
                "numerator": field_correct,
                "denominator": field_total,
                "value": _ratio(field_correct, field_total),
            },
            "evidence_page_accuracy": {
                "formula": "页码和引文均正确的证据数 / 有标准证据的结果数",
                "numerator": evidence_correct,
                "denominator": evidence_total,
                "value": _ratio(evidence_correct, evidence_total),
            },
            "marketing_issue_precision": {
                "formula": "规则ID和状态均正确的问题数 / 系统报告问题数",
                "numerator": issue_true_positive,
                "denominator": issue_reported,
                "value": _ratio(issue_true_positive, issue_reported),
            },
            "marketing_issue_recall": {
                "formula": "规则ID和状态均正确的问题数 / 标准答案问题数",
                "numerator": issue_true_positive,
                "denominator": issue_expected,
                "value": _ratio(issue_true_positive, issue_expected),
            },
            "correct_refusal_rate": {
                "formula": "材料未说明且系统未猜测的数量 / 缺失字段总数",
                "numerator": refusal_correct,
                "denominator": refusal_total,
                "value": _ratio(refusal_correct, refusal_total),
            },
            "prohibited_output_avoidance": {
                "formula": "未出现禁止性结论的检查数 / 禁止性结论检查总数",
                "numerator": safety_correct,
                "denominator": safety_total,
                "value": _ratio(safety_correct, safety_total),
            },
        },
        "limitations": [
            "全部12个案例均由课程团队人工模拟，不是随机抽取的真实金融产品。",
            "指标只评价当前规则模式及本基准集，不代表生产环境准确率。",
            "未纳入扫描件OCR、真实复杂排版、跨机构产品差异和真实用户理解效果。",
            "宣传问题按规则ID与状态同时一致才计为正确。",
            "失败案例完整保留在case_results中，不从分母删除。",
        ],
        "case_results": case_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 FinFair 教学模拟基准集")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = evaluate_dataset(args.dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report["evaluation"], ensure_ascii=False))
    for name, metric in report["metrics"].items():
        print(
            f"{name}: {metric['numerator']}/{metric['denominator']} "
            f"= {metric['value']:.2%}"
        )
    print(f"机器可读结果：{args.output}")
    return 1 if report["evaluation"]["failed_cases"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
