"""Evidence-backed manual generator for setup-tool.

Markdown is the default portable artifact. Word is an optional export. The
generator rejects missing core evidence and never derives an invocation from a
project name.
"""
import argparse
import json
from pathlib import Path

OUT_DIR = Path("工具说明书")


def _require_text(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()


def _string_list(value: object, field: str, *, required: bool = False) -> list[str]:
    if value is None:
        value = []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{field} must be a list of non-empty strings")
    result = list(dict.fromkeys(item.strip() for item in value))
    if required and not result:
        raise ValueError(f"{field} must not be empty")
    return result


def _object(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def validate_tool(tool: dict) -> dict:
    """Normalize input and fail before producing an incomplete manual."""
    if not isinstance(tool, dict):
        raise ValueError("each tool must be an object")
    name = _require_text(tool, "name")
    if any(char in name for char in '\\\\/:*?\"<>|') or name in {".", ".."}:
        raise ValueError("name must be a safe filename")
    compatibility = _object(tool.get("compatibility"), "compatibility")
    configuration = _object(tool.get("configuration"), "configuration")
    triggers = tool.get("triggers", {})
    if not isinstance(triggers, dict):
        raise ValueError("triggers must be an object")
    options = tool.get("options")
    if not isinstance(options, list) or not options:
        raise ValueError("options must be a non-empty list")
    clean_options = []
    for option in options:
        option = _object(option, "each option")
        clean_options.append({
            "id": _require_text(option, "id"),
            "title": _require_text(option, "title"),
            "description": _require_text(option, "description"),
            "impact": _require_text(option, "impact"),
            "steps": _string_list(option.get("steps"), "option.steps", required=True),
            "recommended": option.get("recommended") is True,
        })
    if sum(item["recommended"] for item in clean_options) != 1:
        raise ValueError("options must contain exactly one recommended option")
    selected = _require_text(tool, "selected_option")
    if selected not in {item["id"] for item in clean_options}:
        raise ValueError("selected_option must refer to an option id")
    return {
        "name": name,
        "function_desc": _require_text(tool, "function_desc"),
        "common_forms": _string_list(tool.get("common_forms"), "common_forms", required=True),
        "target_host": _require_text(tool, "target_host"),
        "compatibility": {
            "system_impact": _require_text(compatibility, "system_impact"),
            "user_value": _require_text(compatibility, "user_value"),
            "conflicts": _string_list(compatibility.get("conflicts"), "compatibility.conflicts"),
        },
        "options": clean_options,
        "selected_option": selected,
        "install": _string_list(tool.get("install"), "install", required=True),
        "install_location": _require_text(tool, "install_location"),
        "verification": _string_list(tool.get("verification"), "verification", required=True),
        "configuration": {
            "status": _require_text(configuration, "status"),
            "summary": _require_text(configuration, "summary"),
            "steps": _string_list(configuration.get("steps"), "configuration.steps"),
        },
        "triggers": {
            "slash": _string_list(triggers.get("slash"), "triggers.slash"),
            "natural_language": _string_list(triggers.get("natural_language"), "triggers.natural_language"),
            "cli": _string_list(triggers.get("cli"), "triggers.cli"),
            "mcp_tools": _string_list(triggers.get("mcp_tools"), "triggers.mcp_tools"),
        },
        "sources": _string_list(tool.get("sources"), "sources", required=True),
        "upgrade": _string_list(tool.get("upgrade"), "upgrade"),
        "uninstall": _string_list(tool.get("uninstall"), "uninstall"),
    }


def _bullet(lines: list[str], values: list[str]) -> None:
    lines.extend(f"- {value}" for value in values)


def render_markdown(tool: dict, index: int) -> str:
    """Render one complete, reviewable manual section."""
    lines = [f"## {index}. {tool['name']}", "", "### 项目是什么", tool["function_desc"], "", "### 常见存在形态"]
    _bullet(lines, tool["common_forms"])
    lines.extend(["", "### 目标宿主", tool["target_host"], "", "### 适配性评估", f"- 与现有体系：{tool['compatibility']['system_impact']}", f"- 对你的价值：{tool['compatibility']['user_value']}"])
    if tool["compatibility"]["conflicts"]:
        _bullet(lines, ["已知冲突或注意事项：" + value for value in tool["compatibility"]["conflicts"]])
    else:
        lines.append("- 已知冲突或注意事项：未发现；仍应以来源中的版本约束为准。")
    lines.extend(["", "### 安装方案"])
    for option in tool["options"]:
        marker = "（推荐）" if option["recommended"] else ""
        lines.extend([f"#### {option['id']}. {option['title']}{marker}", option["description"], f"- 影响：{option['impact']}", "- 步骤："])
        _bullet(lines, option["steps"])
    chosen = next(item for item in tool["options"] if item["id"] == tool["selected_option"])
    lines.extend(["", "### 最终选择", f"{chosen['id']}. {chosen['title']}", "", "### 实际安装"])
    _bullet(lines, tool["install"])
    lines.extend([f"- 安装位置：{tool['install_location']}", "", "### 验证结果"])
    _bullet(lines, tool["verification"])
    lines.extend(["", "### 配置", f"- 状态：{tool['configuration']['status']}", f"- {tool['configuration']['summary']}"])
    if tool["configuration"]["steps"]:
        lines.append("- 后续步骤：")
        _bullet(lines, tool["configuration"]["steps"])
    lines.extend(["", "### 调用方式"])
    labels = {"slash": "Slash 命令", "natural_language": "自然语言触发", "cli": "CLI 调用", "mcp_tools": "MCP 工具"}
    for key, label in labels.items():
        values = tool["triggers"][key]
        lines.append(f"- {label}：{' / '.join(values) if values else '官方资料未声明。'}")
    if tool["upgrade"] or tool["uninstall"]:
        lines.extend(["", "### 升级与卸载"])
        _bullet(lines, ["升级：" + value for value in tool["upgrade"]])
        _bullet(lines, ["卸载：" + value for value in tool["uninstall"]])
    lines.extend(["", "### 来源与核验"])
    _bullet(lines, tool["sources"])
    return "\n".join(lines)


def build_filename(tools: list, suffix: str) -> str:
    return "-".join(tool["name"] for tool in tools) + suffix


def _validated(tools: list) -> list[dict]:
    if not isinstance(tools, list) or not tools:
        raise ValueError("tools must be a non-empty list")
    return [validate_tool(tool) for tool in tools]


def generate_markdown(tools: list, out_dir: Path = OUT_DIR) -> Path:
    tools = _validated(tools)
    out_dir.mkdir(parents=True, exist_ok=True)
    title = " + ".join(tool["name"] for tool in tools)
    content = f"# {title} 使用说明\n\n" + "\n\n---\n\n".join(render_markdown(tool, index) for index, tool in enumerate(tools, 1)) + "\n"
    output = out_dir / build_filename(tools, ".md")
    output.write_text(content, encoding="utf-8")
    return output


def generate_docx(tools: list, out_dir: Path = OUT_DIR) -> Path:
    """Optional Word export; python-docx is only required for this format."""
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("Word export requires python-docx; use Markdown or install python-docx") from exc
    tools = _validated(tools)
    out_dir.mkdir(parents=True, exist_ok=True)
    document = Document()
    document.add_heading(" + ".join(tool["name"] for tool in tools) + " 使用说明", level=1)
    for index, tool in enumerate(tools, 1):
        for line in render_markdown(tool, index).splitlines():
            if line.startswith("## "):
                document.add_heading(line[3:], level=2)
            elif line.startswith("### "):
                document.add_heading(line[4:], level=3)
            elif line.startswith("#### "):
                document.add_heading(line[5:], level=4)
            elif line and line != "---":
                document.add_paragraph(line)
    output = out_dir / build_filename(tools, ".docx")
    document.save(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="metadata JSON file")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    parser.add_argument("--format", choices=("markdown", "docx", "both"), default="markdown")
    args = parser.parse_args()
    with open(args.file, encoding="utf-8") as source:
        tools = json.load(source)
    if isinstance(tools, dict):
        tools = [tools]
    output_dir = Path(args.out_dir)
    outputs = []
    if args.format in ("markdown", "both"):
        outputs.append(generate_markdown(tools, output_dir))
    if args.format in ("docx", "both"):
        outputs.append(generate_docx(tools, output_dir))
    print("OK: wrote " + ", ".join(str(path) for path in outputs))


if __name__ == "__main__":
    main()
