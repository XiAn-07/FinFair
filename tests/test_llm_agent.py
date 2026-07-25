import json

from finfair.core import AnalysisResult
from finfair.llm_agent import LLMConfig, _chat, _endpoint, run_hybrid_agents
from finfair.llm_agent import _quote_is_on_page


def test_endpoint_rejects_local_network():
    try:
        _endpoint("http://127.0.0.1:8000/v1")
        assert False, "应拒绝非HTTPS本地地址"
    except Exception as exc:
        assert "HTTPS" in str(exc) or "内网" in str(exc)


def test_anthropic_endpoint_and_native_response(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps(
                {"content": [{"type": "text", "text": "Claude 返回成功"}]}
            ).encode()

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode())
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("finfair.llm_agent.urllib.request.urlopen", fake_urlopen)
    output = _chat(
        LLMConfig(
            api_key="test-key",
            base_url="https://api.anthropic.com/v1",
            model="claude-sonnet-5",
            protocol="anthropic",
        ),
        "system prompt",
        "user prompt",
    )

    assert captured["url"] == "https://api.anthropic.com/v1/messages"
    assert captured["headers"]["X-api-key"] == "test-key"
    assert captured["headers"]["Anthropic-version"] == "2023-06-01"
    assert captured["payload"]["system"] == "system prompt"
    assert captured["payload"]["max_tokens"] == 4096
    assert output == "Claude 返回成功"


def test_quote_gate_allows_only_layout_punctuation_differences():
    pages = ["固定管理费 0.30%/年｜按前一日产品净资产每日计提。"]
    assert _quote_is_on_page(
        "固定管理费：0.30%/年，按前一日产品净资产每日计提", 1, pages
    )
    assert not _quote_is_on_page("固定管理费0.20%/年", 1, pages)


def test_two_agent_calls_and_exact_quote_gate(monkeypatch):
    pages = ["本产品不保证本金和收益。另有一项重要但容易忽略的条件。"]
    responses = iter(
        [
            json.dumps(
                {
                    "insights": [
                        {
                            "id": "A1",
                            "title": "有效洞察",
                            "conclusion": "存在额外条件",
                            "plain_language": "购买前需要继续确认。",
                            "severity": "medium",
                            "evidence_quote": "另有一项重要但容易忽略的条件。",
                            "page": 1,
                        },
                        {
                            "id": "A2",
                            "title": "虚构洞察",
                            "conclusion": "原文没有这句话",
                            "plain_language": "不应展示。",
                            "severity": "high",
                            "evidence_quote": "这是一段模型虚构的原文。",
                            "page": 1,
                        },
                    ]
                },
                ensure_ascii=False,
            ),
            json.dumps(
                {
                    "verification": [
                        {"id": "A1", "status": "supported", "reason": "原文支持"},
                        {"id": "A2", "status": "supported", "reason": "模型误判"},
                    ]
                },
                ensure_ascii=False,
            ),
        ]
    )

    monkeypatch.setattr("finfair.llm_agent._chat", lambda *_args, **_kwargs: next(responses))
    result = run_hybrid_agents(
        pages,
        "",
        AnalysisResult(),
        LLMConfig(
            api_key="test-key",
            base_url="https://example.com/v1",
            model="test-model",
        ),
    )

    assert result.agent_run.analyzer_called is True
    assert result.agent_run.verifier_called is True
    assert result.agent_run.accepted_count == 1
    assert result.agent_run.rejected_count == 1
    assert result.agent_run.rejection_reasons == ["A2：引文无法在第1页逐字定位"]
    assert result.agent_insights[0].insight_id == "A1"
