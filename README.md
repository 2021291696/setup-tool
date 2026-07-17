# setup-tool — Claude Code 工具安装管家

> 端到端安装一个现成工具的 Claude Code skill：确认身份 → 体系比较 → 路由安装 → 实测验证 → 生成 Word 说明书。
> 核心主张：**先确认再装，先比较再装，装完必验**。

## 它解决什么问题

让 AI 装工具最常见的三个翻车点：

1. **装错**——工具名记错/撞名，装了个同名的错东西
2. **装重**——装完才发现和已有 skill/MCP 功能重叠、触发词打架
3. **假成功**——命令没报错就宣布"装好了"，实际根本调不到

本 skill 用 7 步流程把这三点都焊死。

## 支持的工具类型（5+1 类）

- Claude Code **skill**
- Claude Code **plugin**（含单 plugin 仓库缺 marketplace.json 的本地包装、多 skill 包子 skill 禁路由策略）
- **MCP** server
- **CLI**（npm / pipx / uv tool）
- GitHub release **binary**
- **桌面 app** installer

## 安装

```bash
git clone https://github.com/2021291696/setup-tool.git ~/.claude/skills/setup-tool
```

依赖：

| 依赖 | 必需性 | 用途 |
|------|--------|------|
| Claude Code | 必需 | 运行环境 |
| Python 3.x + `python-docx` | 必需 | 步骤 6 生成 Word 说明书（`pip install python-docx`） |
| bash | 必需 | 步骤 2 的冲突扫描脚本（Windows 用 Git Bash） |
| `gh` CLI | 推荐 | 步骤 1 搜仓库候选；没有则降级为网页搜索 |
| `pytest` | 仅开发 | 跑测试 |

网络受限环境：把命令里的代理端口（示例为 Clash 默认 `7890`）换成你自己的。

> **不止 Claude Code**：SKILL.md 是纯 Markdown 指令，Codex、Kimi Code 等支持 SKILL.md 的 agent CLI 也可装入各自 skills 目录使用。其中 `claude plugin` / `claude mcp` 等管理命令是 Claude Code 专有，其他 CLI 需替换为对应 CLI 的等价命令；skill 安装、冲突扫描、说明书生成等核心流程通用。

## 使用

在 Claude Code 里说 `/setup-tool`，或直接说"装个工具 / 下载安装 X 并写说明书 / 配置 X 工具"。

7 步流程：

1. **确认工具身份**：`gh search` 展示全部候选让用户挑；读 README / SKILL.md / package.json / Releases 推断创作者推荐类型
2. **体系比较与安装建议**：扫描全局/项目 skill、plugin、MCP、CLI、workflow，输出冲突评级 + 明确建议，**用户点头前禁止任何安装命令**
3. **按类型路由安装**：见 [references/install-routes.md](references/install-routes.md)
4. **验证**：按类型实测（MCP/plugin 必须重启 CC 才算数）
5. **description 中文化**（仅 skill/plugin，英文时询问）
6. **生成 Word 说明书**：默认输出 `~/工具说明书/<工具名>.docx`，可用 `SETUP_TOOL_MANUAL_DIR` 环境变量或 `--out-dir` 覆盖；多 skill 包逐个子 skill 列功能
7. **报告**：安装位置 + 说明书路径 + 验证结果

决策记录写到 skill 目录下的 `installed-tools.json`（脚本自动创建，个人数据，已在 .gitignore 中排除）。

## 目录结构

```
.
├── SKILL.md                          # skill 主文档（7 步流程与护栏）
├── scripts/
│   ├── gen_tool_manual.py            # Word 说明书生成器
│   └── log_decision.py               # 记录体系比较决策
├── tests/
│   └── test_gen_tool_manual.py       # 测试（pytest，7 个用例）
├── references/
│   ├── install-routes.md             # 5+1 类工具安装路由表
│   └── scan-existing-skills.sh       # 已有 skill/plugin 扫描器
└── docs/
    └── gotchas.md                    # 常见坑合集
```

## 本地测试

```bash
cd ~/.claude/skills/setup-tool
pip install pytest python-docx
python -m pytest tests/test_gen_tool_manual.py -v
```

## 设计要点

- **护栏式确认**：写 `~/.claude/`、删文件、改已装 skill、构造配置——都要用户明确点头
- **不编造**：说明书里的触发词/功能描述只从 SKILL.md / README 读
- **多 skill 包一等公民**：检测子 skill 数量、逐个子 skill 写说明书、子 skill 触发词冲突给禁用策略
- 常见坑（npx skills 实际落点、MCP 重启、release 代理分界、docx CJK 字体）见 [docs/gotchas.md](docs/gotchas.md)

## License

MIT — see [LICENSE](LICENSE).
