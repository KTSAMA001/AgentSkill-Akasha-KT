---

## 自搭建搜索引擎技术

**收录日期**：2026-02-01
**来源日期**：2026-02-01
**标签**：#tools #knowledge #search-engine #meilisearch #searxng
**状态**：✅ 已验证
**适用场景**：私有数据搜索、隐私保护、全文检索、元搜索聚合

**概述**：

当商业搜索 API 不满足需求时（隐私、成本、定制性），可考虑自建搜索解决方案。主要分两类：
1. **全文搜索引擎**：索引自有数据，提供搜索服务
2. **元搜索引擎**：聚合多个搜索源的结果

### 全文搜索引擎对比

| 引擎 | 特点 | 响应速度 | 适用场景 |
|------|------|----------|----------|
| **MeiliSearch** | RESTful API，开箱即用 | <50ms | 中小型项目、快速原型 |
| **Typesense** | 高容错，内置语义搜索 | <50ms | 电商、推荐系统 |
| **Elasticsearch** | 功能最全，生态最大 | 依赖配置 | 大规模、复杂查询 |

#### MeiliSearch ⭐ 推荐入门

**核心特性**：
- 极速响应（<50ms）
- 开箱即用的容错搜索（typo tolerance）
- 支持中文分词
- AI 增强搜索（语义搜索）
- 过滤 + 分面搜索（faceted search）
- 地理位置搜索
- 多租户支持

**部署**：

```bash
# Docker 部署（推荐）
docker run -it --rm \
  -p 7700:7700 \
  -v $(pwd)/meili_data:/meili_data \
  getmeili/meilisearch:latest

# 或使用 Cloud 版本（免费试用）
```

**快速使用**：

```python
import meilisearch

client = meilisearch.Client('http://localhost:7700', 'masterKey')
index = client.index('movies')

# 添加文档
index.add_documents([
    {'id': 1, 'title': 'Carol', 'genres': ['Romance', 'Drama']},
    {'id': 2, 'title': 'Wonder Woman', 'genres': ['Action', 'Adventure']},
])

# 搜索
results = index.search('wonder')
```

**官网**：https://www.meilisearch.com/

#### Typesense ⭐ 电商推荐

**核心特性**：
- 闪电般的搜索速度
- 容错搜索（typo-tolerant）
- 向量搜索 / 语义搜索
- 地理位置搜索
- 推荐引擎
- 个性化搜索
- 同义词管理

**特色功能**：
- **Conversational Search**：自然语言查询
- **Recommendations**：基于用户行为的推荐
- **Personalization**：个性化搜索结果

**官网**：https://typesense.org/

### 元搜索引擎

#### SearXNG ⭐ 隐私优先

**核心特性**：
- 聚合 **246+ 搜索源**
- 完全开源，可自托管
- **零追踪、零用户画像**
- 支持 Tor / I2P
- Docker 一键部署
- GitHub 24.5k Stars

**聚合能力**：
- 通用搜索：Google、Bing、DuckDuckGo、Qwant...
- 图片：Google Images、Flickr、Unsplash...
- 视频：YouTube、Dailymotion、Vimeo...
- 新闻：Google News、Bing News、Yahoo News...
- 学术：Google Scholar、Semantic Scholar、arXiv...
- 代码：GitHub、GitLab、Codeberg...
- 地图：OpenStreetMap、Google Maps...

**部署**：

```bash
# Docker 部署
git clone https://github.com/searxng/searxng-docker.git
cd searxng-docker
docker-compose up -d
```

**配置示例**（settings.yml）：

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

**⚠️ 注意**：
- SearXNG 依赖第三方搜索引擎，同样受反爬影响
- 高频使用会被封 IP，建议配合代理池
- 不适合作为稳定的 API 服务

**官网**：https://docs.searxng.org/

### 数据采集框架

#### Scrapy ⭐ 爬虫首选

**简介**：世界上使用最广泛的开源爬虫框架（GitHub 55.1k Stars）

**核心特性**：
- 异步请求处理
- 自动限速（AutoThrottle）
- 内置防检测（Cookie、User-Agent 伪装）
- CSS/XPath 选择器
- 多格式导出（JSON、CSV、XML）
- 中间件系统可扩展

**快速开始**：

```bash
# 安装
pip install scrapy

# 创建项目
scrapy startproject myproject
cd myproject

# 生成爬虫
scrapy genspider example example.com

# 运行爬虫
scrapy crawl example -o output.json
```

**基础爬虫示例**：

```python
import scrapy

class QuotesSpider(scrapy.Spider):
    name = 'quotes'
    start_urls = ['https://quotes.toscrape.com/']

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('small.author::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(),
            }
        
        # 翻页
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
```

**官网**：https://scrapy.org/

### 架构建议

根据需求选择合适的组合：

| 需求 | 推荐方案 |
|------|----------|
| 私有数据全文搜索 | MeiliSearch / Typesense |
| 电商搜索 + 推荐 | Typesense |
| 隐私保护的通用搜索 | SearXNG（需要代理支持） |
| 大规模数据采集 | Scrapy + 代理池 |
| 稳定的搜索 API | 商业服务（Brave/Serper） |

**完整方案示例**：

```
[数据源] → [Scrapy 采集] → [MeiliSearch 索引] → [API 服务] → [前端/MCP]
```

**参考链接**：
- [MeiliSearch 文档](https://www.meilisearch.com/docs/)
- [Typesense 文档](https://typesense.org/docs/)
- [SearXNG 文档](https://docs.searxng.org/)
- [Scrapy 文档](https://docs.scrapy.org/)

**验证记录**：
- [2026-02-01] 调研官方文档，确认功能和部署方式
- [2026-02-01] SearXNG 在 GitHub 确认 24.5k Stars，活跃维护

**相关知识**：
- [搜索 API 服务对比](./search-api-services.md)
- [网页抓取与反爬虫绕过](./python-web-scraping-antibot.md)

