#!/usr/bin/env python3
"""Safely scan explicit skill roots for potential naming conflicts.

The scanner intentionally has no default home-directory path. A caller must
provide both a verified root and a query, which prevents accidental dumping of
every local skill to an agent tool call.
"""
import argparse
import json
import re
import sys
from pathlib import Path


def configure_utf8_output() -> None:
    """Keep JSON readable when a Windows agent captures stdout through a pipe."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def parse_skill(path: Path) -> dict | None:
    """Extract only frontmatter fields needed for a conflict review."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return None
    frontmatter = match.group(1)
    name_match = re.search(r"^name:\s*(.+?)\s*$", frontmatter, re.MULTILINE)
    description_match = re.search(
        r"^description:\s*(.+?)(?=\n[a-zA-Z_-]+:|\Z)", frontmatter, re.MULTILINE | re.DOTALL
    )
    if not name_match:
        return None
    description = description_match.group(1).strip().strip("\"").strip("'") if description_match else ""
    return {"name": name_match.group(1).strip(), "description": re.sub(r"\s+", " ", description)}


def scan(roots: list[Path], query: str, max_results: int = 20) -> dict:
    """Return matching skill metadata without failing on inaccessible roots."""
    needle = query.casefold().strip()
    results, errors = [], []
    for root in roots:
        try:
            if not root.is_dir():
                errors.append(f"not a readable directory: {root}")
                continue
            files = sorted(root.rglob("SKILL.md"))
        except OSError as exc:
            errors.append(f"cannot scan {root}: {exc}")
            continue
        for path in files:
            data = parse_skill(path)
            if not data or needle not in (data["name"] + " " + data["description"]).casefold():
                continue
            data["path"] = str(path)
            results.append(data)
            if len(results) >= max_results:
                return {"query": query, "skills": results, "errors": errors, "truncated": True}
    return {"query": query, "skills": results, "errors": errors, "truncated": False}


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Scan explicit skill roots for a query")
    parser.add_argument("--root", action="append", required=True, help="verified skill root; repeat for more roots")
    parser.add_argument("--query", required=True, help="non-empty conflict query")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--format", choices=("json", "tsv"), default="json")
    args = parser.parse_args()
    if not args.query.strip() or args.max_results < 1:
        parser.error("--query must not be empty and --max-results must be positive")
    report = scan([Path(root) for root in args.root], args.query, args.max_results)
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for skill in report["skills"]:
            print(f"{skill['name']}\t{skill['description']}\t{skill['path']}")
        for error in report["errors"]:
            print(f"ERROR\t{error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
