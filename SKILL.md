---
name: setup-tool
description: 端到端装一个现成工具--确认身份->按类型路由安装->验证->生成 Word 说明书。支持 5+1 类：Claude Code skill / plugin / MCP / CLI(npm·pipx·uv tool) / GitHub release binary / 桌面 app。触发词："/setup-tool"、"装个工具"、"setup X"、"下载安装 X 并写说明书"、"配置 X 工具"、"装 X 工具"。装到说明书为止，不管沉淀。
---

# setup-tool

端到端装一个现成工具，到生成 Word 说明书为止。

## 流程（7 步）

### 1. 确认工具身份（先确认再装，避免装错）

用户给的工具名/URL 可能记错或不准。**先用 `gh` 搜 + 展示全部候选给用户挑**（无 `gh` 时用网页搜索代替）：

```bash
gh search repos "<name>" --json fullName,description,stargazersCount,pushedAt --limit 20
```

**必须把搜索结果完整列给用户看**（按 star 排序的表格），即使有 10+ 个候选也要全列。等用户挑完后再决定是否看 README/二次筛选。

确认用户挑定的目标后，**先读仓库关键文件推断创作者推荐的安装类型**，再向用户提出建议：

**读取优先级**：
1. `README.md` —— 看 Installation / Getting Started / Usage 章节
2. `SKILL.md`（如有）—— 看 frontmatter `name` / `description` 和文件位置
3. `package.json` / `pyproject.toml` / `Cargo.toml` —— 看 `bin` / `scripts` / `entry_points`
4. `marketplace.json` / `claude.json` / `plugin.json`（如有）
5. GitHub Releases 资源名 —— `.exe` / `.dmg` / `.AppImage` / 无后缀 binary

**类型推断规则**：

| 创作者意图信号 | 推荐类型 |
|---|---|
| 根目录有 `SKILL.md`，仓库名/组织含 `skill` / `claude-skills` | `skill` |
| 有 `marketplace.json` / `plugin.json`，或仓库含 `claude-plugin` / `plugin` | `plugin` |
| README 写 "MCP server" / `mcp-` 前缀 / `src/server.ts` / `stdio` 传输 | `MCP` |
| `package.json` 有 `bin` 字段 / `pipx install` / `uv tool install` / `npm install -g` | `CLI` |
| GitHub Releases 提供可执行文件，README 写 "download binary" | `binary` |
| 提供 `.dmg` / `.exe` / `.AppImage` / 桌面 GUI 截图 | `桌面 app` |

**输出格式**：

```
创作者推荐类型：<类型>
理由：<依据 README 哪句话 / 哪个文件结构>
替代可能：<如果还有 1-2 种合理安装方式，简要列出>
```

然后再问用户：**是否采用推荐类型**（5 + 1 类之一：skill / plugin / MCP / CLI / binary / 桌面 app）+ **是否全局**。

**说明书默认生成**，不询问。除非用户主动说"不要说明书"，否则步骤 6 照常执行。

**原则**：创作者推荐优先；如果创作者同时写了多种用法（例如既是 CLI 又是 MCP），按上表顺序取第一个，并在理由里说明。

**装前确认点护栏**：以下动系统文件的子动作必须显式向用户确认才走，不允许凭"合理"自作主张：

| 动作类型 | 例子 | 决策点 |
|---|---|---|
| 写/复制到 `~/.claude/skills/` 或 `~/.claude/plugins/` | 复制 repo、构造 marketplace.json | 用户点头才走 |
| 删除用户文件 | rm 已装、mv 到 trash 兜底 | 必须用户明确"删" |
| 改已装 skill 内容 | 裁剪 plugin、加 `disable-model-invocation` | 同上 |
| 构造辅助配置 | marketplace.json、hook、enabledPlugins | 必须告诉用户在哪、含什么 |

