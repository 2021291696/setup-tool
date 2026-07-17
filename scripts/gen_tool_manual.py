"""Parameterized Word manual generator for setup-tool.

Reads tool metadata from a JSON file (--file) and outputs a .docx.
Supports single tool or multi-tool merge.

Metadata schema (per tool):
{
  "name": "caveman",
  "function_desc": "...",
  "triggers": {
    "slash": ["/caveman", "/caveman lite|full|ultra"],
    "spoken": ["caveman mode", "less tokens"]
  },
  "sub_skills": [
    {"name": "caveman-commit", "description": "生成简洁 commit 信息", "triggers": ["/caveman-commit"]},
    {"name": "caveman-compress", "description": "压缩指定文件", "triggers": ["/caveman-compress <FILE>"]}
  ],
  "install_location": "~/.claude/skills/caveman/ (symlink to ~/.agents/skills/caveman/)",
  "upgrade": "HTTPS_PROXY=http://127.0.0.1:7890 npx -y skills add <url> --yes --global --force",
  "uninstall": "npx -y skills remove caveman 或删目录"
}

Output: 默认 ~/工具说明书/<工具名>.docx（多工具合并 <工具1>-<工具2>.docx）。
可用环境变量 SETUP_TOOL_MANUAL_DIR 或 --out-dir 覆盖。
"""
import argparse
import json
import os
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

OUT_DIR = Path(os.environ.get("SETUP_TOOL_MANUAL_DIR", str(Path.home() / "工具说明书")))
CN_FONT = "微软雅黑"


def set_cn_font(run, font_name: str = CN_FONT, size_pt: float = 11.0) -> None:
    """Set ASCII + eastAsia font on a run (CJK-aware)."""
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), font_name)
    rfonts.set(qn("w:ascii"), font_name)
    rfonts.set(qn("w:hAnsi"), font_name)


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_heading(level=level)
    run = p.add_run(text)
    set_cn_font(run, size_pt={1: 18, 2: 14, 3: 12}.get(level, 11))


def add_para(doc: Document, text: str, bold: bool = False, size: float = 11.0, icon: str = "") -> None:
    """Add a paragraph. icon is a leading emoji/symbol (e.g. "→", "⚠", "💡").

    Kept simple: no background color, no indent — visual hierarchy comes from
    the 3 priority helpers below (add_must_know/add_ref_box/add_info_box).
    """
    p = doc.add_paragraph()
    if icon:
        run_icon = p.add_run(icon + " ")
        set_cn_font(run_icon, size_pt=size)
    run = p.add_run(text)
    run.bold = bold
    set_cn_font(run, size_pt=size)


def _shade_paragraph(p, hex_color: str) -> None:
    """Apply a background shade to a paragraph (pypandoc-style fallback).

    Used to give priority boxes a faint background color for visual scanning.
    """
    ppr = p._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    ppr.append(shd)


def add_must_know(doc: Document, text: str) -> None:
    """2a: Red-tinted box, bold 13pt — non-negotiable fact user must see first."""
    p = doc.add_paragraph()
    run = p.add_run("❗ " + text)
    run.bold = True
    set_cn_font(run, size_pt=13)
    _shade_paragraph(p, "FFE5E5")  # light red


def add_ref_box(doc: Document, text: str) -> None:
    """2a: Yellow-tinted box, regular 11pt — reference info to look up later."""
    p = doc.add_paragraph()
    run = p.add_run("📋 " + text)
    set_cn_font(run, size_pt=11)
    _shade_paragraph(p, "FFF8DC")  # light yellow


def add_info_box(doc: Document, text: str) -> None:
    """2a: Blue-tinted box, italic 10pt — nice-to-know context."""
    p = doc.add_paragraph()
    run = p.add_run("💡 " + text)
    run.italic = True
    set_cn_font(run, size_pt=10)
    _shade_paragraph(p, "E8F0FE")  # light blue


def add_call_syntax(doc: Document, main_cmd: str, extra_cmds: list) -> None:
    """2c: Big bold syntax line, e.g. "→ /video-downloader <URL>".

    This is the FIRST thing the user sees in each tool's section — it answers
    "how do I call this thing?" at a glance, no scrolling required.
    """
    p = doc.add_paragraph()
    label = p.add_run("【调用方式】 ")
    label.bold = True
    set_cn_font(label, size_pt=12)
    cmd = p.add_run(main_cmd)
    cmd.bold = True
    set_cn_font(cmd, size_pt=15)
    _shade_paragraph(p, "E5F5E5")  # light green
    if extra_cmds:
        extras = p.add_run("  (alias: " + " · ".join(extra_cmds) + ")")
        set_cn_font(extras, size_pt=10)


