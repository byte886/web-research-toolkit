# 取数通道选型（channel-selection）

> 调研时先读本文件选定通道，再采集。原则：**能用低成本通道解决就不上重通道；要穷尽/结构化/反复更新才上 Firecrawl。**

## 目录
1. 通道总览与定位
2. 决策树（按问题走）
3. 各通道能力与边界
4. 国内外网络分流
5. 已知实测事实（持续更新）
6. 待接入通道清单（需用户介入，启用前先实测）

---

## 1. 通道总览与定位

| 通道 | 本质 | 最擅长 | 产出 | 成本 |
| --- | --- | --- | --- | --- |
| 内置联网搜索 general_search | 关键词→搜索结果摘要+链接 | 探索定位、事实速查、最新动态 | 带链接的文本/摘要 | 已含在会员，边际 0 |
| 垂直检索（scholar/legal/finance/medical/enterprise） | 专业库定向检索 | 学术、中国法规、金融行情、医疗、企业内部资料 | 结构化专业结果 | 已含 |
| web.fetch | 对已知 URL 服务端取全文 | 精读单页、在线 PDF/长文分页读完 | 页面全文/片段 | 0 |
| Firecrawl | 云端真实浏览器渲染+LLM 结构化 | 整站批量、JS 动态页、固定字段 JSON、监控 | Markdown/JSON 数据集 | 免费 1000 credits/月，超出付费 |
| 浏览器自动化（browser/computer-use） | 操作真实浏览器 | 可视化点击、登录后内容、人工接管 | 页面内容/截图 | 0，但占人工 |
| Jina Reader（脚本 jina_read.py，已验证） | r.jina.ai 任意 URL→干净 Markdown（0 残留 HTML、保留标题链接） | web.fetch/Firecrawl 都失败时的第三读网页通道，海外页效果好 | Markdown | 免费无 key；脚本默认走 7890 代理、自动 URL 编码（§3.7） |
| Exa 语义搜索（脚本 exa_search.py，已验证） | 免 key MCP，自然语言语义检索返回干净正文，可间接摸到 Reddit 讨论 | 英文/海外资料找相似、找专业文章、社媒讨论线索 | 结构化 JSON（含溯源） | 免费免 key、直连无需代理（§3.6） |
| 社交 UGC 平台（待接入） | 小红书/微博/公众号/X/FB/IG/LinkedIn/雪球等，经 OpenCLI/各 MCP + 登录态读取 | 平台内舆情口碑（评估中仅作 T4 线索） | 平台文本 | 需 Docker/账号 Cookie/代理、有封号风险，需用户介入（见 §6） |
| 其它已验证公开通道 gh/RSS/V2EX | gh 读公开仓库；RSS/Atom 订阅；V2EX 公开 API | 开源情报、行业更新订阅、技术社区 | 文本/JSON/XML | 免费；RSS/V2EX 境外或需代理（§3.8） |

**关键区别（搜索 vs Firecrawl）**：搜索是"我问你答"，给基于索引的摘要，快但可能滞后、不保证穷尽、字段不统一；Firecrawl 是"采集管线"，对指定 URL/入口实时渲染、逐页产出统一结构，可沉淀成可复用数据集。二者互补：Firecrawl 负责把数据搬下来洗干净，模型负责分析与写作。

## 2. 决策树（自上而下）

1. 需要本机登录态 / 付费墙 / 验证码 / 视频流？
   - 是 → 浏览器自动化技能（登录交用户接管），**不在本技能范围展开**。
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

## 3. 各通道能力与边界

### 3.1 内置联网搜索
- 用法：关键词检索；多个独立方面时一次并行 ≤3 个 query；不重复搜同一信息。
- 适用：不知道源在哪、要概览、要时效信息、找候选 URL。
- 边界：返回的是索引摘要而非保证全文；深层页、需翻页/点击的列表、未收录页拿不到；每次结果排序可能不同，不可作为"穷尽采集"手段。
- 摘要有价值但要全文时，改用 web.fetch 精读对应 URL。

