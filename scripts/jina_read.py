#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jina Reader：任意 URL → 干净 Markdown（零第三方 Python 依赖，底层用系统 curl）。

实测固化的坑（2026-09-07）：
1) r.jina.ai 国内直连超时，默认走本机代理 http://127.0.0.1:7890
   （--proxy 换端口，--no-proxy 直连）；
2) 目标 URL 必须百分号编码后拼到 r.jina.ai/ 之后，直接嵌 https:// 会被工具层拦截；
3) Python urllib 经 ClashX 代理访问 r.jina.ai 会 SSL EOF，而系统 curl 走同一代理稳定
   → 本脚本底层统一用 curl。

定位：web.fetch / Firecrawl 都失败时的第三个"读网页"通道，海外网页效果好；
Jina 是境外云端取页，抓国内 gov.cn 的效果未验证，不保证。

用法：
  python3 jina_read.py "https://en.wikipedia.org/wiki/Real_estate_appraisal"
  python3 jina_read.py "https://example.com" --out page.md
  python3 jina_read.py "https://..." --proxy http://127.0.0.1:7897
  python3 jina_read.py "https://..." --no-proxy
"""
import argparse
import shutil
import subprocess
import sys
import time
import urllib.parse

JINA_BASE = "https://r.jina.ai/"


def fetch(url, proxy, timeout):
    if not shutil.which("curl"):
        sys.exit("[jina_read] 未找到系统 curl；本脚本依赖 curl 走代理取页。")
    req_url = JINA_BASE + urllib.parse.quote(url, safe="")  # 坑②：整体百分号编码
    cmd = ["curl", "-sS", "-m", str(timeout)]
    if proxy:                                              # 坑①：国内默认走代理
        cmd += ["-x", proxy]
    cmd += ["-w", "\n%{http_code}", req_url]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
    except subprocess.TimeoutExpired:
        sys.exit("[jina_read] curl 超时（%ss）。" % timeout)
    if p.returncode != 0:
        hint = "" if proxy else "\n国内访问 r.jina.ai 通常需要代理（默认 127.0.0.1:7890）。"
        sys.exit("[jina_read] curl 失败(code=%s): %s%s" %
                 (p.returncode, p.stderr.strip()[-400:], hint))
    body, _, code = p.stdout.rpartition("\n")  # 末行是 -w 写入的状态码
    return body, code.strip(), time.time() - t0, (proxy or "DIRECT")


def main():
    ap = argparse.ArgumentParser(
        description="Jina Reader：任意 URL → 干净 Markdown（默认走本机代理、自动编码）")
    ap.add_argument("url", help="目标页面 URL")
    ap.add_argument("--proxy", default="http://127.0.0.1:7890",
                    help="HTTP 代理，默认 http://127.0.0.1:7890")
    ap.add_argument("--no-proxy", action="store_true", help="直连，不走代理")
    ap.add_argument("--out", help="写文件，否则打印到 stdout")
    ap.add_argument("--timeout", type=int, default=45)
    args = ap.parse_args()

    proxy = None if args.no_proxy else args.proxy
    md, code, secs, via = fetch(args.url, proxy, args.timeout)
    if code != "200":
        sys.exit("[jina_read] HTTP %s，返回：%s" % (code, md[:300]))
    if not md.strip():
        sys.exit("[jina_read] 返回为空（可能被反爬），按溯源规则如实记录，勿填充。")
    sys.stderr.write("[jina_read] HTTP %s | %d chars | %.1fs | via=%s | url=%s\n" %
                     (code, len(md), secs, via, args.url))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(md)
        sys.stderr.write("[jina_read] 已写入 %s\n" % args.out)
    else:
        sys.stdout.write(md if md.endswith("\n") else md + "\n")


if __name__ == "__main__":
    main()
