from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from finfair import (
    AgentAPIError,
    LLMConfig,
    analyze_document,
    analyze_marketing,
    build_docx_report,
    build_markdown_report,
    build_pdf_report,
    extract_pdf_pages,
    run_hybrid_agents,
)


ROOT = Path(__file__).resolve().parent
SAMPLE_PDF = ROOT / "sample_data" / "模拟理财产品说明书.pdf"
SAMPLE_MARKETING = ROOT / "sample_data" / "模拟宣传文案.md"

st.set_page_config(
    page_title="明白金 FinFair",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
    :root {
        --ink: #173330;
        --muted: #5d716e;
        --brand: #0b6e69;
        --brand-dark: #084c49;
        --brand-soft: #e8f1ee;
        --paper: #ffffff;
        --line: #d8e2df;
        --warning: #9a5b08;
        --danger: #a7332b;
    }
    .stApp {
        background:
            radial-gradient(circle at 85% 8%, rgba(129, 190, 176, .16), transparent 30rem),
            #f5f7f4;
        color: var(--ink);
    }
    .block-container { max-width: 1160px; padding-top: 1.25rem; padding-bottom: 3.5rem; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -0.025em; }
    h2 { margin-top: 1.2rem; }
    .hero {
        padding: 34px 38px;
        border-radius: 26px;
        color: white;
        background:
            linear-gradient(120deg, rgba(255,255,255,.06), transparent 45%),
            linear-gradient(135deg, #103f3c 0%, #0b6e69 62%, #2f8f82 100%);
        box-shadow: 0 18px 44px rgba(13, 72, 68, .18);
        margin-bottom: 18px;
        border: 1px solid rgba(255,255,255,.12);
    }
    .hero h1 { color: white; margin: 0 0 10px 0; font-size: 2.45rem; line-height: 1.12; }
    .hero p { color: #e9f6f3; margin: 0; font-size: 1.04rem; line-height: 1.75; max-width: 58rem; }
    .badge {
        display: inline-block; border-radius: 999px; padding: 5px 10px;
        background: rgba(255,255,255,.14); color: white; font-size: .78rem;
        margin-bottom: 12px;
    }
    .hero-boundary {
        margin-top: 14px; color: #cfe8e2; font-size: .86rem;
    }
    .notice {
        padding: 13px 16px; border-radius: 14px; background: #fff8e8;
        border: 1px solid #ead7a8; color: #76500e; margin: 14px 0 20px;
    }
    .step-label {
        display: inline-flex; align-items: center; gap: 7px;
        color: var(--brand-dark); background: var(--brand-soft);
        border: 1px solid #cfe0dc; padding: 5px 10px;
        border-radius: 999px; font-size: .78rem; font-weight: 700;
        margin-bottom: 4px;
    }
    .section-note { color: var(--muted); font-size: .92rem; margin-bottom: 12px; }
    .summary-grid {
        display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 12px; margin: 12px 0 22px;
    }
    .summary-card {
        background: rgba(255,255,255,.92); border: 1px solid var(--line);
        border-radius: 16px; padding: 14px 15px;
        box-shadow: 0 6px 18px rgba(23, 51, 48, .04);
    }
    .summary-card span { display: block; color: var(--muted); font-size: .78rem; }
    .summary-card strong { display: block; color: var(--ink); font-size: 1.55rem; margin-top: 4px; }
    .status-supported, .status-omitted, .status-weakened,
    .status-conflicting, .status-unclear {
        display: inline-block; border-radius: 999px; padding: 3px 9px;
        font-size: .78rem; font-weight: 700; margin-bottom: 8px;
    }
    .status-supported { color: #12613e; background: #e4f4e9; }
    .status-omitted { color: #8b4b08; background: #fff0d7; }
    .status-weakened { color: #8a5810; background: #f8e8c9; }
    .status-conflicting { color: #982d28; background: #fde7e5; }
    .status-unclear { color: #536360; background: #e9eeec; }
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,.92); border: 1px solid var(--line);
        border-radius: 16px; padding: 13px 15px;
        box-shadow: 0 6px 18px rgba(23, 51, 48, .04);
    }
    div[data-testid="stFileUploader"] {
        background: white; border: 1px solid var(--line);
        border-radius: 16px; padding: 9px 12px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255,255,255,.86);
        border-color: var(--line);
        border-radius: 16px;
    }
    div[data-testid="stDownloadButton"] button {
        border-radius: 12px; min-height: 2.8rem; font-weight: 650;
        border-color: #b9ceca;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        border-radius: 13px; min-height: 3rem; font-weight: 750;
        box-shadow: 0 8px 22px rgba(11, 110, 105, .18);
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--line); border-radius: 14px; overflow: hidden;
    }
    @media (max-width: 768px) {
        .block-container { padding: .75rem .85rem 2.5rem; }
        .hero { padding: 24px 21px; border-radius: 20px; }
        .hero h1 { font-size: 1.9rem; }
        .hero p { font-size: .94rem; line-height: 1.6; }
        .hero-boundary { font-size: .8rem; }
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .75rem; }
        div[data-testid="column"] { min-width: 100% !important; flex: 1 1 100% !important; }
        .summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        div[data-testid="stMetric"] { min-height: auto; }
        div[data-testid="stDataFrame"] { font-size: .82rem; }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.45rem !important; }
        h3 { font-size: 1.12rem !important; }
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
  <div class="badge">教学模拟 MVP · 可追溯金融文件分析</div>
  <h1>明白金 FinFair</h1>
  <p>金融产品购买前信息核验 Agent：将宣传材料与正式说明书逐项对照，把收益、本金、期限、费用和风险翻译成普通用户能理解的说明，并为每个结论提供可追溯证据。</p>
  <div class="hero-boundary">只解释与核验信息，不推荐产品，不替代适当性评估或人工判断。</div>
</div>
""",
    unsafe_allow_html=True,
)

entry_mode = st.radio(
    "选择开始方式",
    ["使用教学案例", "上传自己的 PDF"],
    horizontal=True,
    help="建议课堂演示优先使用教学案例；自己的材料必须先脱敏。",
)
use_sample = entry_mode == "使用教学案例"


def render_evidence(label: str, page: str, text: str) -> None:
    """Render untrusted document text without injecting it into HTML."""
    with st.container(border=True):
        st.caption(f"{label} · {page}")
        st.write(text)


with st.sidebar:
    st.header("高级分析设置")
    st.caption("默认使用稳定的规则模式；需要时再开启双阶段 Agent。")
    enable_agent = st.toggle(
        "启用大模型语义增强",
        value=False,
        help="启用后将调用语义分析Agent和证据核验Agent各一次。",
    )
    provider = "通义千问（阿里云百炼·国内）"
    saved_api_config = st.session_state.get("saved_api_config")
    if enable_agent:
        st.subheader("自行接入 API")
        presets = {
            "通义千问（阿里云百炼·国内）": {
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model": "qwen3.7-plus",
                "protocol": "openai_compatible",
            },
            "DeepSeek": {
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-flash",
                "protocol": "openai_compatible",
            },
            "Kimi（月之暗面·国内）": {
                "base_url": "https://api.moonshot.cn/v1",
                "model": "kimi-k2.6",
                "protocol": "openai_compatible",
            },
            "Grok（xAI）": {
                "base_url": "https://api.x.ai/v1",
                "model": "grok-4.5",
                "protocol": "openai_compatible",
            },
            "Gemini（Google AI）": {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
                "model": "gemini-3.6-flash",
                "protocol": "openai_compatible",
            },
            "OpenAI": {
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-5-mini",
                "protocol": "openai_compatible",
            },
            "Claude（Anthropic 原生）": {
                "base_url": "https://api.anthropic.com/v1",
                "model": "claude-sonnet-5",
                "protocol": "anthropic",
            },
            "自定义 OpenAI 兼容接口": {
                "base_url": "",
                "model": "",
                "protocol": "openai_compatible",
            },
            "自定义 Anthropic 原生接口": {
                "base_url": "",
                "model": "",
                "protocol": "anthropic",
            },
        }
        provider_options = list(presets)
        saved_provider = (
            saved_api_config.get("provider")
            if saved_api_config
            else "通义千问（阿里云百炼·国内）"
        )
        provider = st.selectbox(
            "接口预设",
            provider_options,
            index=provider_options.index(saved_provider)
            if saved_provider in provider_options
            else 0,
        )
        selected_preset = presets[provider]
        default_url = selected_preset["base_url"]
        default_model = selected_preset["model"]
        api_protocol = selected_preset["protocol"]
        existing_for_provider = (
            saved_api_config
            if saved_api_config and saved_api_config.get("provider") == provider
            else {}
        )
        with st.form("api_config_form"):
            api_base_url_input = st.text_input(
                "Base URL",
                value=existing_for_provider.get("base_url", default_url),
                placeholder="https://.../v1",
                help=(
                    "将调用原生 /messages 接口。"
                    if api_protocol == "anthropic"
                    else "将调用 OpenAI 兼容的 /chat/completions 接口。"
                ),
            )
            api_model_input = st.text_input(
                "模型名称",
                value=existing_for_provider.get("model", default_model),
                placeholder="填写服务商提供的模型ID",
            )
            api_key_input = st.text_input(
                "API Key",
                value=existing_for_provider.get("api_key", ""),
                type="password",
                placeholder="仅用于本次浏览器会话",
                help="不会写入项目文件、下载报告或GitHub。",
            )
            data_consent_input = st.checkbox(
                "我理解：PDF文字和宣传文案将发送给所选模型服务商",
                value=bool(existing_for_provider),
            )
            confirm_api = st.form_submit_button(
                "确认并保存 API", type="primary", use_container_width=True
            )
        if confirm_api:
            if not all(
                [
                    api_base_url_input.strip(),
                    api_model_input.strip(),
                    api_key_input.strip(),
                ]
            ):
                st.error("请完整填写 Base URL、模型名称和 API Key。")
            elif not data_consent_input:
                st.error("请先确认数据发送提示。")
            else:
                st.session_state["saved_api_config"] = {
                    "provider": provider,
                    "base_url": api_base_url_input.strip(),
                    "model": api_model_input.strip(),
                    "api_key": api_key_input.strip(),
                    "protocol": api_protocol,
                }
                st.rerun()
        saved_api_config = st.session_state.get("saved_api_config")
        if saved_api_config:
            key_tail = saved_api_config["api_key"][-4:]
            st.success(
                f"API 已保存（当前会话）：{saved_api_config['provider']} / "
                f"{saved_api_config['model']} / ••••{key_tail}"
            )
            if st.button("清除已保存 API", use_container_width=True):
                del st.session_state["saved_api_config"]
                st.rerun()
        else:
            st.info("填写后请点击“确认并保存 API”，保存成功后才能运行 Agent。")
        st.caption("请勿上传真实客户资料、身份证、银行卡号或其他敏感信息。")
    st.divider()
    st.subheader("能力边界")
    st.markdown(
        """
- PDF按页解析
- 核心字段提取
- 收益、风险、费用说明
- 宣传文案一致性检查
- 原文页码追溯
- 可选双阶段Agent增强
- Markdown、JSON、Word和PDF下载
"""
    )
    st.divider()
    st.caption("暂不支持扫描件OCR、多产品比较和正式适当性判断。")

st.markdown(
    '<div class="notice">请勿上传身份证、银行卡号、账户流水等真实敏感信息。本工具仅用于课程教学演示，不构成投资建议。</div>',
    unsafe_allow_html=True,
)

left, right = st.columns([1.05, 0.95], gap="large")
with left:
    st.markdown('<span class="step-label">步骤 1 · 正式文件</span>', unsafe_allow_html=True)
    st.subheader("选择要核验的产品说明书")
    uploaded = None
    if use_sample:
        st.success("已选择内置《模拟理财产品说明书.pdf》，可直接开始分析。")
        st.caption("教学案例完全虚构，不对应真实机构或金融产品。")
    else:
        uploaded = st.file_uploader(
            "上传包含可复制文字的 PDF",
            type=["pdf"],
            help="当前不支持纯扫描件；请先移除个人身份、账户和交易信息。",
        )

with right:
    st.markdown('<span class="step-label">步骤 2 · 宣传材料</span>', unsafe_allow_html=True)
    st.subheader("粘贴用户实际看到的宣传文案")
    default_marketing = ""
    if use_sample and SAMPLE_MARKETING.exists():
        text = SAMPLE_MARKETING.read_text(encoding="utf-8")
        marker = "## 用户看到的宣传内容"
        end_marker = "---"
        if marker in text:
            text = text.split(marker, 1)[1]
        if end_marker in text:
            text = text.split(end_marker, 1)[0]
        default_marketing = text.strip()
    marketing_text = st.text_area(
        "宣传文案（可留空）",
        value=default_marketing,
        height=210,
        placeholder="粘贴广告、海报或销售话术……",
        help="只输入用户实际看到的内容，不要包含人工标准答案。",
    )

mode_text = "双阶段 Agent 增强" if enable_agent else "规则模式（无需 API）"
st.markdown('<span class="step-label">步骤 3 · 开始核验</span>', unsafe_allow_html=True)
st.caption(f"当前分析模式：{mode_text}。如需切换，可展开左上角高级分析设置。")
analyze_clicked = st.button(
    "开始核验并生成公平说明书", type="primary", use_container_width=True
)

if analyze_clicked:
    try:
        if uploaded is not None:
            pdf_bytes = uploaded.getvalue()
            document_name = uploaded.name
        elif use_sample and SAMPLE_PDF.exists():
            pdf_bytes = SAMPLE_PDF.read_bytes()
            document_name = SAMPLE_PDF.name
        else:
            st.error("请上传PDF，或打开“使用内置教学案例”。")
            st.stop()

        progress = st.progress(0, text="正在检查文件……")
        pages = extract_pdf_pages(pdf_bytes)
        progress.progress(30, text=f"已解析{len(pages)}页，正在提取产品信息……")
        result = analyze_document(pages)
        result.document_name = document_name
        progress.progress(65, text="正在核验风险、费用与退出条件……")
        result = analyze_marketing(marketing_text, pages, result)
        if enable_agent:
            if not saved_api_config:
                result.analysis_mode = "规则模式（未配置 API）"
                st.warning("尚未确认保存 API，本次已自动降级为规则模式。")
            else:
                progress.progress(72, text="语义分析Agent正在提出候选洞察……")
                try:
                    result = run_hybrid_agents(
                        pages,
                        marketing_text,
                        result,
                        LLMConfig(
                            api_key=saved_api_config["api_key"],
                            base_url=saved_api_config["base_url"],
                            model=saved_api_config["model"],
                            protocol=saved_api_config.get(
                                "protocol", "openai_compatible"
                            ),
                        ),
                    )
                    progress.progress(90, text="证据核验Agent和程序化引用校验已完成……")
                except AgentAPIError as exc:
                    result.agent_run.enabled = True
                    result.agent_run.model = saved_api_config["model"]
                    result.agent_run.protocol = saved_api_config.get(
                        "protocol", "openai_compatible"
                    )
                    result.agent_run.status = "API失败，已降级为规则模式"
                    result.agent_run.stop_reason = "API 调用失败，流程已停止并降级为规则模式"
                    result.agent_run.error = str(exc)
                    result.analysis_mode = "规则模式（Agent 调用失败）"
                    st.warning(f"大模型增强失败，规则分析结果仍然有效：{exc}")
        progress.progress(94, text="正在生成可追溯报告……")
        report_md = build_markdown_report(result, document_name)
        progress.progress(100, text="分析完成")

        st.session_state["analysis_result"] = result
        st.session_state["report_md"] = report_md
        st.session_state["document_name"] = document_name
        st.session_state.pop("report_docx", None)
        st.session_state.pop("report_pdf", None)
    except Exception as exc:
        st.error(f"分析失败：{exc}")

if "analysis_result" in st.session_state:
    result = st.session_state["analysis_result"]
    st.divider()
    st.header("金融产品公平说明书")

    st.subheader("本次分析覆盖范围")
    with st.container(border=True):
        st.caption("分析文件")
        st.write(
            result.document_name
            or st.session_state.get("document_name", "未记录")
        )
        st.caption(
            f"解析 {result.page_count} 页 · 提取 {result.extracted_char_count} 个字符 · "
            f"未提取文字 {result.empty_page_count} 页 · {result.analysis_mode}"
        )
    if result.agent_run.enabled:
        st.caption(f"发送给 Agent 的文档字符数：{result.agent_char_count}")
        if result.agent_truncated:
            st.warning(
                "Agent 输入因长度限制发生截断：规则引擎仍处理了全部已提取文字，"
                "但大模型语义增强没有覆盖完整文档，不能把 Agent 结果视为全文审查。"
            )
        else:
            st.success("Agent 输入未发生长度截断。")
    else:
        st.info("本次未启用 Agent；确定性规则处理了全部已提取文字。")
    if result.empty_page_count:
        empty_ratio = result.empty_page_count / max(result.page_count, 1)
        message = (
            f"{result.empty_page_count} 页没有提取到文字，可能是空白页、扫描页或解析失败。"
        )
        if empty_ratio >= 0.5:
            st.warning(message + " 未覆盖页面比例较高，请不要将结果理解为完整文件审查。")
        else:
            st.caption(message)

    status_labels = {
        "supported": "支持",
        "omitted": "未披露",
        "weakened": "弱化",
        "conflicting": "冲突",
        "unclear": "无法判断",
    }
    priority_labels = {
        "red": "高",
        "orange": "中",
        "blue": "提示",
        "gray": "待人工核对",
    }
    marketing_issue_count = sum(
        1 for item in result.findings if item.status != "supported"
    )
    high_count = sum(
        1 for x in result.fields + result.risks if x.severity == "high"
    ) + sum(
        1
        for x in result.findings
        if x.severity == "red" and x.status != "supported"
    )
    st.markdown(
        f"""
<div class="summary-grid">
  <div class="summary-card"><span>解析页数</span><strong>{int(result.page_count)}</strong></div>
  <div class="summary-card"><span>核心字段</span><strong>{len(result.fields)}</strong></div>
  <div class="summary-card"><span>宣传核验问题</span><strong>{marketing_issue_count}</strong></div>
  <div class="summary-card"><span>高优先级提醒</span><strong>{high_count}</strong></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.subheader("宣传材料与正式说明书逐项对照")
    st.caption("核心问题：宣传材料怎么说，正式说明书到底怎么写。")
    if not result.marketing_provided:
        st.info("本次未输入宣传材料，因此没有执行宣传材料对照。可粘贴宣传文案后重新分析。")
    elif not result.findings:
        st.success("已输入宣传材料，当前规则没有生成可对照项目。")
    else:
        comparison_rows = []
        for finding in result.findings:
            page = (
                f"第 {finding.formal_evidence.page} 页"
                if finding.formal_evidence.page
                else "未定位"
            )
            comparison_rows.append(
                {
                    "核验项目": finding.title,
                    "宣传材料说法": finding.marketing_text or "未披露",
                    "正式说明书怎么写": finding.formal_plain_language,
                    "核验状态": status_labels.get(finding.status, finding.status),
                    "优先级": priority_labels.get(finding.severity, finding.severity),
                    "证据位置": page,
                }
            )
        st.dataframe(
            comparison_rows,
            use_container_width=True,
            hide_index=True,
            column_config={
                "宣传材料说法": st.column_config.TextColumn(width="medium"),
                "正式说明书怎么写": st.column_config.TextColumn(width="large"),
            },
        )
        issue_rows = [item for item in result.findings if item.status != "supported"]
        if not issue_rows:
            st.success("当前规则检查的项目均有对应披露，未发现明显遗漏、弱化或冲突。")
        for finding in issue_rows:
            status = status_labels.get(finding.status, finding.status)
            status_class = (
                finding.status
                if finding.status
                in {"supported", "omitted", "weakened", "conflicting", "unclear"}
                else "unclear"
            )
            page = (
                f"第 {finding.formal_evidence.page} 页"
                if finding.formal_evidence.page
                else "未定位"
            )
            with st.expander(f"{status}｜{finding.title}", expanded=finding.severity == "red"):
                st.markdown(
                    f'<span class="status-{status_class}">{status}</span>',
                    unsafe_allow_html=True,
                )
                st.write(finding.explanation)
                st.markdown("**宣传材料说法**")
                st.write(finding.marketing_text or "未披露")
                st.markdown("**正式说明书结论**")
                st.write(finding.formal_plain_language)
                render_evidence("正式文件证据", page, finding.formal_evidence.text)

    tab_summary, tab_risk, tab_agent, tab_questions, tab_raw = st.tabs(
        [
            "30秒看懂",
            "风险与最坏情形",
            "Agent语义增强",
            "购买前问题",
            "结构化结果",
        ]
    )

    with tab_summary:
        for item in result.fields:
            icon = "🔴" if item.severity == "high" else "🟠" if item.severity == "medium" else "🔵"
            with st.expander(f"{icon} {item.label}：{item.value}", expanded=item.severity == "high"):
                st.write(item.plain_language)
                page = f"第 {item.evidence.page} 页" if item.evidence.page else "未定位"
                render_evidence("证据位置", page, item.evidence.text)

    with tab_risk:
        for item in result.risks:
            page = f"第 {item.evidence.page} 页" if item.evidence.page else "未定位"
            st.markdown(f"### {'🔴' if item.severity == 'high' else '🟠'} {item.label}")
            st.write(item.value)
            st.caption(item.plain_language)
            render_evidence("正式文件证据", page, item.evidence.text)

    with tab_agent:
        st.markdown("### 双阶段 Agent 核验流程")
        st.caption(
            "当前两个逻辑阶段使用同一份模型配置，按固定顺序各调用一次；"
            "没有两个模型无限对话，也不将核验阶段描述为完全独立模型。"
        )
        stage_columns = st.columns(4)
        stage_columns[0].markdown("**① 规则引擎**")
        stage_columns[0].success("已完成确定性提取")
        stage_columns[1].markdown("**② 分析 Agent**")
        if result.agent_run.analyzer_called:
            stage_columns[1].success("已提出候选")
        elif result.agent_run.error and result.agent_run.enabled:
            stage_columns[1].error("调用未完成")
        else:
            stage_columns[1].info("未启用")
        stage_columns[2].markdown("**③ 核验 Agent**")
        if result.agent_run.verifier_called:
            stage_columns[2].success("已核验证据")
        elif result.agent_run.analyzer_called and result.agent_run.error:
            stage_columns[2].error("调用未完成")
        else:
            stage_columns[2].info("未运行")
        stage_columns[3].markdown("**④ 程序门控**")
        if result.agent_run.verifier_called and not result.agent_run.error:
            stage_columns[3].success("逐字引用检查完成")
        else:
            stage_columns[3].info("未运行")

        if not result.agent_run.enabled:
            st.info("本次使用规则模式。可在左侧开启“大模型语义增强”并自行配置API。")
        elif result.agent_run.error:
            st.warning(result.agent_run.status)
            st.caption(result.agent_run.error)
        else:
            st.success(
                f"{result.agent_run.status}：程序门控接受 "
                f"{result.agent_run.gate_passed_count} 项，"
                f"拦截 {result.agent_run.rejected_count} 项。"
            )
        if result.agent_run.enabled:
            protocol_label = (
                "Anthropic Messages"
                if result.agent_run.protocol == "anthropic"
                else "OpenAI-compatible"
            )
            st.caption(
                f"模型：{result.agent_run.model or '未记录'}｜协议：{protocol_label}。"
                "页面不展示 API Key 或完整请求内容。"
            )
            run_metrics = st.columns(4)
            run_metrics[0].metric("分析候选", result.agent_run.candidate_count)
            run_metrics[1].metric(
                "核验支持", result.agent_run.verifier_supported_count
            )
            run_metrics[2].metric("门控通过", result.agent_run.gate_passed_count)
            run_metrics[3].metric("最终拦截", result.agent_run.rejected_count)
            st.markdown(
                f"**停止条件：** {result.agent_run.stop_reason or '固定两阶段完成后停止'}"
            )
            st.caption(
                "只有核验阶段判定支持、且程序能在指定页找到逐字引文的候选才会进入结果。"
            )
            if result.agent_run.rejection_reasons:
                with st.expander("查看候选内容被拦截的原因"):
                    for reason in result.agent_run.rejection_reasons:
                        st.write(f"- {reason}")
            elif not result.agent_run.error:
                st.info("本次没有候选被拦截。")
            if not result.agent_insights:
                st.info("没有发现通过双重核验的新增语义洞察。")
            for insight in result.agent_insights:
                icon = "🔴" if insight.severity == "high" else "🟠" if insight.severity == "medium" else "🔵"
                st.markdown(f"### {icon} {insight.title}")
                st.write(insight.conclusion)
                st.caption(insight.plain_language)
                render_evidence(
                    insight.verification_status,
                    f"第 {insight.evidence.page} 页",
                    insight.evidence.text,
                )

    with tab_questions:
        for index, question in enumerate(result.questions, start=1):
            st.markdown(f"**{index}. {question}**")
        st.warning("这些问题用于帮助核对信息，不代表系统建议购买或拒绝购买。")

    with tab_raw:
        st.json(result.to_dict())

    st.markdown('<span class="step-label">完成 · 保存结果</span>', unsafe_allow_html=True)
    st.subheader("下载公平说明书")
    st.caption("四种格式来自同一份分析结果。下载内容仅供教学与信息核对，不构成投资建议。")
    download_md, download_json = st.columns(2)
    download_md.download_button(
        "下载Markdown公平说明书",
        data=st.session_state["report_md"].encode("utf-8"),
        file_name="金融产品公平说明书.md",
        mime="text/markdown",
        use_container_width=True,
    )
    download_json.download_button(
        "下载JSON结构化结果",
        data=json.dumps(result.to_dict(), ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="金融产品分析结果.json",
        mime="application/json",
        use_container_width=True,
    )
    try:
        if "report_docx" not in st.session_state:
            st.session_state["report_docx"] = build_docx_report(
                result, st.session_state["document_name"]
            )
        if "report_pdf" not in st.session_state:
            st.session_state["report_pdf"] = build_pdf_report(
                result, st.session_state["document_name"]
            )
        download_word, download_pdf = st.columns(2)
        download_word.download_button(
            "下载Word公平说明书",
            data=st.session_state["report_docx"],
            file_name="金融产品公平说明书.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        download_pdf.download_button(
            "下载PDF公平说明书",
            data=st.session_state["report_pdf"],
            file_name="金融产品公平说明书.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as exc:
        st.warning(f"Word/PDF生成失败，Markdown和JSON仍可正常下载：{exc}")

    with st.expander("局限与免责声明"):
        for item in result.limitations:
            st.write(f"- {item}")