**不写盘的动作**（搜索/读文件/查 help/草拟方案）可自由做，但**方案中涉及上述任一动作用 AskUserQuestion 或文字明问**，用户未明确点头绝不执行。

### 2. 体系比较与安装建议（确认下载物后必做）

> ⚠ **触发条件**：步骤 1 中用户已经**确定具体仓库/URL** 后强制执行，不限于 skill / plugin。所有类型（skill / plugin / MCP / CLI / binary / 桌面 app）都要与现有体系比较后再建议是否安装。
>
> **注意**：此步骤**不在搜索候选阶段执行**。步骤 1 前半段只展示 `gh search` 候选列表让用户挑；用户挑定具体目标后，才进入本步骤做体系比较。

**STOP**：在以下「体系比较结果」展示给用户并得到其明确回复前，**禁止执行任何安装命令**（包括但不限于 `git clone`、`npx skills add`、`claude plugin install`、`claude plugin marketplace add`、`claude mcp add`、`npm i -g`、`uv tool install`、`pipx install`、`gh release download`、运行 `.exe`/`.dmg`/`.AppImage` 等）。若用户试图跳过，必须重申本步骤。

**目的**：避免"装完才发现和已有工具重叠/打架/多余"。先比较，再给明确建议，用户点头后再进入步骤 3。

**扫描范围**：

1. **全局 skill**：`~/.claude/skills/*` 的 `SKILL.md` name / description / 触发词
2. **项目级 skill**：当前项目 `.claude/skills/*`
3. **plugin**：`claude plugin list` 输出
4. **MCP**：`claude mcp list` 已注册 server
5. **CLI / binary**：常见安装位置 + `which <cmd>` / `where <cmd`（Windows）+ 本 skill 目录下 `installed-tools.json` 历史记录（首次使用不存在则跳过）
6. **workflow**：项目 `.claude/workflows/`、`~/.claude/workflows/`、以及全局 workflow 脚本
7. **memory（可选）**：如果你装了记忆类 MCP 或笔记系统，搜一下该工具的历史安装/评估记录；没有则跳过本项

**自动化辅助**：

对 skill / plugin 子 skill 的重叠扫描，先运行（需 bash 环境；Windows 用 Git Bash）：

```bash
bash ~/.claude/skills/setup-tool/references/scan-existing-skills.sh --query "<工具名>"
```

将输出与目标工具的 `description` / 触发词做关键词重叠分析。再把其他来源（MCP / CLI / workflow / memory）的结果合并进下表。

**比较维度**：

| 维度 | 查什么 | 判定标准 |
|---|---|---|
| **name 层** | 目标工具名 / 子 skill 名是否与已装 name 重复 | 重复 = 高冲突（CC 路由不可预期） |
| **触发词层** | 目标 description / triggers 与已有 skill 关键字重叠 | 共享 "brainstorm" / "writing" / "review" / "complete" 等 = 中冲突 |
| **功能层** | 目标核心能力属于哪个品类 | 同品类 + 高重叠 = 真冲突；同品类 + 低重叠 = 互补；不同品类 = 无关 |
| **依赖层** | 是否依赖同一后端（同一 MCP server / 同一 CLI / 同一 API key） | 已装 = 可共用；未装 = 新增维护成本 |
| **历史层** | memory 里是否装过又卸载、或评过"不引入" | 有负面记录 = 建议观望 |

**输出格式**：

```
体系比较结果：
- 已装同类/重叠：列出名字 + 重叠点
- 已装互补：列出可组合使用的已有工具
- 冲突评级：高 / 中 / 低 / 无
- 建议：装 / 不装 / 观望 / 用已有 X 替代 / 装但禁用部分子组件
- 理由：一句话
```

**建议必须明确，不能含糊**。例如：
- "建议不装：功能与 X 完全重叠，且 X 已验证稳定"
- "建议装但只暴露入口 skill：plugin 子 skill 与 Y 触发词冲突"
- "建议装：与现有 A/B 互补，无冲突"
- "建议观望：memory 显示 2026-06 评估过同类型并决定不引入"

