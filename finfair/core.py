from __future__ import annotations

import io
import re
from dataclasses import asdict, dataclass, field
from typing import Iterable


@dataclass
class Evidence:
    page: int | None
    text: str
    status: str = "supported"


@dataclass
class FieldResult:
    label: str
    value: str
    plain_language: str
    evidence: Evidence
    severity: str = "info"


@dataclass
class MarketingFinding:
    rule_id: str
    title: str
    severity: str
    explanation: str
    marketing_text: str | None
    formal_evidence: Evidence


@dataclass
class AgentInsight:
    insight_id: str
    title: str
    conclusion: str
    plain_language: str
    severity: str
    evidence: Evidence
    verification_status: str = "supported"


@dataclass
class AgentRunInfo:
    enabled: bool = False
    model: str = ""
    analyzer_called: bool = False
    verifier_called: bool = False
    accepted_count: int = 0
    rejected_count: int = 0
    status: str = "规则模式"
    error: str | None = None
    rejection_reasons: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    fields: list[FieldResult] = field(default_factory=list)
    risks: list[FieldResult] = field(default_factory=list)
    findings: list[MarketingFinding] = field(default_factory=list)
    agent_insights: list[AgentInsight] = field(default_factory=list)
    agent_run: AgentRunInfo = field(default_factory=AgentRunInfo)
    questions: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    page_count: int = 0
    engine: str = "规则审查引擎 v0.1"

    def to_dict(self) -> dict:
        return asdict(self)


def extract_pdf_pages(file_bytes: bytes) -> list[str]:
    """Extract page text while preserving page boundaries."""
    try:
        import pdfplumber
    except ImportError as exc:
        raise RuntimeError("缺少 pdfplumber，请运行 pip install -r requirements.txt") from exc

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            pages.append(_normalize(text))
    if not pages or not any(pages):
        raise ValueError("PDF中没有提取到可用文字；扫描件需要OCR，当前MVP暂未启用。")
    return pages


def _normalize(text: str) -> str:
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _all_lines(pages: list[str]) -> Iterable[tuple[int, str]]:
    for page_no, text in enumerate(pages, start=1):
        for line in text.splitlines():
            line = line.strip()
            if line:
                yield page_no, line


def _find_line(
    pages: list[str],
    patterns: list[str],
    *,
    default: str = "当前材料未找到",
) -> Evidence:
    # 按模式优先级搜索，避免前面的泛化标题抢先匹配后面的完整证据句。
    for pattern in patterns:
        for page_no, line in _all_lines(pages):
            if re.search(pattern, line, flags=re.I):
                return Evidence(page_no, line)
    return Evidence(None, default, "not_found")


def _find_passage(
    pages: list[str],
    patterns: list[str],
    *,
    max_lines: int = 4,
    default: str = "当前材料未找到",
) -> Evidence:
    """Find evidence and join PDF-wrapped continuation lines into a readable passage."""
    for pattern in patterns:
        for page_no, page in enumerate(pages, start=1):
            lines = [line.strip() for line in page.splitlines() if line.strip()]
            for index, line in enumerate(lines):
                if not re.search(pattern, line, flags=re.I):
                    continue
                passage = [line]
                if re.match(
                    r"^(?:第[一二三四五六七八九十]+部分|[一二三四五六七八九十]+、|\d+[.、])",
                    passage[0],
                ) and not re.search(r"[：:。！？；]$", passage[0]):
                    passage[0] += "："
                while (
                    len(passage) < max_lines
                    and index + len(passage) < len(lines)
                    and not re.search(r"[。！？；]$", passage[-1])
                ):
                    next_line = lines[index + len(passage)]
                    if next_line.startswith("|") or re.match(
                        r"^(?:第[一二三四五六七八九十]+部分|[一二三四五六七八九十]+、|\d+[.、])",
                        next_line,
                    ):
                        break
                    passage.append(next_line)
                return Evidence(page_no, "".join(passage))
    return Evidence(None, default, "not_found")


def _extract_value(line: str, label_patterns: list[str], fallback: str) -> str:
    value = line
    for pattern in label_patterns:
        value = re.sub(pattern, "", value, count=1, flags=re.I)
    value = value.strip(" ：:|")
    return value or fallback


