# Firecrawl 实操指南（firecrawl-guide）

> 云端网页抓取与结构化服务。官方文档 https://docs.firecrawl.dev ，定价 https://www.firecrawl.dev/pricing 。本文件记录已核实的用法、边界与成本，**数字以官方页为准，变更需回源核对**。

## 目录
1. 端点与能力
2. Keyless（零 key）边界【含实测】
3. Credit 单价与定价档位
4. 三种调用方式
5. 批量采集成本最优管线
6. 变更监控 Monitor
7. 避坑与合规
8. 扩展位

---

## 1. 端点与能力

| 端点 | 作用 | keyless |
| --- | --- | --- |
| Search | 关键词搜索并返回结果全文，2 credits/10 条 | ✅（结果数少） |
| Scrape | 单 URL → Markdown / JSON / 截图 / HTML，1 credit/页起 | ✅ |
| Parse | PDF/Word 等文档 → 文本，1 + 1/页 | ✅ |
| Map | 只列出站点全部 URL 结构，1/页 | ❌ 需 key |
| Crawl | 从入口跟随链接整站爬，1/页 | ❌ 需 key |
| Extract | 批量按 schema 提取（单请求 ≤50 URL） | ❌ 需 key |
| Interact | 云端有状态浏览器：点击/输入/滚动/翻页，会话 ≤10 分钟，2/浏览器分钟 | 仅官方客户端 keyless |
| Monitor | 定时抓取并与上次快照 diff，变化才告警，1/页/次 | ❌ 需 key |

## 2. Keyless（零 key）边界【2026-09-06 实测】

- 端点：`POST https://api.firecrawl.dev/v2/scrape`，**不带 Authorization 头**即可用；国内直连。
- 零 key 开放：Search、Scrape（含 JSON 格式）、Parse；官方 CLI/SDK 另含 Interact。
- 零 key **不开放**：Map、Crawl、独立 Extract、batch_scrape、Monitor（实测调 map 返回 "not supported by the keyless free tier"）。
- 限流：按"IP/天"的请求数上限 + credit 上限双限，超量返回 HTTP 429；具体阈值官方未公开。
- 定位：适合试用、零散单页、验证字段准确率；**不适合生产级批量**。

## 3. Credit 单价与定价档位（2026-09-06 官方定价页核实）

**每次请求单价（各档一致）**
- Scrape / Crawl / Map / Monitor：1 credit/页（Monitor 是每页每次检查 1）
- Search：2 / 10 条结果；Interact：2 / 浏览器分钟
- Scrape 叠加项：JSON 结构化 +4/页（即 5/页，实测一致）；question/highlights/PII 脱敏各 +4；PDF 解析 +1/页
- Agent（自主研究，预览）：每天 5 次免费，之后动态定价；学术 Research Index 端点免费
- 官方 FAQ：**失败请求不计费**；但返回 200 却内容为空/反爬页属"技术成功"，仍会扣，故目标站要先试抓验证

**订阅档位（年付价，月付约贵 16.7%）**

| 档位 | 价格 | credits/月 | 折合 | scrape/map/search 限流 |
| --- | --- | --- | --- | --- |
| Free | $0 免卡 | 1,000 | 500 次搜索 或 1000 页 MD 或 200 页 JSON | 10/min，2 并发 |
| Hobby | $16/月 | 5,000 | 2500 搜索 / 5000 页 | 100/min，5 并发 |
| Standard | $83/月 | 100,000 | — | 500/min，25 并发 |
| Growth | $333/月 | 500,000 | — | 5000/min |
| Scale | $599/月 | 1,000,000 | — | 仅 Scale 额度可滚存 1 个月 |

- 免费/Hobby/Standard/Growth 额度**月底清零不滚存**。
- 仅付费档可开 pay-as-you-go：$5 一包（Hobby 1000 / Standard 2000 / Growth 2500 / Scale 5000 credits），可设月度上限。
- 支付走 Stripe（信用卡/PayPal），境外订阅有汇率、可能加 VAT。
- **免费额度体感**：100 页 JSON(500)+400 页 MD(400)+50 次搜索(100)=1000；单评估项目约 200 credits → 免费档约撑 4–5 个项目/月。每日监控 N 页：N×30≤1000 → N≤33。

## 4. 三种调用方式

### 4.1 本技能脚本（推荐单页，零依赖）
```bash
python3 scripts/fc_scrape.py "URL"                      # 转 Markdown，打印
python3 scripts/fc_scrape.py "URL" --out page.md        # 写文件
python3 scripts/fc_scrape.py "URL" --json \
  --schema-file ../assets/land-deal.schema.json \
  --prompt "提取土地出让成交信息" --out row.json         # 结构化
export FIRECRAWL_API_KEY=fc-xxx                          # 有 key 后自动切换额度
```

