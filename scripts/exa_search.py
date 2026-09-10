#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exa 全网语义搜索封装（零第三方 Python 依赖，经本机 mcporter 调 Exa 官方免 key MCP）。

为什么需要它：
- Exa 的 REST 端点 api.exa.ai/search 直连要 X402 付费；但官方 MCP 端点
  https://mcp.exa.ai/mcp 经 mcporter 调用免 key、直连无需代理（2026-09-07 实测）。
- 本脚本把 `mcporter call` 的人类可读输出解析成结构化 JSON，并自动回填溯源字段。

一次性配置（只需一次，已配置可跳过）：
  npx -y mcporter@latest config add exa https://mcp.exa.ai/mcp --scope home
撤销：npx -y mcporter@latest config remove exa

用法：
  # 自然语言描述"理想页面"，而不是堆关键词
  python3 exa_search.py "article explaining the sales comparison approach and comparable adjustments in real estate appraisal" --num 5
  # 找某平台讨论可加 site:
  python3 exa_search.py "discussion about China property market site:reddit.com" --num 3 --out exa.json
  python3 exa_search.py "..." --raw        # 不解析，直接看 mcporter 原始文本

输出：每条含 title/sourceUrl/published/author/highlights + 溯源字段；
搜索结果默认 sourceTier=T3，回源精读后按 references/source-schema.md 重新定级。
"""
import argparse
import datetime
import json
import re
import subprocess
import sys

MCP_PKG = "mcporter@latest"
TOOL = "exa.web_search_exa"


def run_mcporter(query, num, timeout):
    cmd = ["npx", "-y", MCP_PKG, "call", TOOL,
           "query=%s" % query, "numResults=%d" % num]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        sys.exit("[exa_search] 未找到 npx/node：Exa 通道需要 Node.js 运行 mcporter。")
    except subprocess.TimeoutExpired:
        sys.exit("[exa_search] mcporter 调用超时（%ss），可加大 --timeout。" % timeout)
    if p.returncode != 0:
        sys.exit(
            "[exa_search] mcporter 调用失败：\n%s\n%s\n"
            "若尚未配置，请先运行：\n"
            "  npx -y %s config add exa https://mcp.exa.ai/mcp --scope home"
            % (p.stdout[-800:], p.stderr[-800:], MCP_PKG))
    return p.stdout


def parse_blocks(text):
    """把 mcporter 的 Title/URL/Published/Author/Highlights 文本块解析成记录列表。"""
    results = []
    for block in re.split(r"\n-{3,}\s*\n", text.strip()):
        block = block.strip()
        if not block:
            continue

        def field(name):
            m = re.search(r"^%s:\s*(.*)$" % name, block, re.M)
            return m.group(1).strip() if m else None

        rec = {
            "title": field("Title"),
            "url": field("URL"),
            "published": field("Published"),
            "author": field("Author"),
            "highlights": [],
        }
        hm = re.search(r"^Highlights:\s*(.*)$", block, re.S)
        if hm:
            for line in hm.group(1).splitlines():
                line = line.strip()
                if line and line != "...":
                    rec["highlights"].append(line)
        if rec["url"]:
            results.append(rec)
    return results


def _na_to_none(v):
    return None if v in (None, "N/A", "") else v


def main():
    ap = argparse.ArgumentParser(
        description="Exa 语义搜索（经 mcporter 免 key MCP，输出结构化 JSON）")
    ap.add_argument("query",
                    help="自然语言描述理想页面；找特定平台可加 site:reddit.com 等")
    ap.add_argument("--num", type=int, default=5, help="返回条数，默认 5")
    ap.add_argument("--out", help="结果写文件（JSON），否则打印到 stdout")
    ap.add_argument("--raw", action="store_true", help="直接输出 mcporter 原始文本，不解析")
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()

    raw = run_mcporter(args.query, args.num, args.timeout)
    if args.raw:
        sys.stdout.write(raw if raw.endswith("\n") else raw + "\n")
        return

    items = parse_blocks(raw)
    today = datetime.date.today().isoformat()
    out = [{
        "title": it.get("title"),
        "sourceUrl": it.get("url"),
        "published": _na_to_none(it.get("published")),
        "author": _na_to_none(it.get("author")),
        "highlights": it.get("highlights", []),
        "sourceName": "Exa MCP web_search_exa",
        "sourceTier": "T3",  # 搜索结果，回源后按 source-schema 重新定级
        "collectedBy": "exa-mcporter",
        "fetchedAt": today,
    } for it in items]

    sys.stderr.write("[exa_search] parsed=%d query=%r\n" %
                     (len(out), args.query[:80]))
    if not out:
        sys.stderr.write("[exa_search] 未解析出结果，可用 --raw 查看原始输出。\n")
    text = json.dumps(out, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write("[exa_search] 已写入 %s\n" % args.out)
    else:
        sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
