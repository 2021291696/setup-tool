# 工具接入常见坑

## 不要把宿主细节当成通用事实

Claude Code、Codex、Hermes、OpenClaw 的 skill 路径、MCP 注册命令和刷新机制可能不同。仅当 adapter 有官方来源和实际验证时才写入这些命令；否则使用 generic 路线并说明宿主接入待验证。

## 冲突扫描必须是窄查询

不要扫描默认主目录，更不要把全部已安装 skill 输出给模型。使用 `scripts/scan_existing_tools.py` 时必须提供已核验根目录和具体查询词；它最多返回 20 条结果，并将不可访问目录作为结构化 `errors` 返回。

## 触发方式只能引用证据

没有官方证据的 slash、自然语言、CLI 或 MCP 调用方式应写为“官方资料未声明”。项目名、安装命令和目录名都不是触发词。

## Word 导出是可选项

Markdown 是默认说明书，因此不依赖 `python-docx`。仅在用户明确要求 `.docx` 时安装或使用 `python-docx`，并在生成后回读确认文件存在和文本正常。