### 4.2 REST（原生，v2）
```bash
# Markdown
curl -s -X POST "https://api.firecrawl.dev/v2/scrape" -H "Content-Type: application/json" \
  -d '{"url":"URL","formats":["markdown"]}'
# JSON 结构化（formats 内为对象；有 key 时加 -H "Authorization: Bearer fc-xxx"）
curl -s -X POST "https://api.firecrawl.dev/v2/scrape" -H "Content-Type: application/json" -d '{
  "url":"URL",
  "formats":[{"type":"json","prompt":"提取要点",
    "schema":{"type":"object","properties":{"a":{"type":"string"}}}}]}'
```
SDK：`pip install firecrawl-py`（Python）/ npm `firecrawl`（JS），注册 key 后全端点。

### 4.3 MCP 接入 AI 编程工具
```bash
# 零注册（仅 search/scrape/parse）
claude mcp add --transport http firecrawl https://mcp.firecrawl.dev/v2/mcp
# 完整工具走 OAuth（推荐）
claude mcp add --transport http firecrawl https://mcp.firecrawl.dev/v2/mcp-oauth   # 再 /mcp 登录
codex mcp add firecrawl --url https://mcp.firecrawl.dev/v2/mcp-oauth && codex mcp login firecrawl
```

## 5. 批量采集成本最优管线（建案例库标准打法）

1. **Map**（需 key）摸清站点 URL 结构与列表分页规律；大站按区域/价位/时间分片，单 job 控制 maxDepth≤10、maxPages≤1000。
2. **Crawl 先抓便宜的 Markdown（1/页）做粗筛**，剔除无关页。
3. **diff 上一轮快照**，按稳定 ID 分 new / changed / gone（gone=下架/成交，评估高价值）。
4. **只对目标页/变化页做 JSON 提取（5/页）**——这是最大成本杠杆，避免对全站每页都付结构化费用；Extract 单请求 ≤50 URL。
5. 无限滚动/动态列表优先找底层分页 API；确实要点击再用 Interact。
6. 引擎无状态，**历史快照要自己存**（本地 CSV/JSON/库），每条留 sourceUrl + scrapedAt。

## 6. 变更监控 Monitor（需 key）

- 三档：page（盯已知 URL）/ website（定时 crawl 整站，检测新增-变化-消失）/ web-scale（全网）。
- 两种 diff：`git-diff` 文本行级（适合政策/文案漂移）；`json` schema 字段级（适合价格/状态等业务信号）。
- 可设定时（如 every 30 minutes）、AI judge 过滤噪声、webhook/邮件告警；可接 n8n/Gmail/Notion。
- 成本=被监控页数 × 检查频次 × 1 credit，上线前先按月测算。

## 7. 避坑与合规

- keyless 做不了整站/批量/监控，别反复试；生产批量直接注册免费 key。
- JSON 5/页、额度月底清零；先 MD 粗筛再结构化省钱。
- 强反爬商业站（如部分中介平台）不保证成功，且须遵守其 robots/服务条款；评估用途只采公开汇总信息，不采个人信息，遵守个保法。
- 评估数字必须可回源核验，结构化结果保留 sourceUrl + fetchedAt；AI 提取字段抽样人工复核后再入正式案例库。
- 云端不持有本机登录态；需要登录的内容改走浏览器自动化，不要把账号密码交给云端。
- **LLM 结构化不是 100% 稳定（实测）**：同一页多次提取可能单位错算（亿/万、公顷/㎡）、字段错位（容积率被填成楼面价）、措辞波动、sourceUrl 误取页内导航链接、fetchedAt 误取页面日期。对策：①单位换算口径写进 schema 的 description，并保留 `*_raw` 原始表述字段供复核；②sourceUrl/fetchedAt 等客观字段由 `fc_scrape.py` 自动回填，不采信模型；③关键数值本地复算或加合理区间规则（如容积率 0.3–8、楼面价为上千的正数）；④正式入库前抽样人工复核，把 AI 输出当"初稿"而非终稿。
- **云端在境外，部分大陆政府站抓不到**：如 landchina.mnr.gov.cn 报 DNS 失败，此时改走 web.fetch 或本机浏览器，不要反复重试 Firecrawl。

## 8. 扩展位（拿到 key 后补操作实例）
- [ ] Crawl/Map/Extract 的真实脚本与分页参数（针对具体站点）
- [ ] Monitor 任务创建 CLI/API 实例与告警落地
- [ ] 快照 diff 与数据集入库脚本
- [ ] 自托管方案评估（开源 AGPL-3.0，省 per-page 但无云端反爬层、需自备服务器与 LLM）
