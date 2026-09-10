---
name: web-research-toolkit
description: 网络调研与公开网页数据采集的统一编排技能。当需要做资料/信息/数据搜集、市场/政策/行业/竞品调研、网页批量采集或转结构化(JSON/表格)、事实核查与信源溯源、持续监控网页变化、房地产评估数据（土地成交、挂牌价、规划/政策文件）采集时使用。负责按任务特征路由取数通道（内置联网搜索、网页精读 web.fetch、Firecrawl 云端抓取与结构化、垂直领域检索、代理分流），并固化"界定问题→选源→采集→交叉核验→结构化溯源→交付归档"的标准流程。触发词：调研、搜集/汇总资料、查清楚、批量抓取网页、网页转 JSON/表格、提取网页字段、监控网页更新、土地成交/挂牌案例采集、信源核查、证据溯源。
compatibility: "仅在 macOS(Darwin) 实测可用；Windows/Linux 未适配。执行前先判平台(uname -s 返回 Darwin)，非 macOS 停止并告知需另行适配、不硬跑；将来补齐 Windows 后仍按平台分流并分别标注验证状态"
---

# 网络调研工具箱（web-research-toolkit）

## 平台适用（执行前先读）
- 本技能当前**仅在 macOS（Darwin）实测可用**，命令、路径、代理端口与系统原生能力均按 Mac。
- 动手前先判平台：`uname -s` 返回 `Darwin` 才走本技能流程；**Windows/Linux 未适配，遇到就停下告知用户“需先做该平台适配”，不要用想当然的等价命令硬跑**。
- 以后补齐 Windows 后也必须保留“先判平台 → 按平台分流”的结构：mac/Windows 的命令与路径分开写、各自标注是否已验证。

统一编排"从公开网络取数 → 核验 → 结构化 → 溯源交付"。本技能不重复实现搜索引擎，核心价值是**选对通道、走对流程、留好证据**。

## 一、调研标准流程（7 步，按序执行）

1. **界定问题与交付物**：要回答的子问题、输出形态（结论 / 表 / 数据集 / 报告）、范围与时间口径。
2. **拆子问题、列信源清单**：每个子问题指定候选源，优先一手/官方源（信源分级见 `references/source-schema.md`）。
3. **选通道采集**：按第二节路由；先广搜定位，再对目标页精读或抓取。
4. **去重与交叉核验**：关键事实至少 2 个独立来源；冲突保留两说并标注；区分"事实 / 观点 / 一方声称"。
5. **结构化**：固定字段入库，每条记录必带 `sourceUrl + fetchedAt + 信源等级`（模板见 source-schema）。
6. **综合分析**：只基于已核验证据下结论；证据不足标"待核实"，**不编造数字与来源**。
7. **交付与归档**：结论逐条附来源；需要沉淀时归档飞书知识库（按项目 AGENTS 规则询问）。

> 完整 SOP、反幻觉清单、房地产评估专项调研清单见 `references/research-workflow.md`。

## 二、取数通道路由（核心，先选通道再动手）

| 任务特征 | 用什么 | 关键边界 |
| --- | --- | --- |
| 不知道信息在哪、探索性问题、少量事实、要最新动态 | 内置联网搜索（general_search），一次并行 ≤3 个 query | 基于搜索索引，给摘要+链接，可能滞后、不保证穷尽 |
| 垂直领域：学术 / 中国法规规范性文件 / 金融 / 医疗 / 企业内部 | 中国法规优先 **pkulaw-legal-data 技能（可看现行有效/时效）**；其余 scholar/finance/medical/enterprise | 领域问题优先垂直库；政策红头文件权威源见 policy-source-map |
| 已知具体 URL，要全文、读在线 PDF/长文档、**大陆 gov.cn 政府站** | web.fetch（分页读完，服务端取页，**不受本机代理影响**） | 单页/少量页精读；大陆政府站首选它兜底；不做整站递归 |
| 整站批量、JS 动态渲染页、媒体/普通网页要固定字段 JSON、反复更新、变更监控 | **Firecrawl**（脚本 `scripts/fc_scrape.py`，指南见第三节） | 按 credit 计费；keyless 仅单页；**云端在境外，部分大陆 gov.cn 会 DNS 失败，遇此改 web.fetch** |
| 英文/海外资料、语义"找相似"、Reddit 讨论线索 | **Exa 语义搜索**（脚本 `scripts/exa_search.py`，免 key） | 自然语言描述需求；结果默认 T3，回源后定级；直连无需代理 |
| 海外已知页面，web.fetch/Firecrawl 都读不下来 | **Jina Reader**（脚本 `scripts/jina_read.py`） | 走代理、自动 URL 编码；境外云端取页 |
| 国外站点 / Google | 先开代理（ClashX `http://127.0.0.1:7890`） | 国内政府/站点直连；**Firecrawl API、Exa MCP 直连；Jina/RSS/V2EX 走代理** |
| 需要可视化点击、人工登录或验证码 | 浏览器自动化技能（browser-use / computer-use），登录环节交用户接管 | 不在本技能展开；本机登录态内容不走 Firecrawl 云端 |