def _field(
    label: str,
    value: str,
    plain: str,
    evidence: Evidence,
    severity: str = "info",
) -> FieldResult:
    return FieldResult(label, value, plain, evidence, severity)


def analyze_document(pages: list[str]) -> AnalysisResult:
    result = AnalysisResult(page_count=len(pages))

    name_ev = _find_line(pages, [r"产品名称"])
    name = _extract_value(name_ev.text, [r"产品名称"], "当前材料未找到")
    if name == "当前材料未找到":
        title_ev = _find_line(pages, [r"理财产品说明书"])
        name_ev = title_ev
        name = re.sub(r"说明书.*$", "", title_ev.text).strip() or "当前材料未找到"
    result.fields.append(_field("产品名称", name, "这是本次分析对应的产品。", name_ev))

    type_ev = _find_line(pages, [r"产品类型", r"非保本浮动收益"])
    non_guaranteed_ev = _find_passage(
        pages,
        [
            r"不保证本金和收益",
            r"非保本浮动收益",
            r"可能损失部分或全部本金",
        ],
    )
    if non_guaranteed_ev.status == "supported":
        principal_value = "不保本，本金可能发生损失"
        principal_plain = "这不是保本产品。极端情况下，投入的本金可能部分或全部损失。"
        principal_severity = "high"
    else:
        principal_value = "当前材料未找到明确的保本结论"
        principal_plain = "不能因为材料中暂时没找到风险表述，就推断本金安全，请人工核对。"
        principal_severity = "review"
    result.fields.append(
        _field(
            "本金保障",
            principal_value,
            principal_plain,
            non_guaranteed_ev,
            principal_severity,
        )
    )

    benchmark_ev = _find_line(pages, [r"业绩比较基准.*\d+(?:\.\d+)?%"])
    if benchmark_ev.status == "not_found":
        benchmark_ev = _find_line(pages, [r"业绩比较基准"])
    benchmark_match = re.search(r"\d+(?:\.\d+)?%", benchmark_ev.text)
    benchmark = benchmark_match.group(0) if benchmark_match else "当前材料未找到"
    result.fields.append(
        _field(
            "业绩比较基准",
            benchmark,
            "业绩比较基准用于投资管理和业绩评价，不等于承诺收益或实际到手收益。",
            benchmark_ev,
            "medium",
        )
    )

    term_ev = _find_line(pages, [r"产品期限"])
    term_match = re.search(r"\d+\s*天", term_ev.text)
    term = re.sub(r"\s+", "", term_match.group(0)) if term_match else "当前材料未找到"
    result.fields.append(
        _field(
            "产品期限",
            term,
            "资金需要按产品约定持有，期间能否退出还要查看赎回规则。",
            term_ev,
        )
    )

    redemption_ev = _find_passage(
        pages,
        [
            r"不开放投资者主动申购或赎回",
            r"不能.*提前取回",
            r"不得提前赎回",
            r"封闭期.*赎回",
        ],
    )
    redemption = (
        "存续期内原则上不能主动赎回"
        if redemption_ev.status == "supported"
        else "当前材料未找到明确的提前赎回规则"
    )
    result.fields.append(
        _field(
            "提前退出",
            redemption,
            "如果临时需要资金，可能无法提前取回本金。",
            redemption_ev,
            "high" if redemption_ev.status == "supported" else "review",
        )
    )

    fee_patterns = [
        ("固定管理费", r"固定管理费.*?(\d+(?:\.\d+)?%/年)"),
        ("托管费", r"托管费.*?(\d+(?:\.\d+)?%/年)"),
        ("销售服务费", r"销售服务费.*?(\d+(?:\.\d+)?%/年)"),
    ]
    for fee_name, pattern in fee_patterns:
        ev = _find_line(pages, [pattern, fee_name])
        match = re.search(r"\d+(?:\.\d+)?%/年", ev.text)
        value = match.group(0) if match else "当前材料未找到"
        result.fields.append(
            _field(
                fee_name,
                value,
                "该费用从产品财产中计提，会降低投资者最终获得的实际收益。",
                ev,
                "medium",
            )
        )

    risk_specs = [
        ("市场风险", [r"市场风险"], "市场利率和资产价格变化可能导致产品净值下跌。"),
        ("信用风险", [r"信用风险"], "融资主体或交易对手违约可能导致产品损失。"),
        ("流动性风险", [r"流动性风险"], "底层资产无法及时变现时，可能延迟兑付或提前终止。"),
        ("估值风险", [r"估值风险"], "估值结果可能与资产最终变现价值不同。"),
        ("信息传递风险", [r"信息传递风险"], "未及时查看公告可能错过重要产品信息。"),
    ]
    for label, patterns, plain in risk_specs:
        ev = _find_passage(pages, patterns, max_lines=3)
        if ev.status == "supported":
            result.risks.append(_field(label, "说明书已披露", plain, ev, "medium"))

    worst_ev = _find_passage(
        pages,
        [r"损失部分或全部本金.*资金到账时间", r"最不利情形"],
    )
    result.risks.insert(
        0,
        _field(
            "最不利情形",
            "可能损失部分或全部本金，到账也可能延迟"
            if worst_ev.status == "supported"
            else "当前材料未找到明确的最不利情形",
            "不要根据业绩比较基准推断本金安全或最低收益。",
            worst_ev,
            "high" if worst_ev.status == "supported" else "review",
        ),
    )

    if type_ev.status == "not_found":
        result.limitations.append("没有可靠识别产品类型，请人工核对。")
    if any(item.evidence.status == "not_found" for item in result.fields):
        result.limitations.append("部分字段在当前材料中未找到，不代表相关条件一定不存在。")
    result.limitations.extend(
        [
            "当前MVP只解析包含可复制文字的PDF，扫描件需要OCR。",
            "分析结果仅用于教学演示和信息辅助，不构成投资建议或正式适当性评估。",
        ]
    )
    result.questions = [
        "业绩比较基准是否等于保证收益？",
        "在什么情况下可能损失本金？",
        "产品存续期内能否提前赎回？",
        "除已列费用外，是否还存在交易费用或税费？",
        "产品到期后资金最晚何时到账？",
        "发生底层资产违约或无法变现时如何处理？",
    ]
    return result


