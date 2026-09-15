# 实测台账与待接入通道（field-test-notes）

> 本文是**运维登记处**，不是选通道指南：选通道看 `channel-selection.md`，逐通道边界看 `channels-detail.md`。每次实测后追加并注明日期；启用新通道前先只读实测一条、成功后再改状态。

## 5. 已知实测事实（每次实测后追加，注明日期）

- 2026-09-06：Firecrawl API 国内直连可达；keyless `v2/scrape` 抓 example.com / 中国土地市场网(landchina.com) / 国家统计局(stats.gov.cn) 均 success、HTTP 200。
- 2026-09-06：keyless 单页 Markdown=1 credit、单页 JSON=5 credits；keyless 调 `v2/map` 被明确拒绝（提示需注册 key）；keyless search 可用但结果条数少。
- 2026-09-06 实跑襄阳/武汉土地成交案例：
  - **云端在境外，部分大陆 gov.cn 抓不到**：迁到 `mnr.gov.cn` 的中国土地市场网（landchina.mnr.gov.cn）Firecrawl 云端两次 DNS 解析失败；同一 URL 改用 web.fetch 立即拿到官方全文。→ 大陆政府站优先 web.fetch 或本机浏览器，Firecrawl 更适合媒体/普通网页与海外站。
  - 襄阳市自规局 shtml 复杂表格页，Firecrawl 转 Markdown 后只剩空表格框架（数据丢失）→ 复杂表格页优先 JSON 模式或 web.fetch。
  - 媒体叙述页（湖北日报）JSON 结构化效果好，能自动单位换算（亿元→万元、公顷→㎡）。
  - 同一页连续提取，LLM 会出现单位错算、字段错位（容积率被填成楼面价）、措辞波动（居住/住宅）、sourceUrl 误取页内导航链接 → AI 提取是初稿，必须过校验门（见 source-schema）。
- 2026-09-07（评估登记，未实装）：开源脚手架 Agent Reach（github.com/MatrixA/Agent-Reach，MIT、自称零 API 费）统一封装网页(Jina)/视频(yt-dlp)/Exa 搜索/社交 UGC 等约 15 通道，是"连接器层"，不做核验/结构化，可被本编排技能当可插拔通道。（后续进展：其中 Jina/Exa 已于当日实测并封装为脚本；社交 UGC 见 §6。）
  - 重叠不重复引入：网页→MD 与 web.fetch/Firecrawl 重叠；视频字幕与自建 `multiplatform-media-fetch` 重叠（后者已做抖音 Cookie、B 站直连、限速防风控）。
  - 真正增量仅三项：Jina 免费兜底、Exa 英文语义/找相似、社交 UGC（小红书/微博/公众号/抖音）舆情读取 + RSS。
  - 风险：Cookie 平台官方提示有封号风险（须用小号）；小红书需 Docker、海外平台服务器需代理；面向可自由 exec 的编码 Agent，豆包内 mcporter/MCP/Docker 链路未实测，**跑通前不得当现成能力**。
  - 行动：不整体安装；出现"批量读 UGC 舆情 / 英文找相似"真实需求时最小化单装对应通道，实测一条后把结果回填本节。
