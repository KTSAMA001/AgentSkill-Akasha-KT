# Scrapy 数据采集框架

**标签**：#python #tools #knowledge #anti-bot
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-01
**来源日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：Scrapy（2026-02-01 记录时点）

### 概要

Scrapy 是 Python 生态中常用的开源数据采集框架，适合构建结构化网页抓取流程；它可以作为搜索系统的上游采集层，但本身不是搜索引擎。

### 内容

Scrapy 的核心定位是数据采集框架。它负责请求、解析、翻页、导出和中间件扩展，常用于把网页内容整理成 JSON、CSV、XML 等结构化数据。

核心特性：

- 异步请求处理。
- 自动限速（AutoThrottle）。
- 支持 Cookie、User-Agent 等请求层配置。
- CSS/XPath 选择器。
- 多格式导出（JSON、CSV、XML）。
- 中间件系统可扩展。

快速开始：

```bash
pip install scrapy

scrapy startproject myproject
cd myproject

scrapy genspider example example.com
scrapy crawl example -o output.json
```

基础爬虫示例：

```python
import scrapy


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = ["https://quotes.toscrape.com/"]

    def parse(self, response):
        for quote in response.css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
                "tags": quote.css("div.tags a.tag::text").getall(),
            }

        next_page = response.css("li.next a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)
```

#### 与搜索引擎的关系

Scrapy 适合放在搜索系统上游，负责从数据源采集内容；MeiliSearch、Typesense、Elasticsearch 等搜索引擎负责索引和检索。

```text
[数据源] -> [Scrapy 采集] -> [搜索引擎索引] -> [API 服务] -> [前端/MCP]
```

### 参考链接

- [Scrapy 官网](https://scrapy.org/) - Scrapy 项目主页。
- [Scrapy 文档](https://docs.scrapy.org/) - Scrapy 官方文档。

### 相关记录

- [自搭建搜索引擎技术选型](./self-hosted-search-engines.md) - 搜索引擎选型与架构建议。
- [网页抓取与反爬虫绕过](./python-web-scraping-antibot.md) - 网页抓取和反爬相关经验。

### 验证记录

- [2026-02-01] 调研官方文档，确认功能和部署方式。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。
---
