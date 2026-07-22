#!/usr/bin/env python3
"""记录 setup-tool 步骤 2 的体系比较决策到 installed-tools.json。

用法：
  python scripts/log_decision.py \\
    --tool teach \\
    --source owner/repo \\
    --rating 低 \\
    --recommendation 装 \\
    --conflicts "" \\
    --complements ""
"""
import argparse
import json
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "installed-tools.json",
)


def main():
    parser = argparse.ArgumentParser(description="记录工具安装决策")
    parser.add_argument("--tool", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--rating", required=True, choices=["高", "中", "低", "无"])
    parser.add_argument("--recommendation", required=True)
    parser.add_argument("--conflicts", default="", help="逗号分隔")
    parser.add_argument("--complements", default="", help="逗号分隔")
    parser.add_argument("--user-confirmed", action="store_true")
    args = parser.parse_args()

    entry = {
        "tool": args.tool,
        "source": args.source,
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "comparison": {
            "conflicts": [x.strip() for x in args.conflicts.split(",") if x.strip()],
            "complements": [x.strip() for x in args.complements.split(",") if x.strip()],
            "rating": args.rating,
            "recommendation": args.recommendation,
        },
        "user_confirmed": args.user_confirmed,
    }

    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, encoding="utf-8") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []

    log.append(entry)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"Logged to {LOG_FILE}")


if __name__ == "__main__":
    main()
