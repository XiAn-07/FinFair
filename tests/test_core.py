import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from finfair import (
    analyze_document,
    analyze_marketing,
    build_markdown_report,
    extract_pdf_pages,
)
from finfair.report_export import build_docx_report, build_pdf_report


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sample_data" / "模拟理财产品说明书.pdf"
MARKETING = ROOT / "sample_data" / "模拟宣传文案.md"
GOLD = ROOT / "sample_data" / "人工标准答案.json"


def _minimal_pages() -> list[str]:
    return [
        (
            "产品名称 测试理财产品\n"
            "本产品为非保本浮动收益型净值型理财产品，不保证本金和收益。"
            "投资者可能损失部分或全部本金。\n"
            "业绩比较基准 3.20%（年化）\n"
            "产品期限 180天"
        ),
        (
            "产品存续期内原则上不开放投资者主动申购或赎回，"
            "投资者不能因临时资金需要而提前取回投资本金。\n"
            "固定管理费 0.30%/年\n托管费 0.03%/年\n销售服务费 0.10%/年"
        ),
        (
            "市场风险\n信用风险\n流动性风险\n估值风险\n信息传递风险\n"
            "最不利情形：投资者可能损失部分或全部本金，资金到账时间也可能延迟。"
        ),
    ]


def test_demo_case():
    pages = extract_pdf_pages(PDF.read_bytes())
    assert len(pages) == 4

    result = analyze_document(pages)
    visible_marketing = MARKETING.read_text(encoding="utf-8").split(
        "## 教学设计说明", 1
    )[0]
    result = analyze_marketing(visible_marketing, pages, result)

    fields = {item.label: item for item in result.fields}
    assert "不保本" in fields["本金保障"].value
    assert fields["业绩比较基准"].value == "3.20%"
    assert fields["产品期限"].value == "180天"
    assert "不能主动赎回" in fields["提前退出"].value
    assert fields["固定管理费"].value == "0.30%/年"
    assert fields["托管费"].value == "0.03%/年"
    assert fields["销售服务费"].value == "0.10%/年"
    assert fields["本金保障"].evidence.text.endswith("发生损失。")
    assert fields["提前退出"].evidence.text.endswith("提前取回投资本金。")

    rule_ids = {item.rule_id for item in result.findings}
    assert {"R01", "R02", "R04", "R06", "R08", "R10"} <= rule_ids
    assert all(item.evidence.page for item in result.fields)

    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    assert gold["principal_and_return"]["principal_guaranteed"]["value"] is False


def test_missing_fields_are_marked_for_review():
    result = analyze_document(["产品名称 信息不完整的测试产品"])
    fields = {item.label: item for item in result.fields}

    assert fields["本金保障"].evidence.status == "not_found"
    assert fields["业绩比较基准"].value == "当前材料未找到"
    assert fields["提前退出"].severity == "review"
    assert any("部分字段" in item for item in result.limitations)


def test_document_coverage_counts_empty_pages():
    pages = ["第一页文字", "", "第三页文字"]
    result = analyze_document(pages)

    assert result.page_count == 3
    assert result.extracted_char_count == len("第一页文字") + len("第三页文字")
    assert result.empty_page_count == 1
    assert any("1页未提取到文字" in item for item in result.limitations)


def test_all_empty_pdf_is_rejected(monkeypatch):
    class FakePDF:
        pages = [
            SimpleNamespace(extract_text=lambda **_kwargs: ""),
            SimpleNamespace(extract_text=lambda **_kwargs: None),
        ]

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setitem(
        sys.modules, "pdfplumber", SimpleNamespace(open=lambda *_args, **_kwargs: FakePDF())
    )
    with pytest.raises(ValueError, match="没有提取到可用文字"):
        extract_pdf_pages(b"fake-pdf")


def test_conflicting_marketing_copy_is_flagged():
    result = analyze_document(_minimal_pages())
    result = analyze_marketing("保本稳赚，年化3.20%，随时可取。", _minimal_pages(), result)
    findings = {item.rule_id: item for item in result.findings}

    assert findings["R01"].status == "omitted"
    assert findings["R02"].status == "conflicting"
    assert findings["R04"].status == "conflicting"
    assert findings["R08"].status == "conflicting"
    assert all(item.formal_evidence.page for item in result.findings)


def test_consistent_marketing_is_marked_supported():
    marketing = (
        "本产品不保本，本金可能损失部分或全部。\n"
        "业绩比较基准3.20%，不代表实际收益，也不保证收益。\n"
        "封闭期内不能提前赎回。\n"
        "产品收取固定管理费、托管费和销售服务费。\n"
        "最不利情形可能损失全部本金，资金到账也可能延迟。"
    )
    result = analyze_marketing(
        marketing, _minimal_pages(), analyze_document(_minimal_pages())
    )

    assert result.marketing_provided is True
    assert len(result.findings) == 6
    assert {item.status for item in result.findings} == {"supported"}


def test_omission_and_conflict_are_distinct():
    result = analyze_marketing(
        "年化3.20%，灵活取用。",
        _minimal_pages(),
        analyze_document(_minimal_pages()),
    )
    findings = {item.rule_id: item for item in result.findings}

    assert findings["R01"].status == "omitted"
    assert findings["R02"].status == "conflicting"
    assert findings["R04"].status == "conflicting"
    assert findings["R06"].status == "omitted"
    assert findings["R10"].status == "omitted"


def test_formal_document_missing_evidence_is_unclear():
    pages = ["产品名称 信息不足产品"]
    result = analyze_marketing("稳健产品，欢迎了解。", pages, analyze_document(pages))

    assert result.marketing_provided is True
    assert all(item.status == "unclear" for item in result.findings)
    assert all(item.formal_evidence.page is None for item in result.findings)


def test_no_marketing_input_has_distinct_state():
    result = analyze_marketing("", _minimal_pages(), analyze_document(_minimal_pages()))

    assert result.marketing_provided is False
    assert result.findings == []
    report = build_markdown_report(result, "测试.pdf")
    assert "未输入宣传材料" in report


def test_four_report_formats_include_same_comparison_status():
    result = analyze_marketing(
        "年化3.20%，随时可取。",
        _minimal_pages(),
        analyze_document(_minimal_pages()),
    )
    result.document_name = "测试.pdf"

    data = result.to_dict()
    markdown = build_markdown_report(result, "测试.pdf")
    assert any(item["status"] == "conflicting" for item in data["findings"])
    assert "核验状态：冲突" in markdown
    assert data["page_count"] == 3
    assert data["extracted_char_count"] > 0
    assert "文档覆盖：解析 3 页" in markdown
    assert "Agent 覆盖：未启用" in markdown

    __import__("pytest").importorskip("docx")
    __import__("pytest").importorskip("reportlab")
    docx_bytes = build_docx_report(result, "测试.pdf")
    pdf_bytes = build_pdf_report(result, "测试.pdf")

    assert len(docx_bytes) > 1_000
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1_000
