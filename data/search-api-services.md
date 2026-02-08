# 搜索 API 服务对比

**收录日期**：2026-02-01
**来源日期**：2026-02-01
**标签**：#tools #knowledge #search-api #serp
**状态**：✅ 已验证
**适用场景**：MCP 服务、AI Agent、SEO 分析、数据采集

**概述**：

当自动化抓取搜索引擎受阻时，官方或第三方搜索 API 是最可靠的替代方案。以下是主流服务的对比分析。

### 服务对比表

| 服务 | 免费额度 | 付费起步 | 特点 | 适用场景 |
|------|----------|----------|------|----------|
| **Brave Search API** | 2000次/月 | $5/1000次 | 独立索引30B+页面，隐私友好 | Claude MCP 官方推荐 |
| **Serper.dev** | 2500次（一次性） | $50/50k次 | 最快最便宜，1-2秒响应 | 高频调用、成本敏感 |
| **SerpAPI** | 250次/月 | $25/月(1k次) | 功能最全，CAPTCHA自动处理 | 完整数据需求、企业级 |
| **Google Custom Search** | 100次/天 | $5/1000次 | 官方API，但只搜索指定站点 | 站内搜索 |

### 详细分析

#### 1. Brave Search API ⭐ 推荐入门

**优势**：
- 免费额度最高（2000次/月，无需信用卡）
- 独立建立的30B+页面索引，不依赖Google
- 被 Claude MCP 官方推荐为首选搜索工具
- SOC 2 认证，支持零数据保留选项

**定价**：
- Free: 2000次/月，1次/秒
- Base AI: $5/1000次
- Pro AI: $9/1000次（含AI摘要）

**限制**：
- 免费版 QPS 较低（1次/秒）
- 部分功能仅限付费版

**适用**：个人项目、MCP 服务开发、隐私敏感场景

#### 2. Serper.dev ⭐ 性价比之选

**优势**：
- 业界最快（1-2秒响应）
- 价格最低（低至 $0.30/1k次）
- 无月费，充值模式，额度6个月有效
- 支持10种搜索类型（网页/图片/新闻/视频/购物等）

**定价**：
- 免费: 2500次（一次性试用）
- Starter: $50/50k次 ($1.00/1k)
- Scale: $1250/2.5M次 ($0.50/1k)
- Ultimate: $3750/12.5M次 ($0.30/1k)

**集成**：
- LangChain / CrewAI / Haystack 官方集成
- 简单 REST API

**适用**：高频调用、AI Agent、成本敏感项目

#### 3. SerpAPI ⭐ 功能最全

**优势**：
- 全浏览器渲染，自动解决 CAPTCHA
- 结构化 JSON 数据（含知识图谱、地图、购物等）
- 精准地理位置定位
- 美国法律保护（爬取公开数据受第一修正案保护）

**定价**：
- Free: 250次/月
- Starter: $25/月(1k次)
- Developer: $75/月(5k次)
- Production: $150/月(15k次)

**支持搜索引擎**：
- Google（含 Light/AI Mode/Scholar/Patents/Maps 等20+子产品）
- Bing / DuckDuckGo / Yahoo / Yandex / Baidu
- Amazon / eBay / Walmart / YouTube / Yelp

**适用**：需要完整SERP数据、企业级应用、多引擎支持

### MCP 集成推荐

根据实际调研，MCP 服务开发推荐顺序：

1. **Brave Search API** - 免费额度充足，官方推荐
2. **Serper.dev** - 性价比高，响应快
3. **SerpAPI** - 数据完整，企业级保障

**MCP 配置示例**（Brave Search）：

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 注意事项

1. **官方 vs 第三方**：Google Custom Search API 只能搜索预定义站点，不等于完整 Google 搜索
2. **数据新鲜度**：第三方 API 的索引更新频率可能有延迟
3. **法律合规**：SerpAPI 提供美国法律保护，其他服务需自行评估
4. **额度管理**：充值模式（Serper）vs 订阅模式（SerpAPI），选择适合项目节奏的

**参考链接**：
- [Brave Search API](https://brave.com/search/api/)
- [Serper.dev](https://serper.dev/)
- [SerpAPI](https://serpapi.com/)
- [Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview)

**验证记录**：
- [2026-02-01] 调研官方文档，确认定价和功能
- [2026-02-01] 确认 Brave Search API 为 Claude MCP 官方推荐

**相关知识**：
- [自搭建搜索引擎](./self-hosted-search-engines.md)
- [网页抓取与反爬虫绕过](./python-web-scraping-antibot.md)

