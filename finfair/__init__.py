"""FinFair core package."""

from .core import (
    AgentInsight,
    AgentRunInfo,
    AnalysisResult,
    analyze_document,
    analyze_marketing,
    build_markdown_report,
    extract_pdf_pages,
)
from .llm_agent import AgentAPIError, LLMConfig, run_hybrid_agents
from .report_export import build_docx_report, build_pdf_report

__all__ = [
    "AgentAPIError",
    "AgentInsight",
    "AgentRunInfo",
    "AnalysisResult",
    "LLMConfig",
    "analyze_document",
    "analyze_marketing",
    "build_markdown_report",
    "build_docx_report",
    "build_pdf_report",
    "extract_pdf_pages",
    "run_hybrid_agents",
]