**记录决策**：

把比较结果写入本 skill 目录下的 `installed-tools.json`（脚本自动创建；该文件是个人决策记录，不上传、不 commit）。可手动写，也可运行辅助脚本：

```bash
python ~/.claude/skills/setup-tool/scripts/log_decision.py \
  --tool "<工具名>" \
  --source "<owner/repo 或安装来源>" \
  --rating "<高/中/低/无>" \
  --recommendation "<装/不装/观望/用已有 X 替代/装但禁用部分子组件>" \
  --conflicts "<重叠项1, 重叠项2>" \
  --complements "<互补项1>" \
  --user-confirmed
```

每个条目结构（installed-tools.json 为数组）：

```json
{
  "tool": "工具名",
  "source": "owner/repo 或安装来源",
  "decided_at": "2026-07-16T16:34:00",
  "comparison": {
    "conflicts": ["重叠项1", "重叠项2"],
    "complements": ["互补项1"],
    "rating": "高/中/低/无",
    "recommendation": "装/不装/观望/用已有 X 替代/装但禁用部分子组件"
  },
  "user_confirmed": true
}
```

**用户决策**：把比较结果和建议列出来后，**用文字或 AskUserQuestion 让用户确认**。用户未明确同意前，不进入步骤 3。

**坑**：宁可列表长，不可漏比较——"基本不冲突"的草率评估和"撞名"误判都会破坏用户信任。

### 3. 按类型路由安装

查 `references/install-routes.md` 取该类型的安装命令、代理需求、验证方法、关联坑（合集见 `docs/gotchas.md`）。**如果你所在的网络访问 GitHub 受限，先设置代理环境变量**（端口换成你自己的代理端口，示例用 Clash 默认的 7890）：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
```

### 4. 验证（别信"装好了"）

按类型的验证方法实测：
- skill: `test -s ~/.claude/skills/<name>/SKILL.md`
- MCP: `claude mcp list` + **重启 CC**（MCP 装/改后必须重启才加载，见 `docs/gotchas.md`）
- CLI: `<cmd> --version`
- binary: `<binary> --version`

skill 类型还要检测多 skill 包：`ls ~/.claude/skills/ | grep <name>` 看落了几个子 skill。

**plugin 类型额外验证**（plugin install 成功 ≠ 可用）：

```bash
claude plugin list 2>&1 | grep -B1 -A6 "<plugin-name>"
# 看：
# (1) Status: ✔ enabled
# (2) 下方是否含红字 "Error: Hook load failed" / "✘" 警告
# (3) Scope 正确（user / project / local）

