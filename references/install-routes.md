# 安装路由表（5+1 类工具）

每类含 4 字段：安装命令 / 代理需求 / 验证 / 关联坑（合集见 `docs/gotchas.md`）。

## 通用前置（所有类型）

**先确认工具身份再装**：

```bash
gh search repos "<name>" --json fullName,description,stargazersCount,pushedAt
gh repo view <owner>/<name> --json description,stargazerCount,primaryLanguage
gh api repos/<owner>/<name>/readme --jq '.content' | base64 -d | head -50
```

（无 `gh` CLI 时用网页搜索 + 直接读仓库页面代替。）

**网络受限环境先设代理**（端口换成你自己的代理端口，示例用 Clash 默认的 7890）：

```bash
export HTTPS_PROXY=http://127.0.0.1:7890
export HTTP_PROXY=http://127.0.0.1:7890
```

（`gh api` / `gh search` / `gh repo view` 走 API 通常不需要代理；`git clone` / release 二进制下载 / `npx skills add` 需要的概率高。）

下文命令中的 `$PROXY` 均指 `HTTPS_PROXY=http://127.0.0.1:7890 HTTP_PROXY=http://127.0.0.1:7890` 这对环境变量前缀，按你的网络情况决定加不加、换成什么端口。

---

## 1. Claude Code skill

**安装**：

```bash
$PROXY npx -y skills add https://github.com/<owner>/<repo>.git --yes --global
```

fallback（npx skills 不可用）：

```bash
$PROXY git clone https://github.com/<owner>/<repo>.git ~/.claude/skills/<name>
```

**代理**：网络受限时需要（git clone 易失败）。
**验证**：`test -s ~/.claude/skills/<name>/SKILL.md && echo OK`
**多 skill 包检测**：`ls ~/.claude/skills/ | grep <name>`（有的包会展开成多个子 skill）
**坑**：见 `docs/gotchas.md`「npx skills add」（实际安装到 `~/.agents/skills/` + symlink，验证时别找错位置）

---

## 2. MCP server

**安装**：

```bash
claude mcp add <name> -s user -- <command> [args]
# 或带 env
claude mcp add <name> -s user -e KEY=VALUE -- <command>
```

**代理**：视源（npm 装的 MCP 包可能需要）。
**验证**：`claude mcp list`（看到 <name>）+ **重启 CC**（装/改后必须重启，agent 才能调到工具——`docs/gotchas.md`「MCP 重启」）

---

## 3. CLI（npm / pipx / uv tool）

### npm
**安装**：`npm i -g <package>`（慢则用镜像：`npm i -g <pkg> --registry=https://registry.npmmirror.com`）
**验证**：`<cmd> --version`

### python
**安装**：`uv tool install <package>` 或 `pipx install <package>`
**验证**：`<cmd> --version`

**代理**：可选（npm 慢用 npmmirror，pip 慢用 `https://pypi.tuna.tsinghua.edu.cn/simple`）。
**坑**：pipx 装的命令在 `~/.local/bin/`，确认在 PATH。

---

## 4. GitHub release binary

**安装**：

```bash
$PROXY gh release download --repo <owner>/<repo> --pattern "<binary-asset>" --dir <target-dir>
```

（`gh release download` 的 API 请求本身不需要代理，但二进制文件走 GitHub CDN，网络受限时下载阶段需要代理。）

**代理**：网络受限时需要。
**验证**：`<target-dir>/<binary> --version`
**坑**：见 `docs/gotchas.md`「release 下载代理」

---

## 1.b Claude Code plugin

**安装**（标准情况：repo 本身就是 marketplace 或市场里有 source）：

```bash
$PROXY claude plugin marketplace add <owner>/<repo>           # 添加 marketplace 源
claude plugin install <plugin-name>@<marketplace-name> --scope user
claude plugin enable <plugin-name>
```

**代理**：网络受限时必须（拉源码）。
**验证**：`claude plugin list`（看到 `✔ enabled`）+ **grep 输出是否含 `Error: Hook load failed`/`✘` 等红字警告**（成功 ≠ 可用）。
**多 skill 包检测**：`plugin list` 输出的 Version 行下方列 component inventory 数量。
**坑**：装 / enable / update 后都需重启 CC 才生效（`docs/gotchas.md`「MCP 重启」同理）。

### 1.b.1 单 plugin 仓库（缺 marketplace.json）的本地包装

很多作者只发布 `plugin.json`（plugin 清单），**没有 `marketplace.json`**。而 `claude plugin install` 只能从 marketplace 装。这种情况要本地包装：

**步骤**：
1. clone 到稳定源（如 `~/.claude/plugins/repos/<name>/`）
2. 在源的 `.claude-plugin/marketplace.json`（新建）：
   ```json
   {
     "name": "<marketplace-名>",
     "description": "Local marketplace wrapper for <owner>/<repo>",
     "owner": { "name": "local" },
     "plugins": [
       {
         "name": "<plugin-name-来自-plugin.json>",
         "description": "<作者原描述>",
         "version": "<version>",
         "source": "./"
       }
     ]
   }
   ```
3. `claude plugin marketplace add <源绝对路径> --scope user`
4. `claude plugin install <plugin-name>@<marketplace-名> --scope user`
5. `claude plugin enable <plugin-name>`
6. **重启 CC**

**名称冲突**：marketplace name 必须 unique（`claude plugin marketplace list` 看现有列表）；plugin name 也要 unique。

### 1.b.2 多 skill 包触发词污染 + disable 子 skill 策略

多 skill 包（有的 plugin 含十几个子 skill）以 plugin 形式装时，**所有子 skill 都被 CC 当独立 skill 加载**，可能与已有 skill 触发词重叠。

**激进策略（推荐）**：除主入口 skill 外，**所有子 skill 加 `disable-model-invocation: true`**：

```bash
# 批量给子 skill 加 disable（在源 repo 改 frontmatter）
python -c "
import os, glob
base = r'<path-to-source>/skills'
for f in glob.glob(os.path.join(base, '*', 'SKILL.md')):
    text = open(f, encoding='utf-8').read()
    if 'disable-model-invocation:' in text:
        continue
    parts = text.split('---', 2)
    if len(parts) >= 3:
        new = '---' + parts[1].rstrip('\n') + '\ndisable-model-invocation: true\n---' + parts[2]
        open(f, 'w', encoding='utf-8').write(new)
"
```

**效果**：子 skill 不进入自动路由，只被主 skill 编排调用或 `/子 skill 名` 显式触发。零冲突。

**代价**：`claude plugin update` 拉新版本会覆盖 disable 补丁，需重跑上面脚本。

### 1.b.3 plugin.json 的 hooks 字段陷阱

CC 自动加载 plugin 根 `hooks/hooks.json`。**`plugin.json` 里不要再写 `"hooks": "./hooks/hooks.json"`**，否则报：
> Hook load failed: Duplicate hooks file detected ... The standard hooks/hooks.json is loaded automatically, so manifest.hooks should only reference additional hook files.

裸 `plugin.json`（只声明 `name`/`version`/`description`/`skills`/其他元数据）即可。

---

## 5. 桌面 app installer

**安装**：下载 installer（`.exe`/`.msi`）+ 运行（silent 参数：`/S` 或 `/quiet`）。

```bash
$PROXY curl -L -o <installer>.exe <download-url>
# silent install
./<installer>.exe /S
```

**代理**：网络受限时需要（installer 下载）。
**验证**：桌面快捷方式存在 / `where <app>`（Windows）/ 注册表项。
**坑**：silent 参数因 installer 而异（NSIS `/S`、MSI `/quiet`、Inno Setup `/VERYSILENT`）。