def analyze_marketing(
    marketing_text: str,
    pages: list[str],
    result: AnalysisResult,
) -> AnalysisResult:
    text = _normalize(marketing_text)
    if not text:
        return result

    benchmark_ev = _find_passage(
        pages, [r"业绩比较基准.*不代表", r"业绩比较基准"], max_lines=4
    )
    non_guaranteed_ev = _find_passage(
        pages, [r"不保证本金和收益", r"非保本浮动收益"], max_lines=4
    )
    redemption_ev = _find_passage(
        pages, [r"不开放投资者主动申购或赎回", r"不能.*提前取回"], max_lines=4
    )
    fee_ev = _find_line(pages, [r"固定管理费"])
    worst_ev = _find_passage(
        pages, [r"损失部分或全部本金.*资金到账时间", r"最不利情形"], max_lines=4
    )

    benchmark_number = None
    for line in text.splitlines():
        if re.search(r"年化\s*\d+(?:\.\d+)?%", line) and "业绩比较基准" not in line:
            benchmark_number = line.strip()
            break
    if benchmark_number:
        result.findings.append(
            MarketingFinding(
                "R02",
                "业绩比较基准可能被表达成确定收益",
                "red",
                "宣传直接使用“年化”数字，却没有同时说明这是业绩比较基准且不代表实际收益。",
                benchmark_number,
                benchmark_ev,
            )
        )

    absolute_terms = [
        term
        for term in ["稳赚", "稳稳拿", "保本", "零风险", "确定收益", "安心增值", "稳健增值"]
        if term in text
    ]
    if absolute_terms:
        result.findings.append(
            MarketingFinding(
                "R08",
                "存在容易形成确定性预期的表达",
                "orange",
                "这些表达可能弱化净值波动和本金损失风险，需要改成审慎、完整的风险收益表述。",
                "、".join(absolute_terms),
                non_guaranteed_ev,
            )
        )

    has_non_guarantee = bool(re.search(r"非保本|不保证本金|本金可能.*损失", text))
    if not has_non_guarantee:
        result.findings.append(
            MarketingFinding(
                "R01",
                "未明确披露产品不保本",
                "red",
                "笼统的“市场有风险”不能替代对本金损失可能性的明确说明。",
                None,
                non_guaranteed_ev,
            )
        )

    has_redemption_limit = bool(re.search(r"不可赎回|不能提前|不开放.*赎回|封闭期", text))
    if not has_redemption_limit:
        result.findings.append(
            MarketingFinding(
                "R04",
                "未明确披露提前赎回限制",
                "orange",
                "消费者可能不知道临时需要资金时无法提前取回本金。",
                None,
                redemption_ev,
            )
        )

    has_fees = bool(re.search(r"管理费|托管费|销售服务费|费用", text))
    if not has_fees:
        result.findings.append(
            MarketingFinding(
                "R06",
                "未披露产品费用",
                "orange",
                "费用会影响实际收益，宣传材料至少应提示用户查看完整费用安排。",
                None,
                fee_ev,
            )
        )

    has_worst_case = bool(re.search(r"损失.*本金|延迟兑付|提前终止|最不利", text))
    if not has_worst_case:
        result.findings.append(
            MarketingFinding(
                "R10",
                "未说明最不利情形",
                "orange",
                "宣传材料没有说明本金损失和到账延迟等可能显著影响用户决定的情形。",
                None,
                worst_ev,
            )
        )
    return result