ls <installPath>/   # 一般是 ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/
ls <installPath>/skills/ 2>/dev/null | wc -l  # 嵌套子 skill 数量
```

嵌套 SKILL.md 陷阱：plugin 形式下 repo 根 SKILL.md 是入口，但 repo `skills/` 下嵌套的子 SKILL.md 也可能被 CC 当顶层加载。先数 skill 数，确认与预期一致（`plugin list` 的 component inventory）。

### 5. description 中文化（仅 skill / plugin，英文时触发）

> **触发条件**：类型为 `skill` 或 `plugin`，且安装后读到的 `SKILL.md` frontmatter `description` 字段以英文为主。

**目的**：涉及 `/` 斜杠命令的工具会出现在 CC 命令菜单/自动路由中，中文 description 对中文用户更友好。

**执行**：

1. 读取已安装根 `SKILL.md` 的 frontmatter `description`。
2. 判断是否为英文（简单启发：字段中中文字符占比 < 20% 视为英文）。
3. 如果是英文，**询问用户**："该工具 description 为英文：'<原文>'。是否翻译成中文？"
4. 用户同意后，将 `description` 翻译成准确、简洁的中文，**只改 description，不动其他 frontmatter 字段和正文**。
5. 对多 skill 包的每个子 SKILL.md 同样检查；询问时说明"主 skill + N 个子 skill 有英文 description"。
6. 保存修改，重新验证 skill 仍能被 CC 正常加载（`claude plugin list` / 测试 `/<name>` 触发）。

**护栏**：此步骤修改已装 skill 内容，必须用户明确"同意/改"才执行。用户拒绝或超时则跳过，直接进入步骤 6。

### 6. 生成 Word 说明书

调 `scripts/gen_tool_manual.py`，传工具元数据（JSON 文件或命令行参数）。元数据**从 SKILL.md frontmatter / README 读**，不编造。

**多 skill 包处理**：如果工具包含多个子 skill（例如 plugin 的 `skills/` 目录下嵌套多个 `SKILL.md`，或 skill 包安装后展开出多个子目录），**必须逐个读取每个子 SKILL.md**，提取其 `name`、`description`、触发词和功能描述。说明书中要为每个子 skill 单独给出功能描述，不能只写根入口 skill。

**必填字段（脚本会强制或自动派生）：**
- `name` — 工具名（决定输出文件名）
- `triggers.slash` — slash 命令列表，**必须包含主命令 `/<name>`**；缺失时脚本自动从 `name` 派生（例：`name="video-downloader"` → 自动补 `"/video-downloader"`）
- `triggers.spoken` — 口语触发词（用于自动路由）
- `function_desc` — 工具整体功能描述；多 skill 包时还要汇总各子 skill 能力
- `sub_skills` — **多 skill 包必填**：每个子 skill 的 `{name, description, triggers}` 列表
- `install_location` / `upgrade` / `uninstall` — 装哪/升级/卸载命令

**可选字段（按需分级，让说明书有重点）：**
- `must_know` — 列表，渲染成红色❗ box（必看警告/坑）
- `ref_quick` — 列表，渲染成黄色📋 box（快速参考/常用命令）
- `info` — 列表，渲染成蓝色💡 box（背景信息/为什么这样设计）

```json
{
  "name": "video-downloader",
  "function_desc": "下载主流视频网站内容；多子 skill 分别负责搜索、下载、转码",
  "sub_skills": [
    {"name": "video-downloader-search", "description": "按关键词搜索视频源", "triggers": ["/video-downloader-search", "搜视频"]},
    {"name": "video-downloader-download", "description": "执行下载并选择清晰度", "triggers": ["/video-downloader-download", "下载视频"]},
    {"name": "video-downloader-convert", "description": "下载后转码为 mp3/mp4", "triggers": ["/video-downloader-convert", "转视频"]}
  ],
  "must_know": ["某些平台未实现直链下载，需先用官方客户端缓存"],
  "ref_quick": ["env VIDEO_DOWNLOADER_OUTPUT_DIR=~/downloads"],
  "info": ["可配合笔记类工具做内容归档"]
}
```

输出默认 `~/工具说明书/<工具名>.docx`（多工具合并 `<工具1>-<工具2>.docx`；可用环境变量 `SETUP_TOOL_MANUAL_DIR` 或 `--out-dir` 覆盖）。验证：`PYTHONIOENCODING=utf-8 python -c "from docx import Document; ..."` 读回确认段数 + CJK 正常（CJK 字体设置等坑见 `docs/gotchas.md`）。

### 7. 报告

输出：工具安装位置 + 说明书路径 + 验证结果。如需沉淀经验，提醒用户手动触发他们自己的经验沉淀流程。

## 关键约束

- **先确认再装**：工具名/URL 不准时先查，不猜（名字记错会导致反复装错、排查数轮）
- **网络受限时 GitHub 操作带代理**：`git clone` / `gh release download` / `npx skills add` 可能直连失败
- **验证必跑**：不靠"装完没报错"判断，按类型实测
- **说明书触发信息从 SKILL.md/README 读**，不编造
- **不 commit**：skill 文件 + 说明书均不 commit
