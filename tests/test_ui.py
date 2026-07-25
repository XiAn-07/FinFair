from streamlit.testing.v1 import AppTest

from finfair.core import AnalysisResult, Evidence, FieldResult


def test_first_screen_explains_value_and_two_entry_modes():
    at = AppTest.from_file("app.py", default_timeout=15).run()

    assert not at.exception
    markdown_text = "\n".join(item.value for item in at.markdown)
    assert "金融产品购买前信息核验 Agent" in markdown_text
    assert "不推荐产品" in markdown_text
    assert any(item.label == "选择开始方式" for item in at.radio)
    assert any(
        item.label == "宣传文案（可留空）" for item in at.text_area
    )

    at.radio[0].set_value("上传自己的 PDF").run()
    assert not at.exception
    uploaders = at.get("file_uploader")
    assert len(uploaders) == 1
    assert uploaders[0].label == "上传包含可复制文字的 PDF"


def test_untrusted_evidence_uses_native_safe_rendering():
    malicious = "<script>window.BAD=1</script><img src=x onerror=alert(1)>"
    result = AnalysisResult(
        fields=[
            FieldResult(
                label="产品名称",
                value="安全渲染测试",
                plain_language="测试说明",
                evidence=Evidence(page=1, text=malicious),
            )
        ],
        page_count=1,
        extracted_char_count=len(malicious),
    )
    at = AppTest.from_file("app.py", default_timeout=15)
    at.session_state["analysis_result"] = result
    at.session_state["report_md"] = "# test"
    at.session_state["document_name"] = "安全测试.pdf"
    at.run()

    assert not at.exception
    evidence_blocks = [item for item in at.markdown if item.value == malicious]
    assert len(evidence_blocks) == 1
    # Streamlit protobuf enum 1 = NATIVE（st.write安全渲染），不是允许HTML执行的HTML元素。
    assert evidence_blocks[0].proto.element_type == 1
