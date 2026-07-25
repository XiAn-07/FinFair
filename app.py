from __future__ import annotations

import json
import sys
from pathlib import Path

# Codex桌面工作区自带pdfplumber；普通环境请使用requirements.txt安装。
CODEX_PYTHON_PACKAGES = Path(
    r"C:\Users\32896\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages"
)
if CODEX_PYTHON_PACKAGES.exists() and str(CODEX_PYTHON_PACKAGES) not in sys.path:
    sys.path.append(str(CODEX_PYTHON_PACKAGES))

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
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background: #f6f8fb; color: #172b4d; }
    .block-container { max-width: 1180px; padding-top: 1.6rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: #102a43; letter-spacing: -0.02em; }
    .hero {
        padding: 28px 30px;
        border-radius: 22px;
        color: white;
        background: linear-gradient(135deg, #102a43 0%, #1769aa 70%, #2f80c9 100%);
        box-shadow: 0 16px 40px rgba(16, 42, 67, .18);
        margin-bottom: 22px;
    }
    .hero h1 { color: white; margin: 0 0 8px 0; font-size: 2.2rem; }
    .hero p { color: #eaf4fb; margin: 0; font-size: 1.02rem; }
    .badge {
        display: inline-block; border-radius: 999px; padding: 5px 10px;
        background: rgba(255,255,255,.14); color: white; font-size: .78rem;
        margin-bottom: 12px;
    }
    .notice {
        padding: 13px 15px; border-radius: 12px; background: #fff7e6;
        border: 1px solid #f7c873; color: #7a4d00; margin: 10px 0 18px;
    }
    .evidence {
        padding: 11px 13px; border-radius: 10px; background: #edf5fb;
        border-left: 4px solid #1769aa; color: #334e68; font-size: .9rem;
    }
    .high { color:#b42318; font-weight:700; }
    .medium { color:#b25e09; font-weight:700; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #d9e2ec; border-radius: 14px;
        padding: 12px 14px;
    }
    div[data-testid="stFileUploader"] {
        background: white; border-radius: 14px; padding: 8px 12px;
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
  <p>不替你做决定，只把重要的事讲明白。</p>
</div>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("分析设置")
    st.caption("当前版本：规则引擎 + 双逻辑 Agent")
    use_sample = st.toggle("使用内置教学案例", value=True)
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
    st.subheader("当前能力")
    st.markdown(
        """
- PDF按页解析
- 核心字段提取
- 收益、风险、费用说明
- 宣传文案一致性检查
- 原文页码追溯
- 可选双逻辑Agent增强
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
    st.subheader("1. 上传正式产品文件")
    uploaded = st.file_uploader("选择包含可复制文字的PDF", type=["pdf"])
    if use_sample and uploaded is None:
        st.info("将使用内置《模拟理财产品说明书.pdf》。")

with right:
    st.subheader("2. 输入宣传文案（可选）")
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
        "只输入用户实际看到的内容，不要包含人工标准答案。",
        value=default_marketing,
        height=210,
        placeholder="粘贴广告、海报或销售话术……",
    )

analyze_clicked = st.button("开始生成公平说明书", type="primary", use_container_width=True)

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
        progress.progress(65, text="正在核验风险、费用与退出条件……")
        result = analyze_marketing(marketing_text, pages, result)
        if enable_agent:
            if not saved_api_config:
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
                    result.agent_run.status = "API失败，已降级为规则模式"
                    result.agent_run.error = str(exc)
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

    high_count = sum(
        1 for x in result.fields + result.risks if x.severity == "high"
    ) + sum(1 for x in result.findings if x.severity == "red")
    metrics = st.columns(4)
    metrics[0].metric("解析页数", result.page_count)
    metrics[1].metric("核心字段", len(result.fields))
    metrics[2].metric("宣传问题", len(result.findings))
    metrics[3].metric("高优先级提醒", high_count)

    tab_summary, tab_risk, tab_marketing, tab_agent, tab_questions, tab_raw = st.tabs(
        [
            "30秒看懂",
            "风险与最坏情形",
            "宣传材料检查",
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
                st.markdown(
                    f'<div class="evidence"><b>证据位置：{page}</b><br>{item.evidence.text}</div>',
                    unsafe_allow_html=True,
                )

    with tab_risk:
        for item in result.risks:
            page = f"第 {item.evidence.page} 页" if item.evidence.page else "未定位"
            st.markdown(f"### {'🔴' if item.severity == 'high' else '🟠'} {item.label}")
            st.write(item.value)
            st.caption(item.plain_language)
            st.markdown(
                f'<div class="evidence"><b>{page}</b><br>{item.evidence.text}</div>',
                unsafe_allow_html=True,
            )

    with tab_marketing:
        if not result.findings:
            st.success("未提交宣传材料，或当前规则没有发现明显差异。")
        for finding in result.findings:
            icon = "🔴" if finding.severity == "red" else "🟠"
            st.markdown(f"### {icon} {finding.title}")
            st.write(finding.explanation)
            if finding.marketing_text:
                st.markdown(f"**宣传原文：** {finding.marketing_text}")
            else:
                st.markdown("**宣传材料状态：** 未披露")
            page = (
                f"第 {finding.formal_evidence.page} 页"
                if finding.formal_evidence.page
                else "未定位"
            )
            st.markdown(
                f'<div class="evidence"><b>正式文件证据：{page}</b><br>{finding.formal_evidence.text}</div>',
                unsafe_allow_html=True,
            )

    with tab_agent:
        if not result.agent_run.enabled:
            st.info("本次使用规则模式。可在左侧开启“大模型语义增强”并自行配置API。")
        elif result.agent_run.error:
            st.warning(result.agent_run.status)
            st.caption(result.agent_run.error)
        else:
            st.success(
                f"{result.agent_run.status}：模型 {result.agent_run.model}，"
                f"接受 {result.agent_run.accepted_count} 项，"
                f"拦截 {result.agent_run.rejected_count} 项。"
            )
            st.caption(
                "只有同时通过证据核验Agent和程序化逐字引用校验的内容才会显示。"
            )
            if result.agent_run.rejection_reasons:
                with st.expander("查看候选内容被拦截的原因"):
                    for reason in result.agent_run.rejection_reasons:
                        st.write(f"- {reason}")
            if not result.agent_insights:
                st.info("没有发现通过双重核验的新增语义洞察。")
            for insight in result.agent_insights:
                icon = "🔴" if insight.severity == "high" else "🟠" if insight.severity == "medium" else "🔵"
                st.markdown(f"### {icon} {insight.title}")
                st.write(insight.conclusion)
                st.caption(insight.plain_language)
                st.markdown(
                    f'<div class="evidence"><b>{insight.verification_status} · '
                    f'第 {insight.evidence.page} 页</b><br>{insight.evidence.text}</div>',
                    unsafe_allow_html=True,
                )

    with tab_questions:
        for index, question in enumerate(result.questions, start=1):
            st.markdown(f"**{index}. {question}**")
        st.warning("这些问题用于帮助核对信息，不代表系统建议购买或拒绝购买。")

    with tab_raw:
        st.json(result.to_dict())

    st.subheader("下载结果")
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