### 3.2 垂直领域检索（优先于通用搜索）
- 学术论文/文献 → scholar_search；个股/财报/行情/宏观 → finance 检索；医药健康 → medical 检索；企业内部文档/记录 → enterprise 检索。
- **中国大陆法律法规 / 部门规章 / 规范性文件 / 司法案例 → 优先 `pkulaw-legal-data` 技能（北大法宝 MCP）**：可按标题/文号/关键词检索法条与案例，支持发文机关、生效日期、**现行有效/废止状态**过滤，用于确认评估依据是否仍有效；运行时该 MCP 不可用则按其说明回退，通用 legal 检索补充。政策/红头文件权威源见 `policy-source-map.md`。
- 领域问题先用垂直库保证权威性，再用通用搜索补外部视角。

### 3.3 web.fetch
- 用法：传 URL；长文档用 pagination 分页（offset/end_offset），直到 end_offset≥total_length；只找片段用 snippet + query。
- 适用：已知 URL 的全文精读、在线 PDF、长报告。
- 边界：单页/少量页；不做整站跟随链接；服务端取页，**与本机代理/登录态无关**。

### 3.4 Firecrawl（详见 firecrawl-guide.md）
- 适用：整站/多页批量、JS 渲染、统一 JSON 字段、定时监控、搜索引擎未收录的深层页。
- 边界：云端不持有本机登录态；强反爬站不保证成功；按 credit 计费；keyless 无整站/批量/监控能力。

### 3.5 浏览器自动化
- 仅当公开通道走不通且确需真实操作（点击路径、登录、人工验证）时使用；敏感步骤（登录/支付/验证码）必须暂停交用户接管。

### 3.6 Exa 语义搜索（脚本 scripts/exa_search.py，已验证）
- 一次性配置（仅首次）：`npx -y mcporter@latest config add exa https://mcp.exa.ai/mcp --scope home`（免 key，配置存 ~/.mcporter，`mcporter config remove exa` 可撤销）。
- 调用：`python3 scripts/exa_search.py "用自然语言描述想要的页面" --num 5 [--out x.json]`；找特定平台讨论在 query 内加 `site:reddit.com`；`--raw` 看原始文本。
- 产出：结构化 JSON，每条含 title/sourceUrl/published/author/highlights + 溯源字段（sourceTier 默认 T3，回源精读后按 source-schema 重新定级）。
- 适用：英文/海外资料、语义"找相似/找同类"、社媒讨论线索；直连无需代理。边界：是语义检索而非穷尽列表；REST 直连要 X402 付费，必须走本脚本的 MCP 通道。

### 3.7 Jina Reader（脚本 scripts/jina_read.py，已验证）
- 调用：`python3 scripts/jina_read.py "https://目标页" [--out page.md]`；脚本默认走 7890 代理并自动做 URL 百分号编码，`--proxy` 换端口、`--no-proxy` 直连。
- 适用：web.fetch/Firecrawl 读不下来的海外页面，要干净 Markdown。边界：境外云端取页，国内 gov.cn 可抓性未验证；底层用系统 curl（Python urllib 经 ClashX 会 SSL EOF）。

### 3.8 其它已验证零配置公开通道
- GitHub：`gh` 已装，读公开仓库/搜索免登录（`gh api repos/OWNER/REPO`、`gh search repos "q"`）；写操作与私有库需 `gh auth login`。
- RSS/Atom：`curl` 取 XML 即可订阅行业更新（境外源走代理）；要解析成结构化再 `pip install feedparser`（本机暂未装）。
- V2EX：`curl "https://www.v2ex.com/api/topics/hot.json"`，**直连超时、须走代理**。

## 4. 国内外网络分流（重要）

