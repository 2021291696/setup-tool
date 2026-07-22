"""Regression tests for portable, evidence-backed manuals."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import gen_tool_manual as gtm  # noqa: E402


SAMPLE = {
    "name": "test-tool",
    "function_desc": "An official tool for a focused task.",
    "common_forms": ["CLI", "MCP server"],
    "target_host": "generic (no host adapter required)",
    "compatibility": {"system_impact": "No known command or port conflict.", "user_value": "Removes a repetitive manual step.", "conflicts": []},
    "options": [
        {"id": "A", "title": "Project installation", "description": "Keeps dependencies local.", "impact": "Writes project config.", "steps": ["Run the official command"], "recommended": True},
        {"id": "B", "title": "Do not install", "description": "Keep the current workflow.", "impact": "No system change.", "steps": ["Take no action"], "recommended": False},
    ],
    "selected_option": "A",
    "install": ["official install command"],
    "install_location": "project/tools/test-tool",
    "verification": ["official --version command returned the expected version"],
    "configuration": {"status": "completed", "summary": "No further setup is needed.", "steps": []},
    "triggers": {"slash": ["/documented-alias"], "natural_language": [], "cli": ["test-tool --help"], "mcp_tools": []},
    "sources": ["README: https://example.com/test-tool#usage"],
}


def test_markdown_is_the_default_portable_manual(tmp_path):
    output = gtm.generate_markdown([SAMPLE], tmp_path)
    content = output.read_text(encoding="utf-8")
    assert output.name == "test-tool.md"
    for section in ("项目是什么", "适配性评估", "安装方案", "最终选择", "配置", "来源与核验"):
        assert section in content


def test_no_trigger_is_explicit_and_never_derived(tmp_path):
    tool = {**SAMPLE, "name": "no-trigger-tool", "triggers": {"slash": [], "natural_language": [], "cli": [], "mcp_tools": []}}
    content = gtm.generate_markdown([tool], tmp_path).read_text(encoding="utf-8")
    assert "Slash 命令：官方资料未声明。" in content
    assert "自然语言触发：官方资料未声明。" in content
    assert "/no-trigger-tool" not in content


def test_documented_alias_is_not_rewritten_to_project_name(tmp_path):
    tool = {**SAMPLE, "name": "different-name"}
    content = gtm.generate_markdown([tool], tmp_path).read_text(encoding="utf-8")
    assert "/documented-alias" in content
    assert "/different-name" not in content


@pytest.mark.parametrize("field", ["sources", "install", "verification"])
def test_missing_evidence_fails_fast(tmp_path, field):
    tool = dict(SAMPLE)
    tool.pop(field)
    with pytest.raises(ValueError, match=field):
        gtm.generate_markdown([tool], tmp_path)


def test_exactly_one_recommendation_is_required(tmp_path):
    tool = {**SAMPLE, "options": [{**SAMPLE["options"][0], "recommended": False}]}
    with pytest.raises(ValueError, match="exactly one"):
        gtm.generate_markdown([tool], tmp_path)


def test_word_remains_an_optional_export(tmp_path):
    output = gtm.generate_docx([SAMPLE], tmp_path)
    assert output.name == "test-tool.docx"
    assert output.exists() and output.stat().st_size > 1000
