# 结构化与信源溯源规范（source-schema）

> 所有调研产出必须可追溯。本文件定义信源分级、通用溯源字段、证据标注方式与房地产场景的 JSON Schema 模板。

## 目录
1. 信源分级（sourceTier）
2. 通用溯源字段（每条记录必备）
3. 证据标注与结论用语
4. 房地产 JSON Schema 模板
5. 数据集文件组织

---

## 1. 信源分级（sourceTier）

| 等级 | 定义 | 例子 | 可支撑强度 |
| --- | --- | --- | --- |
| T1 官方一手 | 主管部门、交易平台、统计机关、法律法规原文、官方公报 | 土地市场网、统计局、政府公报、人大/政府发布 | 可直接作为依据 |
| T2 权威机构 | 事业单位、行业协会、权威研究/学术、上市公司公告 | 行业协会年报、学术论文、券商/评估机构报告 | 可支撑，注明出处 |
| T3 专业二手 | 专业媒体、百科汇编、咨询机构整理 | 专业财经媒体、行业数据库二手汇编 | 需回溯一手或交叉 |
| T4 自媒体/一方称 | 自媒体、厂商/中介营销、匿名帖 | 公众号软文、楼盘宣传、博主说法 | 仅作线索，须独立佐证 |

原则：关键结论优先 T1；只用 T4 时必须标"未经独立核实"。

> 政策/法规类 T1 的具体权威库（国家法律法规数据库、国务院政策文件库、各级政府政策文件库、北大法宝等）与五级分层找法见 `policy-source-map.md`。

## 2. 通用溯源字段（每条记录必备）

| 字段 | 含义 |
| --- | --- |
| `sourceUrl` | 具体页面 URL（能回到原文，不是站点首页） |
| `sourceName` | 来源名称（机构/站点/文件标题） |
| `sourceTier` | T1–T4 |
| `fetchedAt` | 抓取/访问时间，ISO 或 YYYY-MM-DD HH:mm |
| `accessStatus` | ok / paywall / empty / blocked / snapshot（说明获取状态） |

建议另含：`collectedBy`（search/fetch/firecrawl/browser）、`note`（口径/存疑点）。

### 2.1 AI 提取结果校验门（入库前必过）

AI/LLM 从网页提取的结构化结果一律视为**初稿**，正式入库前逐项校验：

1. 必填字段非空、类型正确；缺失留 null，不接受臆造值。
2. 数值在合理区间（如容积率 0.3–8、楼面价为上千正数、面积/价格为正），异常即回原文核对。
3. 单位换算用 `*_raw` 原始表述复算（如 3.806 亿 → 38060 万、6.874629 公顷 → 68746.29 ㎡）。
4. 客观字段以程序为准：sourceUrl 用请求 URL、fetchedAt 用抓取当天（fc_scrape.py 已自动回填）。
5. 相邻同类型字段检查错位（如 far 与 floor_price 不可相等）。
6. 不通过则回退原文（web.fetch/人工）或换通道，不把可疑值写入正式案例库。

## 3. 证据标注与结论用语

- **已查证**：≥2 独立来源（关键项至少 1 个 T1）一致 → 可直接陈述。
- **一方称**：仅利益相关/单一来源 → 用"据 XX 称/XX 数据显示"，不写成客观事实。
- **待核实**：缺源或来源冲突未定 → 显式标注并列出需要补的证据。
- 禁止把估算当实测：估算写"约/估算（口径：…）"。
- 时间敏感结论标注"截至 YYYY-MM-DD"。

## 4. 房地产 JSON Schema 模板

> 可直接作为 Firecrawl `--schema-file`。字段按实际页面增删，但**溯源字段与必填项保留**。文件版见 `assets/land-deal.schema.json`。

### 4.1 土地成交（比较法/假设开发法）
```json
{
  "type": "object",
  "properties": {
    "plot_id": {"type": "string", "description": "地块编号"},
    "location": {"type": "string", "description": "地块位置/板块"},
    "land_use": {"type": "string", "description": "土地用途"},
    "area_sqm": {"type": "number", "description": "出让面积(平方米)"},
    "far": {"type": "number", "description": "容积率"},
    "deal_price_wan": {"type": "number", "description": "成交价(万元)"},
    "floor_price": {"type": "number", "description": "楼面价(元/平方米),没有则留空勿臆造"},
    "winner": {"type": "string", "description": "竞得人"},
    "deal_date": {"type": "string", "description": "成交日期 YYYY-MM-DD"},
    "sourceUrl": {"type": "string"},
    "fetchedAt": {"type": "string"}
  },
  "required": ["plot_id", "deal_price_wan", "sourceUrl"]
}
```
楼面价等派生值优先让模型留空、由本地用计算工具按统一口径现算，原值（成交价、面积、容积率）必须保留。

### 4.2 房产挂牌/成交（比较法，扩展用）
关键字段：`estate_name`(小区)、`location`、`house_type`、`area_sqm`、`floor`、`orientation`、`decoration`、`list_or_deal`(挂牌/成交)、`total_price_wan`、`unit_price`、`price_date`、`listing_status`(在售/已成交/下架→对应 diff 的 new/changed/gone)、`sourceUrl`、`fetchedAt`。

### 4.3 政策文件（依据留痕）
`doc_title`、`doc_no`(文号)、`legal_level`(效力层级：法律/行政法规/部门规章/地方性法规/地方规范性文件/党委文件)、`issuer`(发文机关)、`issue_date`、`effective_date`、`status`(现行有效/已废止/被修订，并记核对日期)、`key_clause`(相关条款原文摘录)、`sourceUrl`、`fetchedAt`、`accessStatus`。权威源与分层找法见 `policy-source-map.md`。

## 5. 数据集文件组织

- 一次采集一个目录：`主题_YYYYMMDD/`，内含 `raw/`（原始 Markdown/HTML，备查）、`data.csv|jsonl`（结构化结果，含溯源列）、`sources.md`（来源清单与等级）、`notes.md`（口径、缺口、踩坑）。
- JSONL 每行一条记录，便于追加与 diff；CSV 用 UTF-8。
- 跨轮更新按稳定 ID（地块编号/房源 ID/文号）对齐，标 new/changed/gone，保留历史快照不覆盖。
