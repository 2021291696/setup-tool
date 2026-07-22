"""Regression tests for concise, evidence-backed manuals."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gen_tool_manual as gtm  # noqa: E402


SAMPLE = {
    "name": "test-tool",
    "function_desc": "Automates a focused, repetitive task.",
    "usage": ["Run the documented command.", "Check the generated result."],
    "special_notes": ["Requires noncommercial use."],
    "sources": ["README: https://example.com/test-tool#usage"],
}


def test_manual_contains_only_reader_facing_sections(tmp_path):
    content = gtm.generate_markdown([SAMPLE], tmp_path).read_text(encoding="utf-8")
    assert content.startswith("# test-tool")
    for section in ("## 作用", "## 使用方法", "## 特殊注意事项"):
        assert section in content
    for forbidden in ("安装方案", "最终选择", "验证结果", "来源与核验", "适配性评估", "配置"):
        assert forbidden not in content


def test_special_notes_section_is_omitted_when_empty(tmp_path):
    tool = {**SAMPLE, "special_notes": []}
    content = gtm.generate_markdown([tool], tmp_path).read_text(encoding="utf-8")
    assert "特殊注意事项" not in content


def test_usage_is_never_derived_from_name(tmp_path):
    tool = {**SAMPLE, "name": "no-trigger-tool", "usage": ["Open it from the documented host menu."]}
    content = gtm.generate_markdown([tool], tmp_path).read_text(encoding="utf-8")
    assert "/no-trigger-tool" not in content
    assert "Open it from the documented host menu." in content


@pytest.mark.parametrize("field", ["function_desc", "usage", "sources"])
def test_missing_required_metadata_fails_fast(tmp_path, field):
    tool = dict(SAMPLE)
    tool.pop(field)
    with pytest.raises(ValueError, match=field):
        gtm.generate_markdown([tool], tmp_path)


def test_word_has_only_allowed_sections(tmp_path):
    output = gtm.generate_docx([SAMPLE], tmp_path)
    from docx import Document
    text = "\n".join(paragraph.text for paragraph in Document(output).paragraphs)
    assert all(section in text for section in ("作用", "使用方法", "特殊注意事项"))
    assert "安装方案" not in text


def test_utf8_output_configuration_is_safe():
    gtm.configure_utf8_output()
