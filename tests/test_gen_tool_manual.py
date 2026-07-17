"""Test gate for gen_tool_manual.py -- 1 最简测试，零 framework 复杂度。"""
import json
import sys
from pathlib import Path

# Make the script importable
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import gen_tool_manual as gtm  # noqa: E402


SAMPLE_SINGLE = {
    "name": "test-tool",
    "function_desc": "A test tool for verifying the generator.",
    "triggers": {
        "slash": ["/test-tool", "/test-tool --flag"],
        "spoken": ["test mode", "use test"],
        "subskills": ["/test-sub"],
    },
    "install_location": "~/.claude/skills/test-tool/",
    "upgrade": "npx -y skills add <url> --force",
    "uninstall": "rm -rf ~/.claude/skills/test-tool/",
}

SAMPLE_MULTI = [
    {
        "name": "tool-a",
        "function_desc": "Tool A.",
        "triggers": {"slash": ["/a"], "spoken": ["a mode"], "subskills": []},
        "install_location": "~/.claude/skills/a/",
    },
    {
        "name": "tool-b",
        "function_desc": "Tool B.",
        "triggers": {"slash": ["/b"], "spoken": ["b mode"], "subskills": []},
        "install_location": "~/.claude/skills/b/",
    },
]

SAMPLE_WITH_SUB_SKILLS = {
    "name": "parent-tool",
    "function_desc": "Parent with multiple sub-skills.",
    "triggers": {"slash": ["/parent-tool"], "spoken": ["parent mode"]},
    "sub_skills": [
        {"name": "parent-tool-search", "description": "搜索资源", "triggers": ["/parent-tool-search", "搜一下"]},
        {"name": "parent-tool-download", "description": "执行下载", "triggers": ["/parent-tool-download"]},
    ],
    "install_location": "~/.claude/skills/parent-tool/",
}


def test_single_tool_filename(tmp_path):
    out = gtm.generate([SAMPLE_SINGLE], tmp_path)
    assert out.name == "test-tool.docx"
    assert out.exists()
    assert out.stat().st_size > 1000


def test_multi_tool_filename(tmp_path):
    out = gtm.generate(SAMPLE_MULTI, tmp_path)
    assert out.name == "tool-a-tool-b.docx"
    assert out.exists()


def test_docx_has_paragraphs(tmp_path):
    out = gtm.generate([SAMPLE_SINGLE], tmp_path)
    from docx import Document
    d = Document(str(out))
    texts = [p.text.strip() for p in d.paragraphs if p.text.strip()]
    assert any("test-tool" in t for t in texts)
    assert any("功能描述" in t for t in texts)
    assert any("/test-tool" in t for t in texts)
    assert any("升级与卸载" in t for t in texts)
    assert len(texts) >= 5


def test_build_filename_single():
    assert gtm.build_filename([SAMPLE_SINGLE]) == "test-tool.docx"


def test_build_filename_multi():
    assert gtm.build_filename(SAMPLE_MULTI) == "tool-a-tool-b.docx"


def test_heading_numbering(tmp_path):
    """First tool should be '1.', second '2.' (regression: idx logic)."""
    out = gtm.generate(SAMPLE_MULTI, tmp_path)
    from docx import Document
    d = Document(str(out))
    headings = [p.text.strip() for p in d.paragraphs if p.text.strip().startswith(("1.", "2."))]
    assert "1. tool-a" in headings, f"expected '1. tool-a', got {headings}"
    assert "2. tool-b" in headings, f"expected '2. tool-b', got {headings}"


def test_sub_skills_rendered(tmp_path):
    """New sub_skills format: each sub-skill name, description and triggers appear."""
    out = gtm.generate([SAMPLE_WITH_SUB_SKILLS], tmp_path)
    from docx import Document
    d = Document(str(out))
    texts = [p.text.strip() for p in d.paragraphs if p.text.strip()]
    assert any("子 skill 功能描述" in t for t in texts)
    assert any("parent-tool-search" in t for t in texts)
    assert any("搜索资源" in t for t in texts)
    assert any("/parent-tool-search" in t for t in texts)
    assert any("parent-tool-download" in t for t in texts)
    assert any("执行下载" in t for t in texts)