def render_tool(doc: Document, tool: dict, idx: int) -> None:
    """Append one tool's section to the doc."""
    name = tool["name"]
    triggers = tool.get("triggers", {})

    # 2c: Auto-derive main slash command from name if missing.
    # If user-provided slash is empty, fill with "/<name>". If non-empty,
    # ensure "/<name>" is the first entry (move to front if present elsewhere).
    user_slash = list(triggers.get("slash") or [])
    main_cmd = f"/{name}"
    if not user_slash:
        slash_list = [main_cmd]
    elif main_cmd not in user_slash:
        slash_list = [main_cmd] + user_slash
    else:
        slash_list = [main_cmd] + [c for c in user_slash if c != main_cmd]

    add_heading(doc, f"{idx}. {name}", level=2)

    # 2c: Highlighted "【调用方式】" section — first thing user sees.
    add_call_syntax(doc, main_cmd, user_slash)

    # 2a/2b: Priority boxes — must_know first (red, top), then ref_quick
    # (yellow), then info (blue). These give the doc visual hierarchy
    # so the eye can scan for the most important bits.
    for item in tool.get("must_know", []):
        add_must_know(doc, item)
    for item in tool.get("ref_quick", []):
        add_ref_box(doc, item)
    for item in tool.get("info", []):
        add_info_box(doc, item)

    add_para(doc, "功能描述：", bold=True)
    add_para(doc, tool.get("function_desc", "(未提供)"))

    add_para(doc, "触发方式：", bold=True)
    if slash_list:
        # main cmd already shown above, show remaining
        for cmd in slash_list[1:]:
            add_para(doc, f"  {cmd}")
    if triggers.get("spoken"):
        add_para(doc, '  口语自动触发：' + " / ".join(f'"{w}"' for w in triggers["spoken"]))
    sub_skills = tool.get("sub_skills") or triggers.get("subskills")
    if sub_skills:
        add_para(doc, "子 skill 功能描述：", bold=True)
        for sub in sub_skills:
            if isinstance(sub, dict):
                sub_name = sub.get("name", "(未命名)")
                sub_desc = sub.get("description", "")
                sub_triggers = sub.get("triggers", [])
                trigger_str = " / ".join(str(t) for t in sub_triggers) if sub_triggers else ""
                parts = [f"  {sub_name}"]
                if trigger_str:
                    parts.append(f"— {trigger_str}")
                if sub_desc:
                    parts.append(f"：{sub_desc}")
                add_para(doc, " ".join(parts))
            else:
                # 兼容旧格式：triggers.subskills 字符串列表
                add_para(doc, f"  {sub}")

    add_para(doc, "安装位置：", bold=True)
    add_para(doc, tool.get("install_location", "(未提供)"))

    if tool.get("upgrade") or tool.get("uninstall"):
        add_para(doc, "升级与卸载：", bold=True)
        if tool.get("upgrade"):
            add_para(doc, f"  升级：{tool['upgrade']}")
        if tool.get("uninstall"):
            add_para(doc, f"  卸载：{tool['uninstall']}")


def build_filename(tools: list) -> str:
    """<工具名>.docx (single) / <工具1>-<工具2>.docx (multi)."""
    base = "-".join(t["name"] for t in tools)
    return f"{base}.docx"


def generate(tools: list, out_dir: Path = OUT_DIR) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = Document()

    if len(tools) == 1:
        add_heading(doc, f"{tools[0]['name']} 使用说明", level=1)
    else:
        names = " + ".join(t["name"] for t in tools)
        add_heading(doc, f"{names} 使用说明", level=1)

    for idx, tool in enumerate(tools, start=1):
        render_tool(doc, tool, idx)

    out_path = out_dir / build_filename(tools)
    doc.save(out_path)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="path to metadata JSON (list of tool dicts)")
    ap.add_argument("--out-dir", default=str(OUT_DIR), help="output directory")
    args = ap.parse_args()

    with open(args.file, encoding="utf-8") as f:
        tools = json.load(f)
    if isinstance(tools, dict):
        tools = [tools]

    out_path = generate(tools, Path(args.out_dir))
    print(f"OK: wrote {out_path}")


if __name__ == "__main__":
    main()
