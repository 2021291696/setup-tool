# Gotchas — 安装工具常见坑合集

> 这些是实战中踩出来的坑，SKILL.md 和 install-routes.md 里的「坑」引用都指向这里。
> 欢迎补充。

## npx skills add 的实际安装位置

用 `npx -y skills add <repo> --global` 装 skill 时：

- 实际文件落在 `~/.agents/skills/<name>/`，`~/.claude/skills/<name>` 是 **symlink**
- 验证时两个位置都要看：`ls -la ~/.claude/skills/<name>` 确认链接有效 + `test -s ~/.claude/skills/<name>/SKILL.md`
- 某些环境下安装输出会误报 "PromptScript" 类警告——只要 SKILL.md 存在且 CC 能列出，即可忽略
- 一个 repo 可能展开成多个子 skill（装完 `ls ~/.claude/skills/ | grep <name>` 数一下）

## MCP 装/改后必须重启 CC

`claude mcp add` 之后 `claude mcp list` 能立刻看到新 server、甚至显示 Connected，但 **agent 会话内的工具列表是启动时加载的**——不重启 CC，模型根本调不到新 MCP 的工具。

- add / remove / 改配置 / update 都要重启
- 「Connected ≠ agent 能调工具」
- 同理：`claude plugin install` / `enable` / `update` 后也要重启

## GitHub release 下载的代理分界

网络受限环境下，`gh` 的行为分两段：

| 操作 | 走什么 | 需要代理吗 |
|------|--------|-----------|
| `gh api` / `gh search` / `gh repo view` / `gh release download` 的**清单请求** | GitHub API | 通常不需要 |
| `gh release download` 的**二进制文件本体** | GitHub CDN | 大概率需要 |
| `git clone` / `npx skills add` | git over HTTPS | 大概率需要 |

所以 `gh release download` 建议整条命令带代理前缀，最省心。

## Word 说明书（python-docx）的 CJK 字体

生成中文 docx 时只设 `run.font.name = "微软雅黑"` 不够——Word 对东亚字符走单独的 `w:eastAsia` 字体槽，不设就会回退到默认字体、中西文混排破相。

正确做法（`gen_tool_manual.py` 的 `set_cn_font` 已内置）：

```python
rpr = run._element.get_or_add_rPr()
rfonts = OxmlElement("w:rFonts")
rfonts.set(qn("w:eastAsia"), "微软雅黑")
rfonts.set(qn("w:ascii"), "微软雅黑")
rfonts.set(qn("w:hAnsi"), "微软雅黑")
```

生成后的验证也要做：用 `python-docx` 读回文件，确认段落数 > 0 且中文字符正常（不是乱码/方块）——别只看文件生成了没有。

非 Windows 系统没有「微软雅黑」时 Word 会自动 fallback，不影响内容正确性；在意观感可把 `CN_FONT` 常量换成本机有的中文字体。