完整对比、决策树、中英文搜索源路由与各通道实测边界见 `references/channel-selection.md`；**政策/红头文件的权威库与五级分层找法见 `references/policy-source-map.md`**。

## 三、Firecrawl 用法（速查）

- **零 key（不注册，当前默认）**：单页转 Markdown、单页 JSON 结构化、搜索、PDF 解析；按"IP/天"限流；国内直连。
- **注册免费档（1000 credits/月，$0）后解锁**：Map 列整站链接、Crawl 整站爬取、批量 Extract、Monitor 定时监控。
- **成本（官方单价，2026-09 核实）**：Markdown 抓取 1 credit/页；**JSON 结构化 5/页**；搜索 2/10 条；监控 1/页/次；交互浏览器 2/分钟；额度月底清零。
- **单页直接跑（零依赖脚本）**：
  ```bash
  # 转 Markdown，结果打印到屏幕（也可 --out page.md）
  python3 scripts/fc_scrape.py "https://example.com"
  # 按 JSON Schema 结构化（schema 模板见 assets/）
  python3 scripts/fc_scrape.py "https://某公告页" --json \
    --schema-file ../assets/land-deal.schema.json \
    --prompt "提取土地出让成交信息" --out row.json
  # 有注册 key 后：export FIRECRAWL_API_KEY=fc-xxx（自动切换，额度更高）
  ```

> 端点全表、keyless 实测边界、定价档位、SDK/MCP 接入、批量与监控管线、避坑见 `references/firecrawl-guide.md`。

### 其它已验证脚本（海外取数）
```bash
# Exa 英文语义搜索（首次需配置，免 key：npx -y mcporter@latest config add exa https://mcp.exa.ai/mcp --scope home）
python3 scripts/exa_search.py "natural-language description of the ideal page" --num 5 --out exa.json
# Jina 任意网页→Markdown（默认走 7890 代理、自动 URL 编码；web.fetch/Firecrawl 失败时的海外页兜底）
python3 scripts/jina_read.py "https://example.com" --out page.md
```
> 通道决策树、gh/RSS/V2EX 用法、待接入平台（小红书/Twitter/Reddit 读帖/公众号等，启用前先实测）见 `references/channel-selection.md`。

## 四、溯源硬规则（不可违反）

1. 每个事实性结论可追溯到具体 URL；关键事实多源交叉并标注信源等级（官方/权威/专业/自媒体）。
2. 数字、日期、价格必须来自来源或可复现计算，否则标"待核实"；**禁止编造来源、数值、链接**。
3. 每条结构化记录必含 `sourceUrl、sourceName、sourceTier、fetchedAt`；评估数据另需可回源核验。
4. 抓取失败、被反爬、内容为空要**如实报告**，不得用旧快照或臆测填充；区分"已查证 / 一方称 / 未核实"。
5. 只采集公开信息，遵守目标站点条款与个人信息保护法，不采集个人敏感信息。
6. **AI 结构化结果是初稿，不是终稿**：入库前必须过校验门（合理区间、单位按 `*_raw` 复算、相邻字段错位检查、客观字段以程序为准），见 `references/source-schema.md` 2.1。

## 五、能力清单与扩展位（迭代登记处）

**已就位（经 2026-09-06 真实土地成交案例验证）**
- 内置联网搜索 + 垂直检索路由；web.fetch 精读（含大陆 gov.cn 兜底）；Firecrawl 单页（Markdown / JSON，keyless 实测可用）；**Exa 英文语义搜索（exa_search.py 免 key）、Jina 海外网页兜底（jina_read.py）、gh/RSS/V2EX 均已实测**；国内外网络分流。
- 土地成交 schema：单位换算口径固化（亿→万、公顷→㎡）、含 `*_raw` 原值复核字段。
- `fc_scrape.py` 自动回填 sourceUrl/fetchedAt（不采信模型）；AI 提取校验门 + 信源溯源规范。

**扩展位（具备条件后启用，先在对应 reference 登记再使用）**
- [ ] 拿到 Firecrawl API key：Crawl / Map / 批量 Extract / Monitor 变更监控、MCP 接入 Claude Code/Codex
- [ ] 站点适配器：中国土地市场网、公共资源交易中心、挂牌平台（分页/查询参数固化）
- [ ] 定时采集 + 快照 diff（new / changed / gone）入数据集
- [ ] Firecrawl 自托管或其它采集通道（按需评估）
- [ ] 社交 UGC 平台（小红书/Twitter/Reddit 读帖/公众号等）：前置条件与封号风险见 channel-selection §6，需要时先只读实测 1 条、成功后再启用

> 新增任何取数能力，先写进 `references/channel-selection.md` 的通道表，再在流程中使用，保持单一权威清单。
