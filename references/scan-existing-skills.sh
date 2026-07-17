#!/usr/bin/env bash
# scan-existing-skills.sh
# 扫描所有已装的全局 + 项目级 skill，输出 name + 完整 description 为 TSV
# 用于 setup-tool 1.5 冲突评估：把目标工具子 skill 的 description 和这份输出做关键词重叠分析
#
# 用法：
#   bash references/scan-existing-skills.sh                        # 默认扫全局 + 当前项目
#   bash references/scan-existing-skills.sh --global-only          # 只扫全局
#   bash references/scan-existing-skills.sh --project <项目路径>    # 只扫指定项目
#   bash references/scan-existing-skills.sh --query <keyword>      # 只列含 keyword 的
#
# 输出：TSV 列 name<TAB>scope<TAB>description_full_path
#  --  scope: global | project | plugin
#  --  description: YAML frontmatter 里 description 字段的完整内容（保留所有触发词）

set -euo pipefail

GLOBAL_SKILLS_DIR="${HOME}/.claude/skills"
PROJECT_SKILLS_DIR=""
# 默认推断：当前工作目录或 git repo 根的 .claude/skills
if [ -d "./.claude/skills" ]; then
  PROJECT_SKILLS_DIR="./.claude/skills"
elif command -v git >/dev/null 2>&1; then
  _root=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$_root" ] && [ -d "$_root/.claude/skills" ]; then
    PROJECT_SKILLS_DIR="$_root/.claude/skills"
  fi
fi
TARGET_QUERY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --global-only) PROJECT_SKILLS_DIR="/dev/null"; shift ;;
    --project)     PROJECT_SKILLS_DIR="$2"; shift 2 ;;
    --query)       TARGET_QUERY="$2"; shift 2 ;;
    *) echo "usage: $0 [--global-only] [--project <path>] [--query <kw>]" >&2; exit 1 ;;
  esac
done

# 提取单个 SKILL.md 的 name + description（兼容 description: "..." 单行 和 description: > 多行）
extract_skill_meta() {
  local file="$1" scope="$2"
  # Windows 原生 python / *nix python3 自动选
  local py
  if command -v python >/dev/null 2>&1; then py=python
  elif command -v python3 >/dev/null 2>&1; then py=python3
  else echo "scan-existing-skills.sh: 需要 python（YAML frontmatter 解析）" >&2; return 0
  fi
  PYTHONIOENCODING=utf-8 "$py" - "$file" "$scope" <<'PYEOF'
import sys, re, os
path, scope = sys.argv[1], sys.argv[2]
try:
    text = open(path, encoding='utf-8').read()
except Exception:
    sys.exit(0)
m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
if not m:
    sys.exit(0)
fm = m.group(1)
name_m = re.search(r'^name:\s*(.+?)\s*$', fm, re.MULTILINE)
desc_m = re.search(r'^description:\s*(.+?)(?=\n[a-zA-Z_-]+:|\Z)', fm, re.MULTILINE | re.DOTALL)
if not name_m or not desc_m:
    sys.exit(0)
name = name_m.group(1).strip()
# 兼容 YAML: 去除第一个引号对 + 多行折叠为单行
desc = desc_m.group(1).strip().strip('"').strip("'")
desc = re.sub(r'\s+', ' ', desc)
print(f"{name}\t{scope}\t{desc}")
PYEOF
}

emit_from_dir() {
  local root="$1" scope="$2"
  [ -d "$root" ] || return 0
  while IFS= read -r -d '' f; do
    extract_skill_meta "$f" "$scope"
  done < <(find "$root" -mindepth 2 -maxdepth 2 -name "SKILL.md" -print0 2>/dev/null)
}

# 全局 skill（~/.claude/skills/<name>/SKILL.md 一层）
emit_from_dir "$GLOBAL_SKILLS_DIR" "global"

# 项目级 skill（默认从工作目录或 git 根推断，--project 覆盖）
if [ -n "$PROJECT_SKILLS_DIR" ] && [ -d "$PROJECT_SKILLS_DIR" ]; then
  emit_from_dir "$PROJECT_SKILLS_DIR" "project"
fi

# 已装 plugin 内的子 skill（~/.claude/plugins/cache/*/*/<version>/skills/<name>/SKILL.md）
PLUGIN_CACHE="${HOME}/.claude/plugins/cache"
if [ -d "$PLUGIN_CACHE" ]; then
  while IFS= read -r -d '' f; do
    extract_skill_meta "$f" "plugin"
  done < <(find "$PLUGIN_CACHE" -mindepth 5 -maxdepth 6 -name "SKILL.md" -path "*/skills/*" -print0 2>/dev/null)
fi