| 目标 | 通道 |
| --- | --- |
| Google、YouTube、X 等被墙站点 | 先开代理：ClashX，HTTP 代理 `http://127.0.0.1:7890`（端口以实际为准） |
| 国内政府/公开站点（土地、统计、自规局等） | 直连，走代理反而可能失败 |
| **Firecrawl API（api.firecrawl.dev）** | **国内直连即可，无需代理**（2026-09-06 实测 200/约 0.9s） |
| web.fetch | 服务端取页，与本机是否开代理无关 |
| **Exa MCP（mcp.exa.ai 经 mcporter）** | **直连即可，无需代理**（2026-09-07 实测） |
| **Jina Reader / RSS / V2EX（境外）** | **走代理**（Jina、V2EX 直连超时；2026-09-07 实测） |

代理检测：`lsof -iTCP:7890 -sTCP:LISTEN` 或 `curl -x http://127.0.0.1:7890 -sI https://www.google.com`。

### 4.1 按内容语言/生态选搜索源（与"能不能连上网"是两回事）

- **中文 / 国内内容**（gov.cn、国内政策与市场、中文媒体）：内置联网搜索 + 垂直库 + web.fetch 为主，对国内生态覆盖最好。
- **英文 / 海外内容**（海外公司、国际市场、英文文献与资料）：内置搜索对英文网页覆盖有限；需要时开代理用 Google，或接入下面的海外搜索 API。
- 口诀：先判断"信息长在哪种语言/生态的网上"再选搜索源；代理只解决连通性，不解决索引全不全。

### 4.2 海外 AI 搜索 API（扩展位：当前未接入，需自备 key、多数付费）

按"搜索停在哪一步"分工；价格随官方调整，接入前以官网为准，此处只记定位、不写死价格。

| 工具 | 停在哪步 / 定位 | 典型用途 |
| --- | --- | --- |
| Tavily | 搜索 + 干净正文，最均衡的默认项 | 海外市场/竞品调研、RAG 事实采集 |
| Exa | 语义/神经检索，"给一个找一批相似" | 同类发现、概念/公司发现 |
| Perplexity Sonar | 直接返回带引用的答案（按 token 计费） | 一步到位问答 |
| Brave | 独立索引，不依赖 Google/Bing | 隐私/独立索引备选 |
| Serper/SerpAPI | 只取 Google SERP 原始结果 | SEO/排名追踪，成本最低 |
| Firecrawl | 搜索后整站批量爬取 + 结构化 | 批量内容获取（本技能已接 keyless 单页） |

> 选型：90% 海外检索默认 Tavily；要"找相似"用 Exa；整站批量用 Firecrawl；想直接拿答案用 Sonar；Brave/Serper 为备选。真要接入某个时再单独出接入与成本方案。

## 5. 已知实测事实（每次实测后追加，注明日期）

- 2026-09-06：Firecrawl API 国内直连可达；keyless `v2/scrape` 抓 example.com / 中国土地市场网(landchina.com) / 国家统计局(stats.gov.cn) 均 success、HTTP 200。
- 2026-09-06：keyless 单页 Markdown=1 credit、单页 JSON=5 credits；keyless 调 `v2/map` 被明确拒绝（提示需注册 key）；keyless search 可用但结果条数少。
- 2026-09-06 实跑襄阳/武汉土地成交案例：
  - **云端在境外，部分大陆 gov.cn 抓不到**：迁到 `mnr.gov.cn` 的中国土地市场网（landchina.mnr.gov.cn）Firecrawl 云端两次 DNS 解析失败；同一 URL 改用 web.fetch 立即拿到官方全文。→ 大陆政府站优先 web.fetch 或本机浏览器，Firecrawl 更适合媒体/普通网页与海外站。
  - 襄阳市自规局 shtml 复杂表格页，Firecrawl 转 Markdown 后只剩空表格框架（数据丢失）→ 复杂表格页优先 JSON 模式或 web.fetch。
  - 媒体叙述页（湖北日报）JSON 结构化效果好，能自动单位换算（亿元→万元、公顷→㎡）。
  - 同一页连续提取，LLM 会出现单位错算、字段错位（容积率被填成楼面价）、措辞波动（居住/住宅）、sourceUrl 误取页内导航链接 → AI 提取是初稿，必须过校验门（见 source-schema）。
