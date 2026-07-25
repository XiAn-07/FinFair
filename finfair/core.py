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
    status: str
    formal_plain_language: str
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
    protocol: str = ""
    analyzer_called: bool = False
    verifier_called: bool = False
    candidate_count: int = 0
    verifier_supported_count: int = 0
    gate_passed_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    status: str = "规则模式"
    stop_reason: str = "未启用 Agent"
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
    document_name: str = ""
    page_count: int = 0
    extracted_char_count: int = 0
    empty_page_count: int = 0
    agent_char_count: int = 0
    agent_truncated: bool = False
    analysis_mode: str = "规则模式"
    marketing_provided: bool = False
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
    result = AnalysisResult(
        page_count=len(pages),
        extracted_char_count=sum(len(page) for page in pages),
        empty_page_count=sum(1 for page in pages if not page.strip()),
    )

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
    if result.empty_page_count:
        result.limitations.append(
            f"共解析{result.page_count}页，其中{result.empty_page_count}页未提取到文字；"
            "这些页面可能为空白页、扫描页或解析失败，未被文字规则有效覆盖。"
        )
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
        result.marketing_provided = False
        return result
    result.marketing_provided = True
    result.findings = []

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

    def add_comparison(
        rule_id: str,
        title: str,
        severity: str,
        status: str,
        formal_plain_language: str,
        explanation: str,
        marketing_excerpt: str | None,
        evidence: Evidence,
    ) -> None:
        if evidence.status == "not_found":
            status = "unclear"
            severity = "gray"
            formal_plain_language = "正式说明书中也没有定位到足够信息，需要人工核对。"
            explanation = "由于正式文件证据不足，系统不能判断宣传说法是否完整或准确。"
        result.findings.append(
            MarketingFinding(
                rule_id=rule_id,
                title=title,
                severity=severity,
                status=status,
                formal_plain_language=formal_plain_language,
                explanation=explanation,
                marketing_text=marketing_excerpt,
                formal_evidence=evidence,
            )
        )

    benchmark_line = None
    for line in text.splitlines():
        if re.search(r"(?:年化|业绩比较基准).*?\d+(?:\.\d+)?%", line):
            benchmark_line = line.strip()
            break
    benchmark_as_return = bool(
        benchmark_line
        and re.search(r"年化\s*\d+(?:\.\d+)?%", benchmark_line)
        and "业绩比较基准" not in benchmark_line
    )
    benchmark_has_boundary = bool(
        re.search(r"业绩比较基准", text)
        and re.search(r"不代表|不等于|非.*收益|不保证", text)
    )
    add_comparison(
        "R02",
        "收益数字的性质",
        "red" if benchmark_as_return else "blue" if benchmark_has_boundary else "orange",
        "conflicting" if benchmark_as_return else "supported" if benchmark_has_boundary else "omitted",
        "正式文件中的数字是业绩比较基准，不是保证收益或实际到手收益。",
        (
            "宣传把业绩比较基准写成“年化收益”，容易形成确定收益预期。"
            if benchmark_as_return
            else "宣传已说明数字属于业绩比较基准且不代表实际收益。"
            if benchmark_has_boundary
            else "宣传没有说明收益数字的性质和非承诺边界。"
        ),
        benchmark_line,
        benchmark_ev,
    )

    absolute_terms = [
        term
        for term in ["稳赚", "稳稳拿", "零风险", "确定收益", "安心增值", "稳健增值"]
        if term in text
    ]
    if re.search(r"(?:^|[^不非])保本", text):
        absolute_terms.append("保本")
    has_non_guarantee = bool(re.search(r"非保本|不保证本金|本金可能.*损失", text))
    generic_risk_only = bool(re.search(r"市场有风险|投资需谨慎", text)) and not has_non_guarantee
    principal_excerpt = next(
        (
            line.strip()
            for line in text.splitlines()
            if re.search(r"非保本|不保证本金|本金可能.*损失|市场有风险|投资需谨慎", line)
        ),
        None,
    )
    add_comparison(
        "R01",
        "本金是否保障",
        "blue" if has_non_guarantee else "orange" if generic_risk_only else "red",
        "supported" if has_non_guarantee else "weakened" if generic_risk_only else "omitted",
        "正式文件明确产品不保本，投资者可能损失部分或全部本金。",
        (
            "宣传已明确提示不保本或本金损失可能。"
            if has_non_guarantee
            else "宣传只有笼统风险提示，没有明确说明本金可能损失。"
            if generic_risk_only
            else "宣传没有披露产品不保本。"
        ),
        principal_excerpt,
        non_guaranteed_ev,
    )
    add_comparison(
        "R08",
        "是否形成确定性预期",
        "red" if absolute_terms else "blue",
        "conflicting" if absolute_terms else "supported",
        "正式文件不保证本金和收益，产品净值可能波动。",
        (
            "宣传使用绝对化表达，与正式文件的不保本、不保证收益边界冲突。"
            if absolute_terms
            else "未发现“稳赚、保本、零风险”等确定性表达。"
        ),
        "、".join(absolute_terms) if absolute_terms else None,
        non_guaranteed_ev,
    )

    has_redemption_limit = bool(re.search(r"不可赎回|不能提前|不开放.*赎回|封闭期", text))
    claims_flexible = bool(re.search(r"随时可取|灵活取用|随取随用|随时赎回", text))
    redemption_excerpt = next(
        (
            line.strip()
            for line in text.splitlines()
            if re.search(r"不可赎回|不能提前|不开放.*赎回|封闭期|随时可取|灵活取用|随取随用|随时赎回", line)
        ),
        None,
    )
    add_comparison(
        "R04",
        "提前退出限制",
        "red" if claims_flexible else "blue" if has_redemption_limit else "orange",
        "conflicting" if claims_flexible else "supported" if has_redemption_limit else "omitted",
        "正式文件说明存续期内原则上不能主动赎回，临时需要资金时可能无法提前取回。",
        (
            "宣传声称资金可灵活取用，与正式文件的赎回限制冲突。"
            if claims_flexible
            else "宣传已披露提前赎回限制。"
            if has_redemption_limit
            else "宣传没有披露提前赎回限制。"
        ),
        redemption_excerpt,
        redemption_ev,
    )

    has_fees = bool(re.search(r"管理费|托管费|销售服务费|费用", text))
    fee_excerpt = next(
        (line.strip() for line in text.splitlines() if re.search(r"管理费|托管费|销售服务费|费用", line)),
        None,
    )
    add_comparison(
        "R06",
        "费用披露",
        "blue" if has_fees else "orange",
        "supported" if has_fees else "omitted",
        "正式文件披露固定管理费等费用，费用会降低实际收益。",
        "宣传已提示费用安排。" if has_fees else "宣传没有披露费用或提示查看完整费用安排。",
        fee_excerpt,
        fee_ev,
    )

    has_worst_case = bool(re.search(r"损失.*本金|延迟兑付|提前终止|最不利", text))
    worst_excerpt = next(
        (
            line.strip()
            for line in text.splitlines()
            if re.search(r"损失.*本金|延迟兑付|提前终止|最不利", line)
        ),
        None,
    )
    add_comparison(
        "R10",
        "最不利情形",
        "blue" if has_worst_case else "orange",
        "supported" if has_worst_case else "omitted",
        "正式文件提示可能损失部分或全部本金，资金到账也可能延迟。",
        "宣传已提示最不利情形。" if has_worst_case else "宣传没有说明本金损失、到账延迟等最不利情形。",
        worst_excerpt,
        worst_ev,
    )
    return result