def build_markdown_report(result: AnalysisResult, document_name: str) -> str:
    lines = [
        "# 金融产品公平说明书",
        "",
        f"> 分析文件：{document_name}",
        f"> 分析引擎：{result.engine}",
        "> 用途：教学演示，不构成投资建议或正式适当性评估。",
        "",
        "## 30秒看懂产品",
        "",
    ]
    for item in result.fields:
        page = f"第{item.evidence.page}页" if item.evidence.page else "未定位"
        lines.extend(
            [
                f"### {item.label}：{item.value}",
                "",
                item.plain_language,
                "",
                f"- 证据位置：{page}",
                f"- 原文：{item.evidence.text}",
                "",
            ]
        )
    lines.extend(["## 主要风险", ""])
    for item in result.risks:
        page = f"第{item.evidence.page}页" if item.evidence.page else "未定位"
        lines.extend(
            [
                f"- **{item.label}**：{item.value}（{page}）",
                f"  - {item.plain_language}",
            ]
        )
    lines.extend(["", "## 宣传材料一致性检查", ""])
    if result.findings:
        for finding in result.findings:
            page = (
                f"第{finding.formal_evidence.page}页"
                if finding.formal_evidence.page
                else "未定位"
            )
            lines.extend(
                [
                    f"### [{finding.severity.upper()}] {finding.title}",
                    "",
                    finding.explanation,
                    "",
                    f"- 宣传原文：{finding.marketing_text or '宣传材料未披露'}",
                    f"- 正式文件证据（{page}）：{finding.formal_evidence.text}",
                    "",
                ]
            )
    else:
        lines.append("未提交宣传材料，或当前规则未发现明显差异。")
    lines.extend(["", "## 大模型语义增强", ""])
    if result.agent_run.enabled and result.agent_insights:
        lines.append(
            f"> 模型：{result.agent_run.model}；"
            f"已通过证据核验 {result.agent_run.accepted_count} 项。"
        )
        lines.append("")
        for insight in result.agent_insights:
            page = f"第{insight.evidence.page}页" if insight.evidence.page else "未定位"
            lines.extend(
                [
                    f"### {insight.title}",
                    "",
                    insight.conclusion,
                    "",
                    insight.plain_language,
                    "",
                    f"- 核验状态：{insight.verification_status}",
                    f"- 原文证据（{page}）：{insight.evidence.text}",
                    "",
                ]
            )
    elif result.agent_run.enabled:
        lines.append("大模型增强已运行，但没有产生通过双重证据核验的新洞察。")
    else:
        lines.append("本次使用规则模式，未启用大模型语义增强。")
    lines.extend(["", "## 购买前必须确认的问题", ""])
    lines.extend([f"{i}. {q}" for i, q in enumerate(result.questions, start=1)])
    lines.extend(["", "## 局限与免责声明", ""])
    lines.extend([f"- {item}" for item in result.limitations])
    return "\n".join(lines)
