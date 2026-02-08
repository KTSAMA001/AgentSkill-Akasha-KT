# MCP 协议与 Agent 服务开发经验

**标签**：#ai #experience #mcp
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-01
**来源日期**：2026-01-30 ~ 2026-02-01
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：MCP 0.3+ / FastMCP 0.2+ / AstrBot v4.13.2+

**问题/场景**：

AI Agent 生态（如 AstrBot、Claude、Cursor）需要统一的工具协议，支持多种传输模式（stdio、SSE），并能在 Docker 容器内高效部署。

**解决方案/结论**：

- MCP 协议推荐优先使用 stdio 传输，SSE 受限于容器网络（如 DNS rebinding）。
- FastMCP 框架适合快速开发 Python 工具服务，支持 Playwright、BeautifulSoup4 等库。
- 工具命名建议加前缀（如 kt_）避免与内置工具冲突。
- ~~搜索引擎爬取建议多选择器兜底，优先 Bing、DuckDuckGo，最后 Baidu。~~（此方案在 Docker 环境下被证实无效，见下方补充）
- Docker 内部署需提前安装 Playwright 浏览器依赖。

**关键代码**：

```python
# MCP 服务启动示例
from mcp.server.fastmcp import FastMCP
FastMCP.run(tools=[...], transport="stdio")
```

**参考链接**：
- [FastMCP GitHub](https://github.com/fastmcp-me/fastmcp-python) - Python MCP 框架
- [FastMCP 文档](https://fastmcp.wiki/) - 官方文档
- [Playwright Python 文档](https://playwright.dev/python/docs/intro) - 自动化浏览器

**验证记录**：
- [2026-01-30] MCP 服务本地开发，SSE 受限于 Docker 网络
- [2026-02-01] AstrBot 容器内 stdio 部署，工具正常加载
- [2026-02-01] ⚠️ **搜索引擎多选择器兜底方案失效**：所有搜索引擎（百度、Bing、DuckDuckGo、Brave）均检测到自动化并重定向到验证/保护页面。尝试了自定义 User-Agent、playwright-stealth 库、反检测脚本等多种方案均无效。

**补充结论（2026-02-01 更新）**：

搜索引擎在 Docker 环境下的反爬虫限制是系统性的，无法通过技术手段完全绕过。可行的解决方案：

1. **集成官方搜索 API**（推荐）：Serper.dev、SerpAPI、Brave Search API
2. **改造成网页抓取工具**：直接访问特定站点的内部搜索，而非搜索引擎结果页
3. **自建搜索**：Elasticsearch + 自有爬虫

**对比参考**：
- `web_archive_mcp`（本地）能正常工作，因为直接访问具体网页 URL，普通网站反爬虫机制相对宽松

**相关经验**：
- [网页抓取与反爬虫绕过](./python-web-scraping-antibot.md) - 详细的反爬虫工具对比与绕过方案