def build_markdown_report(result: AnalysisResult, document_name: str) -> str:
    lines = [
        "# 金融产品公平说明书",
        "",
        f"> 分析文件：{result.document_name or document_name}",
        f"> 分析引擎：{result.engine}",
        f"> 分析模式：{result.analysis_mode}",
        f"> 文档覆盖：解析 {result.page_count} 页，提取 {result.extracted_char_count} 个字符，"
        f"空白/未提取文字页面 {result.empty_page_count} 页",
        (
            f"> Agent 覆盖：接收 {result.agent_char_count} 个文档字符，"
            f"{'发生截断，未分析完整提取文本' if result.agent_truncated else '未发生截断'}"
            if result.agent_run.enabled
            else "> Agent 覆盖：未启用，全部确定性规则在本地解析文本上运行"
        ),
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
    lines.extend(["", "## 宣传材料与正式说明书逐项对照", ""])
    status_labels = {
        "supported": "支持",
        "omitted": "未披露",
        "weakened": "弱化",
        "conflicting": "冲突",
        "unclear": "无法判断",
    }
    if not result.marketing_provided:
        lines.append("本次未输入宣传材料，因此没有执行宣传材料对照。")
    elif result.findings:
        for finding in result.findings:
            page = (
                f"第{finding.formal_evidence.page}页"
                if finding.formal_evidence.page
                else "未定位"
            )
            lines.extend(
                [
                    f"### {finding.title}｜{status_labels.get(finding.status, finding.status)}",
                    "",
                    finding.explanation,
                    "",
                    f"- 宣传材料说法：{finding.marketing_text or '未披露'}",
                    f"- 正式说明书怎么写：{finding.formal_plain_language}",
                    f"- 核验状态：{status_labels.get(finding.status, finding.status)}",
                    f"- 优先级：{finding.severity}",
                    f"- 正式文件证据（{page}）：{finding.formal_evidence.text}",
                    "",
                ]
            )
    else:
        lines.append("已输入宣传材料，当前规则没有生成可对照项目。")
    lines.extend(["", "## 大模型语义增强", ""])
    if result.agent_run.enabled:
        lines.extend(
            [
                f"> 模型：{result.agent_run.model}；协议："
                f"{result.agent_run.protocol or '未记录'}",
                "> 固定流程：规则引擎 → 分析 Agent → 核验 Agent → 程序逐字引用门控",
                f"> 运行计数：候选 {result.agent_run.candidate_count} 项；"
                f"核验支持 {result.agent_run.verifier_supported_count} 项；"
                f"门控通过 {result.agent_run.gate_passed_count} 项；"
                f"最终拦截 {result.agent_run.rejected_count} 项",
                f"> 停止条件：{result.agent_run.stop_reason}",
                "",
            ]
        )
        if result.agent_run.error:
            lines.extend([f"- 降级原因：{result.agent_run.error}", ""])
        if result.agent_run.rejection_reasons:
            lines.append("### 拦截原因")
            lines.append("")
            lines.extend([f"- {reason}" for reason in result.agent_run.rejection_reasons])
            lines.append("")
    if result.agent_run.enabled and result.agent_insights:
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
