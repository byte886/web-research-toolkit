# 取数通道选型（channel-selection）

> 调研时先读本文件选定通道，再采集。原则：**能用低成本通道解决就不上重通道；要穷尽/结构化/反复更新才上 Firecrawl。**

## 本文导航
- 本页：通道总览表、决策树、国内外网络分流表
- `channels-detail.md`：各通道用法与实测边界（§3.1–3.9）
- `network-and-language.md`：检索语言策略（先英后中）、海外 AI 搜索 API 扩展位
- `field-test-notes.md`：历次实测事实台账、待接入通道清单（启用前先只读实测一条）

---

## 1. 通道总览与定位

| 通道 | 本质 | 最擅长 | 产出 | 成本 |
| --- | --- | --- | --- | --- |
| 内置联网搜索 general_search | 关键词→搜索结果摘要+链接 | 探索定位、事实速查、最新动态 | 带链接的文本/摘要 | 已含在会员，边际 0 |
| 垂直检索（scholar/legal/finance/medical/enterprise） | 专业库定向检索 | 学术、中国法规、金融行情、医疗、企业内部资料 | 结构化专业结果 | 已含 |
| web.fetch | 对已知 URL 服务端取全文 | 精读单页、在线 PDF/长文分页读完 | 页面全文/片段 | 0 |
| Firecrawl | 云端真实浏览器渲染+LLM 结构化 | 整站批量、JS 动态页、固定字段 JSON、监控 | Markdown/JSON 数据集 | 免费 1000 credits/月，超出付费 |
| 浏览器自动化（browser/computer-use） | 操作真实浏览器 | 可视化点击、登录后内容、人工接管 | 页面内容/截图 | 0，但占人工 |
| Jina Reader（脚本 jina_read.py，已验证） | r.jina.ai 任意 URL→干净 Markdown | web.fetch/Firecrawl 都失败时的第三读网页通道，海外页效果好 | Markdown | 免费无 key；脚本自动探测本机代理、自动 URL 编码 |
| Exa 语义搜索（脚本 exa_search.py，已验证） | 免 key MCP，自然语言语义检索，可间接摸 Reddit 讨论 | 英文/海外资料找相似、找专业文章、社媒讨论线索 | 结构化 JSON（含溯源） | 免费免 key、直连无需代理 |
| 社交 UGC 平台（待接入） | 小红书/微博/公众号/X 等，经 OpenCLI/各 MCP + 登录态读取 | 平台内舆情口碑（评估中仅作 T4 线索） | 平台文本 | 需 Docker/账号 Cookie/代理、有封号风险，需用户介入（见 field-test-notes） |
| **付费社群：生财有术 scys-mcp（已验证）** | 官方 MCP 连接器，OAuth 后以本人身份读会员私有内容 | 精华帖/风向标、项目库、航海手册、圈友发言、线下局、个人足迹，AI 亦仁做决策判断 | 帖子全文/AI 摘要/字段 + 原文链接 | 需生财会员；官方接口不封号；详见 `scys-mcp-guide.md` |
| 其它已验证公开通道 gh/RSS/V2EX | gh 读公开仓库；RSS/Atom 订阅；V2EX 公开 API | 开源情报、行业更新订阅、技术社区 | 文本/JSON/XML | 免费；RSS/V2EX 境外或需代理 |

**关键区别（搜索 vs Firecrawl）**：搜索是"我问你答"，给基于索引的摘要，快但可能滞后、不保证穷尽、字段不统一；Firecrawl 是"采集管线"，对指定 URL/入口实时渲染、逐页产出统一结构，可沉淀成可复用数据集。二者互补：Firecrawl 把数据搬下来洗干净，模型负责分析与写作。

## 2. 决策树（自上而下）

1. 需要本机登录态 / 付费墙 / 验证码 / 视频流？
   - 是「生财有术」站内会员内容 → **走官方 scys-mcp 连接器（见 scys-mcp-guide.md），不用浏览器爬、不碰 Cookie**。
   - 是其它登录态 / 付费墙 / 验证码 → 浏览器自动化技能（登录交用户接管），**不在本技能范围展开**。
   - 否（公开网页）↓
2. 只是搞懂问题、页面 <20、一次性、不要求固定字段？
   - 是 → 内置搜索；领域问题走垂直检索。
   - 否（要批量 / 统一字段 / 反复用）↓
3. 已有明确 URL，只是要这几页全文？
   - 是 → web.fetch 精读（少量页优先它，不花 Firecrawl credit）。
4. 要整站、JS 动态、固定字段 JSON、定期更新？
   - 零散单页 / 验证可行性 → Firecrawl **keyless 单页**（`fc_scrape.py`）。
   - 整站批量 / 监控 → 注册免费档拿 key，走 Crawl/Map/Extract/Monitor。
5. 找英文/海外资料、"找相似"、Reddit 等讨论线索？→ Exa 语义搜索（`exa_search.py`，免 key、直连）。
6. 已知海外 URL，但 web.fetch/Firecrawl 都读不下来？→ Jina Reader（`jina_read.py`，走代理）。

## 4. 国内外网络分流（重要）

| 目标 | 通道 |
| --- | --- |
| Google、YouTube、X 等被墙站点 | 先开代理（端口以本机实测为准：ClashX 多为 7890、ClashVerge 多为 7897） |
| 国内政府/公开站点（土地、统计、自规局等） | 直连，走代理反而可能失败 |
| **Firecrawl API（api.firecrawl.dev）** | **国内直连即可，无需代理**（2026-09-06 实测 200/约 0.9s） |
| web.fetch | 服务端取页，与本机是否开代理无关 |
| **Exa MCP（mcp.exa.ai 经 mcporter）** | **直连即可，无需代理**（2026-09-07 实测） |
| **Jina Reader / RSS / V2EX（境外）** | **走代理**（Jina、V2EX 直连超时；2026-09-07 实测） |

代理检测（端口以本机实测为准）：`for p in 7890 7897 1087; do nc -z -w1 127.0.0.1 $p && echo "在用端口 $p"; done`，再 `curl -x http://127.0.0.1:<探测到的端口> -sI https://www.google.com`。

> **检索语言策略（选源看信息生态、多语召回、先英后中）与海外 AI 搜索 API 扩展位见 `network-and-language.md`。** 各通道逐通道用法与实测边界见 `channels-detail.md`；历次实测台账与待接入清单见 `field-test-notes.md`。
