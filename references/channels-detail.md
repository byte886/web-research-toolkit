# 各通道能力与边界（channels-detail）

> 本文逐通道展开用法与实测边界；选哪个通道见 `channel-selection.md` 的总览表与决策树；网络分流与检索语言策略见 `network-and-language.md`；实测台账见 `field-test-notes.md`。

## 3.1 内置联网搜索
- 用法：关键词检索；多个独立方面时一次并行 ≤3 个 query；不重复搜同一信息。
- 适用：不知道源在哪、要概览、要时效信息、找候选 URL。
- 边界：返回的是索引摘要而非保证全文；深层页、需翻页/点击的列表、未收录页拿不到；每次结果排序可能不同，不可作为"穷尽采集"手段。
- 摘要有价值但要全文时，改用 web.fetch 精读对应 URL。

## 3.2 垂直领域检索（优先于通用搜索）
- 学术论文/文献 → scholar_search；个股/财报/行情/宏观 → finance 检索；医药健康 → medical 检索；企业内部文档/记录 → enterprise 检索。
- **中国大陆法律法规 / 部门规章 / 规范性文件 / 司法案例 → 优先 `pkulaw-legal-data` 技能（北大法宝 MCP）**：可按标题/文号/关键词检索法条与案例，支持发文机关、生效日期、**现行有效/废止状态**过滤，用于确认评估依据是否仍有效；运行时该 MCP 不可用则按其说明回退，通用 legal 检索补充。政策/红头文件权威源见 `policy-source-map.md`。
- 领域问题先用垂直库保证权威性，再用通用搜索补外部视角。

## 3.3 web.fetch
- 用法：传 URL；长文档用 pagination 分页（offset/end_offset），直到 end_offset≥total_length；只找片段用 snippet + query。
- 适用：已知 URL 的全文精读、在线 PDF、长报告。
- 边界：单页/少量页；不做整站跟随链接；服务端取页，**与本机代理/登录态无关**。

## 3.4 Firecrawl（详见 firecrawl-guide.md）
- 适用：整站/多页批量、JS 渲染、统一 JSON 字段、定时监控、搜索引擎未收录的深层页。
- 边界：云端不持有本机登录态；强反爬站不保证成功；按 credit 计费；keyless 无整站/批量/监控能力。

## 3.5 浏览器自动化
- 仅当公开通道走不通且确需真实操作（点击路径、登录、人工验证）时使用；敏感步骤（登录/支付/验证码）必须暂停交用户接管。

## 3.6 Exa 语义搜索（脚本 scripts/exa_search.py，已验证）
- 一次性配置（仅首次）：`npx -y mcporter@latest config add exa https://mcp.exa.ai/mcp --scope home`（免 key，配置存 ~/.mcporter，`mcporter config remove exa` 可撤销）。
- 调用：`python3 scripts/exa_search.py "用自然语言描述想要的页面" --num 5 [--out x.json]`；找特定平台讨论在 query 内加 `site:reddit.com`；`--raw` 看原始文本。
- 产出：结构化 JSON，每条含 title/sourceUrl/published/author/highlights + 溯源字段（sourceTier 默认 T3，回源精读后按 source-schema 重新定级）。
- 适用：英文/海外资料、语义"找相似/找同类"、社媒讨论线索；直连无需代理。边界：是语义检索而非穷尽列表；REST 直连要 X402 付费，必须走本脚本的 MCP 通道。

## 3.7 Jina Reader（脚本 scripts/jina_read.py，已验证）
- 调用：`python3 scripts/jina_read.py "https://目标页" [--out page.md]`；脚本默认自动探测本机代理端口（7890/7897/…）并自动做 URL 百分号编码，`--proxy` 换端口、`--no-proxy` 直连。
- 适用：web.fetch/Firecrawl 读不下来的海外页面，要干净 Markdown。边界：境外云端取页，国内 gov.cn 可抓性未验证；底层用系统 curl（Python urllib 经 ClashX 会 SSL EOF）。

## 3.8 其它已验证零配置公开通道
- GitHub：`gh` 已装，读公开仓库/搜索免登录（`gh api repos/OWNER/REPO`、`gh search repos "q"`）；写操作与私有库需 `gh auth login`。
- RSS/Atom：`curl` 取 XML 即可订阅行业更新（境外源走代理）；要解析成结构化再 `pip install feedparser`（本机暂未装）。
- V2EX：`curl "https://www.v2ex.com/api/topics/hot.json"`，**直连超时、须走代理**。

## 3.9 付费社群：生财有术 scys-mcp（已验证，详见 scys-mcp-guide.md）
- 本质：官方 MCP 连接器（非爬虫），OAuth 授权后以本人身份读会员可见的站内私有内容；约 45 个工具分 8 能力域（内容搜读/航海/项目库/找人/线下局/个人数据/写操作/AI 亦仁）。
- 安装：豆包桌面端新建自定义连接器，地址 `https://mcp.scys.com/shengcai-web/mcp`，HTTP（Streamable HTTP），OAuth2.1+PKCE 浏览器授权、无需手填 Token，对话内勾选启用；连通自检＝只读调 `listMenu`（无参）。
- 调研主力：`contentSearch`（pageSize≤50、pageIndex 从 1 起逐页）广搜 → 按 `entityId` 去重 → 相关性过滤 → `topicDetail` 深读（单批≤2–3、优先 `aiSummaryContent`），结论附 `scys.com/articleDetail/xq_topic/<id>` 链接。
- 与其它通道分工：它解决"公开网根本没有的圈内私有数据"，**不替代**通用搜索；AI 亦仁（startAiYiRenChat/queryAiYiRenChat）只做主观决策判断、须显式点名。
- 边界：需有效会员、只看得到权限内内容、数据有约 1 天同步延迟、限流约 40 次/分；默认只读，写操作（点赞/收藏/投锚/关注）需用户明确授权；官方接口不封号，禁止改用浏览器插件/模拟点击爬取。