- 2026-09-07（评估登记，未实装）：开源脚手架 Agent Reach（github.com/MatrixA/Agent-Reach，MIT、自称零 API 费）统一封装网页(Jina)/视频(yt-dlp)/Exa 搜索/社交 UGC 等约 15 通道，是"连接器层"，不做核验/结构化，可被本编排技能当可插拔通道。（后续进展：其中 Jina/Exa 已于当日实测并封装为脚本，见 §3.6/§3.7；社交 UGC 见 §6。）
  - 重叠不重复引入：网页→MD 与 web.fetch/Firecrawl 重叠；视频字幕与自建 multiplatform-media-fetch 重叠（后者已做抖音 Cookie、B 站直连、限速防风控）。
  - 真正增量仅三项：Jina 免费兜底、Exa 英文语义/找相似、社交 UGC（小红书/微博/公众号/抖音）舆情读取 + RSS。
  - 风险：Cookie 平台官方提示有封号风险（须用小号）；小红书需 Docker、海外平台服务器需代理；面向可自由 exec 的编码 Agent，豆包内 mcporter/MCP/Docker 链路未实测，**跑通前不得当现成能力**。
  - 行动：不整体安装；出现"批量读 UGC 舆情 / 英文找相似"真实需求时最小化单装对应通道，实测一条后把结果回填本节。
- 2026-09-07 实测（Jina/Exa，本机代理 7890 开启）：
  - Jina Reader：直连 r.jina.ai 30s 超时（HTTP 000），**必须走代理**；走代理抓英文维基"房地产评估"页 HTTP 200、约 1s、107KB/428 行、18 标题、177 链接、**0 残留 HTML 标签**，清洗质量好。调用坑：路径里直接嵌 `https://`（r.jina.ai/https://…）在本环境会被工具层拦截，**目标 URL 须百分号编码**（r.jina.ai/https%3A%2F%2F…）；属境外云端取页，抓国内 gov.cn 的效果未测，不臆断。已封装 `scripts/jina_read.py`（默认走代理+自动编码，底层用系统 curl，规避 urllib 经 ClashX 的 SSL EOF）。
  - Exa：直连 REST api.exa.ai/search 不带 key 返回 **X402 Payment Required**（按次约 $0.007、要 USDC 支付）；但**经 mcporter 接官方 MCP 端点免 key 已跑通**：`npx -y mcporter@latest config add exa https://mcp.exa.ai/mcp --scope home` 后 `npx mcporter call exa.web_search_exa query="自然语言描述理想页面" numResults=3`，直连无需代理，返回标题/URL/发布时间/高亮正文，英文专业主题相关性高；另有 `web_fetch_exa` 可批量读全文；并能经 Exa 间接检索 Reddit 讨论帖正文（直接读评论楼仍需登录态）。注意官方要求 node>=24、本机 v22 有 EBADENGINE 警告但实测可用；配置写在 ~/.mcporter（`mcporter config remove exa` 可逆）。已封装 `scripts/exa_search.py`，直接输出结构化 JSON 并回填溯源字段。
  - 同批零配置通道实测：gh 读公开仓库可用（一手读到 Agent-Reach star=78460、MIT）；RSS 走代理可取（BBC business 51 条；解析库 feedparser 本机未装，需要时 pip install feedparser）；V2EX 公开 API 直连超时、**走代理可用**。
  - 重门槛通道（小红书/Twitter/FB/IG/LinkedIn/雪球/直接读 Reddit/公众号/小宇宙）的启用前置与风险统一见 §6 待接入清单：本机当前不具备、需用户介入，不擅自启用；抖音/视频字幕与自建 multiplatform-media-fetch 重叠，不重复引入。
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
| 小宇宙播客 | 中文播客转写 | Whisper key | 音视频转写优先用已有 multiplatform-media-fetch |
| Boss直聘 | 招聘/用工信息 | mcp-bosszp + 登录态 | 评估基本用不上 |
