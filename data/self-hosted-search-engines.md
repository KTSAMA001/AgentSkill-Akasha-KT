# 自搭建搜索引擎技术选型

**标签**：#tools #knowledge #search-engine #meilisearch #searxng
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-01
**来源日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：MeiliSearch / Typesense / SearXNG（2026-02-01 记录时点）

### 概要

当商业搜索 API 不满足隐私、成本或定制性需求时，可考虑自建搜索解决方案。搜索引擎主题主要分为索引自有数据的全文搜索引擎，以及聚合多个搜索源的元搜索引擎。

### 内容

自搭建搜索引擎主要分两类：

1. **全文搜索引擎**：索引自有数据，提供搜索服务。
2. **元搜索引擎**：聚合多个搜索源的结果。

### 全文搜索引擎对比

| 引擎 | 特点 | 响应速度 | 适用场景 |
|------|------|----------|----------|
| **MeiliSearch** | RESTful API，开箱即用 | <50ms | 中小型项目、快速原型 |
| **Typesense** | 高容错，内置语义搜索 | <50ms | 电商、推荐系统 |
| **Elasticsearch** | 功能最全，生态最大 | 依赖配置 | 大规模、复杂查询 |

#### MeiliSearch 推荐入门

核心特性：

- 极速响应（<50ms）。
- 开箱即用的容错搜索（typo tolerance）。
- 支持中文分词。
- AI 增强搜索（语义搜索）。
- 过滤 + 分面搜索（faceted search）。
- 地理位置搜索。
- 多租户支持。

部署示例：

```bash
docker run -it --rm \
  -p 7700:7700 \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest
```

快速使用：

```python
import meilisearch

client = meilisearch.Client("http://localhost:7700", "masterKey")
index = client.index("movies")

index.add_documents([
    {"id": 1, "title": "Carol", "genres": ["Romance", "Drama"]},
    {"id": 2, "title": "Wonder Woman", "genres": ["Action", "Adventure"]},
])

results = index.search("wonder")
```

#### Typesense 电商推荐

核心特性：

- 闪电般的搜索速度。
- 容错搜索（typo-tolerant）。
- 向量搜索 / 语义搜索。
- 地理位置搜索。
- 推荐引擎。
- 个性化搜索。
- 同义词管理。

特色功能：

- **Conversational Search**：自然语言查询。
- **Recommendations**：基于用户行为的推荐。
- **Personalization**：个性化搜索结果。

### 元搜索引擎

#### SearXNG 隐私优先

核心特性：

- 聚合多个搜索源。
- 完全开源，可自托管。
- 零追踪、零用户画像。
- 支持 Tor / I2P。
- Docker 一键部署。

聚合能力：

- 通用搜索：Google、Bing、DuckDuckGo、Qwant 等。
- 图片：Google Images、Flickr、Unsplash 等。
- 视频：YouTube、Dailymotion、Vimeo 等。
- 新闻：Google News、Bing News、Yahoo News 等。
- 学术：Google Scholar、Semantic Scholar、arXiv 等。
- 代码：GitHub、GitLab、Codeberg 等。
- 地图：OpenStreetMap、Google Maps 等。

部署示例：

```bash
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker
docker-compose up -d
```

配置示例（`settings.yml`）：

```yaml
use_default_settings: true
server:
  secret_key: "your-secret-key"
  bind_address: "0.0.0.0"
search:
  safe_search: 0
  autocomplete: "google"
  default_lang: "zh-CN"
```

注意：

- SearXNG 依赖第三方搜索引擎，同样受反爬影响。
- 高频使用会被封 IP，建议配合代理池。
- 不适合作为稳定的 API 服务。

### 架构建议

根据需求选择合适的组合：

| 需求 | 推荐方案 |
|------|----------|
| 私有数据全文搜索 | MeiliSearch / Typesense |
| 电商搜索 + 推荐 | Typesense |
| 隐私保护的通用搜索 | SearXNG（需要代理支持） |
| 稳定的搜索 API | 商业服务（Brave/Serper） |

搜索系统可以与独立的数据采集层组合，但采集框架本身不属于搜索引擎主题。

```text
[数据源或采集层] -> [MeiliSearch / Typesense 索引] -> [API 服务] -> [前端/MCP]
```

### 参考链接

- [MeiliSearch 文档](https://www.meilisearch.com/docs/) - MeiliSearch 官方文档。
- [Typesense 文档](https://typesense.org/docs/) - Typesense 官方文档。
- [SearXNG 文档](https://docs.searxng.org/) - SearXNG 官方文档。

### 相关记录

- [搜索 API 服务对比](./search-api-services.md) - 商业搜索 API 的替代方案。
- [Scrapy 数据采集框架](./scrapy-data-collection-framework.md) - 可作为搜索系统上游的数据采集层。

### 验证记录

- [2026-02-01] 调研官方文档，确认功能和部署方式。
- [2026-02-01] SearXNG 在 GitHub 确认 24.5k Stars，活跃维护。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。
---