- 2026-09-07 实测（Jina/Exa，本机代理 7890 开启）：
  - Jina Reader：直连 r.jina.ai 30s 超时（HTTP 000），**必须走代理**；走代理抓英文维基"房地产评估"页 HTTP 200、约 1s、107KB/428 行、18 标题、177 链接、**0 残留 HTML 标签**，清洗质量好。调用坑：路径里直接嵌 `https://`（r.jina.ai/https://…）在本环境会被工具层拦截，**目标 URL 须百分号编码**（r.jina.ai/https%3A%2F%2F…）；属境外云端取页，抓国内 gov.cn 的效果未测，不臆断。已封装 `scripts/jina_read.py`（默认走代理+自动编码，底层用系统 curl，规避 urllib 经 ClashX 的 SSL EOF）。
  - Exa：直连 REST api.exa.ai/search 不带 key 返回 **X402 Payment Required**（按次约 $0.007、要 USDC 支付）；但**经 mcporter 接官方 MCP 端点免 key 已跑通**：`npx -y mcporter@latest config add exa https://mcp.exa.ai/mcp --scope home` 后 `npx mcporter call exa.web_search_exa query="自然语言描述理想页面" numResults=3`，直连无需代理，返回标题/URL/发布时间/高亮正文，英文专业主题相关性高；另有 `web_fetch_exa` 可批量读全文；并能经 Exa 间接检索 Reddit 讨论帖正文（直接读评论楼仍需登录态）。注意官方要求 node>=24、本机 v22 有 EBADENGINE 警告但实测可用；配置写在 ~/.mcporter（`mcporter config remove exa` 可逆）。已封装 `scripts/exa_search.py`，直接输出结构化 JSON 并回填溯源字段。
  - 同批零配置通道实测：gh 读公开仓库可用（一手读到 Agent-Reach star=78460、MIT）；RSS 走代理可取（BBC business 51 条；解析库 feedparser 本机未装，需要时 pip install feedparser）；V2EX 公开 API 直连超时、**走代理可用**。
  - 重门槛通道（小红书/Twitter/FB/IG/LinkedIn/直接读 Reddit/公众号/小宇宙）的启用前置与风险统一见 §6 待接入清单：本机当前不具备、需用户介入，不擅自启用；抖音/视频字幕与自建 `multiplatform-media-fetch` 重叠，不重复引入。
- 2026-09（生财有术 scys-mcp，安装/连通 09-09、中大型主题调研 09 月内实测）：连接器地址 `https://mcp.scys.com/shengcai-web/mcp`，OAuth2.1+PKCE 免手填 Token，约 45 工具，只读 `listMenu` 无参即连通。一次主题普查中 contentSearch 翻 12 页（pageSize=50）+searchTopic 兜底，按 entityId 去重得 548、相关性过滤后 174、topicDetail 深读 9 篇精华跑通全管线。实测坑：① contentSearch 多页同拉 / topicDetail 单批发太多会 `[Tool result expired]`，须分批、单批≤2–3、当轮落盘，超大结果会自动持久化为 txt 需脚本解析；② 深读优先 `aiSummaryContent`，其次 `articleContentContainFeishuDoc`，`articleContent` 常只有简介；③ 工具 schema 被压缩时先 tool_search 取真实参数再调；④ 限流约 40 次/分/账号。完整 SOP 见 `scys-mcp-guide.md`。
- 待补充：公共资源交易、挂牌平台等目标站点经各通道的可抓性与字段质量，实测后登记于此。

## 6. 待接入通道清单（需用户介入；每次启用前先只读实测一条，成功后再改状态）

> 这些通道 Agent Reach 支持、但本机当前不具备零配置使用条件。**用户需要时：先说明前置条件与封号风险并取得同意 → 最小化安装/配置 → 只读实测 1 条 → 回填 §5 并把该通道升为"已验证"。未实测前不得当现成能力，也不替用户登录或读取其浏览器 Cookie。**

| 通道 | 对调研的潜在用途 | 启用前置（缺一不可） | 备注 / 风险 |
| --- | --- | --- | --- |
| 小红书 | 楼盘口碑、片区舆情、消费趋势（T4 线索） | 装 Docker 跑 xiaohongshu-mcp；小号 Cookie 或受控 Chrome 会话 | 脚本调用有封号风险，用小号 |
| Twitter/X | 海外舆情、行业人物观点 | 小号 AUTH_TOKEN/CT0（或 xreach）+ 海外代理 | 封号风险，用小号 |
| Reddit 读帖/评论 | 海外用户真实讨论 | 登录态 + 住宅代理 | 数据中心 IP 被 403；**搜索先用已验证的 Exa 加 site:reddit.com 替代** |
| Facebook/Instagram | 海外社媒舆情 | OpenCLI 复用受控 Chrome 登录态 + 代理 | 封号风险，评估基本用不上 |
| LinkedIn | 公司/人物/职位背景 | linkedin MCP + 登录态 | 评估价值低 |
| 雪球 | A股/港股社区情绪 | 登录 Cookie | 金融数据优先用已内置 finance 检索 |
| 微信公众号 | 中文行业文章全文 | camoufox 隐身浏览器 + 搜狗检索 | 非零配置，需另装 |
| 小宇宙播客 | 中文播客转写 | Whisper key | 音视频转写优先用已有 `multiplatform-media-fetch` |
| Boss直聘 | 招聘/用工信息 | mcp-bosszp + 登录态 | 评估基本用不上 |
