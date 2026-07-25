import json
from pathlib import Path

from finfair import analyze_document, analyze_marketing, extract_pdf_pages


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


def test_conflicting_marketing_copy_is_flagged():
    result = analyze_document(_minimal_pages())
    result = analyze_marketing("保本稳赚，年化3.20%，随时可取。", _minimal_pages(), result)
    rule_ids = {item.rule_id for item in result.findings}

    assert {"R01", "R02", "R08"} <= rule_ids
    assert all(item.formal_evidence.page for item in result.findings)
