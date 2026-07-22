# setup-tool

跨 AI 编程宿主的工具接入 skill：先核验项目，再判断是否值得安装、给出选择与推荐、安装配置、最后生成可追溯说明书。

它可用于 Claude Code、Codex、Hermes、OpenClaw 和普通项目环境。平台专有命令只有在官方资料和 adapter 均已验证时才会使用；未知平台安全回退到通用 CLI/MCP/项目依赖方案。

## 核心流程

1. 查询并核验具体项目及官方来源。
2. 说明项目用途和常见形态，检查与已有体系的冲突及实际价值。
3. 给出至少两个选择（包含“不安装”）和唯一推荐；用户决定后才执行。
4. 安装、真实验证，并自动完成安全可逆的配置或逐步教学。
5. 默认生成 Markdown 使用说明；可选生成 Word。

## 安装

将此目录放入目标宿主的 skill 目录，具体目录请以宿主官方文档为准：

```bash
git clone https://github.com/2021291696/setup-tool.git <your-skill-directory>/setup-tool
```

若宿主不支持 skill 文件，仍可把 `SKILL.md` 作为工具接入流程的可读指令使用。

## 说明书格式

`scripts/gen_tool_manual.py` 默认生成 `<工具名>.md`。它强制记录项目用途、常见形态、兼容性判断、安装选项与推荐、最终选择、实际安装/验证/配置、真实调用方式及来源。

Word 是可选导出：

```bash
python scripts/gen_tool_manual.py --file metadata.json --out-dir manuals --format both
```

`--format` 支持 `markdown`（默认）、`docx`、`both`。Word 导出需要 `python-docx`；Markdown 不需要额外 Python 包。

## 体系冲突扫描

扫描必须使用**已核验**的 skill 根目录，并提供具体查询词；不会默认枚举用户主目录或输出全部技能：

```bash
python scripts/scan_existing_tools.py --root "<verified-skill-root>" --query "<tool-name>"
```

默认 JSON 输出最多 20 条结果。不可访问的目录会写入结果中的 `errors`，命令仍安全返回，供 agent 解释下一步。

## 触发词原则

没有官方证据的 slash、自然语言、CLI 或 MCP 调用方式会明确写为“官方资料未声明”。生成器绝不从项目名派生 `/项目名`，也不把安装命令当触发词。

## 开发

```bash
python -m pytest tests/test_gen_tool_manual.py -q
```

## 贡献 adapter

见 [adapters/README.md](adapters/README.md)。不要加入未经官方资料核验的目录、配置键或平台命令。

## License

MIT — see [LICENSE](LICENSE).
