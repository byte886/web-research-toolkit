#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firecrawl 单页抓取/结构化封装（仅用 Python 标准库，零第三方依赖）。

默认 keyless：无需注册，按 IP/天限流，仅支持单页 scrape（Markdown/JSON）。
设置环境变量 FIRECRAWL_API_KEY 或传 --key 后，自动改用注册额度（仍走单页端点；
整站 crawl/map、批量 extract、monitor 需另调对应端点，见 references/firecrawl-guide.md）。

用法示例：
  # 单页转 Markdown，打印到屏幕
  python3 fc_scrape.py "https://example.com"
  # 转 Markdown 并写文件
  python3 fc_scrape.py "https://example.com" --out page.md
  # 按 JSON Schema 结构化（keyless 也可用，约 5 credits/页）
  python3 fc_scrape.py "https://某公告页" --json \
      --schema-file ../assets/land-deal.schema.json \
      --prompt "提取土地出让成交信息，页面没有的字段留 null" --out row.json
  # 网络确需代理时（Firecrawl API 国内通常直连，无需代理）
  python3 fc_scrape.py "https://example.com" --proxy http://127.0.0.1:7890

运行信息（creditsUsed、状态码）打到 stderr，正文打到 stdout/文件，便于管道处理。
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.firecrawl.dev/v2/scrape"


def post_scrape(body, key=None, proxy=None, timeout=120):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    opener = urllib.request.build_opener(*handlers)
    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
    try:
        with opener.open(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        sys.exit("[fc_scrape] HTTP %s: %s" % (e.code, detail[:600]))
    except urllib.error.URLError as e:
        sys.exit("[fc_scrape] 网络错误: %s\nFirecrawl API 国内通常直连；如确需外网代理可加 --proxy。" % e.reason)


def main():
    ap = argparse.ArgumentParser(description="Firecrawl 单页抓取/结构化（默认 keyless，零依赖）")
    ap.add_argument("url", help="目标页面 URL")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON（配合 --schema-file/--prompt）")
    ap.add_argument("--schema-file", help="JSON Schema 文件路径")
    ap.add_argument("--prompt", default="", help="结构化提取提示词")
    ap.add_argument("--with-html", action="store_true", help="Markdown 模式下同时取原始 HTML")
    ap.add_argument("--out", help="输出文件路径；不指定则打印到 stdout")
    ap.add_argument("--key", default=os.environ.get("FIRECRAWL_API_KEY"),
                    help="API key，默认读环境变量 FIRECRAWL_API_KEY；都没有则走 keyless")
    ap.add_argument("--proxy", default=None, help="代理，如 http://127.0.0.1:7890；默认直连")
    ap.add_argument("--timeout", type=int, default=120)
    args = ap.parse_args()

    if args.json:
        fmt = {"type": "json",
               "prompt": args.prompt or "Extract structured data from the page; leave missing fields null."}
        if args.schema_file:
            with open(args.schema_file, "r", encoding="utf-8") as f:
                fmt["schema"] = json.load(f)
        formats = [fmt]
    else:
        formats = ["markdown"] + (["html"] if args.with_html else [])

    result = post_scrape({"url": args.url, "formats": formats},
                         key=args.key, proxy=args.proxy, timeout=args.timeout)

    if not result.get("success"):
        sys.exit("[fc_scrape] 抓取失败: %s" % result.get("error"))

    data = result.get("data", {}) or {}
    meta = data.get("metadata", {}) or {}
    mode = "api-key" if args.key else "keyless"
    sys.stderr.write("[fc_scrape] ok mode=%s status=%s creditsUsed=%s url=%s\n" % (
        mode, meta.get("statusCode"), meta.get("creditsUsed"), args.url))

    if args.json:
        payload = data.get("json")
        if payload is None:
            sys.exit("[fc_scrape] 返回中没有 json 字段，请检查 prompt/schema 或页面内容。")
        # 溯源字段以本次请求为准强制回填，不信任模型从页面导航里抓到的链接
        fixed = []
        if isinstance(payload, dict):
            if "sourceUrl" in payload and payload.get("sourceUrl") != args.url:
                payload["sourceUrl"] = args.url
                fixed.append("sourceUrl")
            if "fetchedAt" in payload:
                # 抓取时间是客观值，无条件以本机当天为准，不采信模型从页面推断的日期
                payload["fetchedAt"] = datetime.date.today().isoformat()
                fixed.append("fetchedAt")
        if fixed:
            sys.stderr.write("[fc_scrape] 已自动回填溯源字段: %s\n" % ", ".join(fixed))
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = data.get("markdown", "")
        if not text:
            sys.exit("[fc_scrape] 返回 Markdown 为空（可能被反爬或页面无正文），按溯源规则如实记录，勿填充。")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write("[fc_scrape] 已写入 %s（%s 字符）\n" % (args.out, len(text)))
    else:
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))


if __name__ == "__main__":
    main()
