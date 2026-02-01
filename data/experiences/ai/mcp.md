---

## MCP 协议与 Agent 服务开发经验

**收录日期**：2026-02-01
**来源日期**：2026-01-30 ~ 2026-02-01
**标签**：#MCP #Agent #AI #协议 #服务集成
**状态**：✅ 已验证
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
- [MCP 官方文档](https://github.com/fastmcp/fastmcp)
- [Playwright 官方文档](https://playwright.dev/python/)

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

---

## 反爬虫绕过技术调查

**收录日期**：2026-02-01
**来源日期**：2026-02-01
**标签**：#反爬虫 #Playwright #Selenium #自动化 #Web抓取
**状态**：✅ 已验证
**适用版本**：playwright-stealth 2.0+ / undetected-chromedriver 3.5+

**问题/场景**：

本地脚本/控制台实现自动化搜索或网页抓取时，被反爬虫机制检测并拦截。

**解决方案/结论**：

| 工具 | 特点 | 有效性 |
|---|---|---|
| **undetected-chromedriver** | Selenium 补丁，绕过 Cloudflare/Imperva/DataDome | ⚠️ 普通网站有效，**不隐藏 IP**，数据中心 IP 大概率失败 |
| **playwright-stealth** | Playwright 隐身插件，伪装浏览器指纹 | ⚠️ 仅对简单反爬有效，作者明确声明不保证效果 |
| **住宅代理** | 从数据中心 IP 切换为住宅 IP | ✅ 解决 IP 信誉问题，但需付费 |
| **官方 Search API** | Serper.dev / SerpAPI / Brave Search API | ✅ **最可靠**，推荐用于搜索引擎 |

**关键发现**：

1. **搜索引擎反爬最严格**：Google/Bing/Baidu 有最强的检测机制，stealth 类工具不保证有效
2. **IP 是关键因素**：`undetected-chromedriver` 明确说明数据中心 IP 大概率失败
3. **没有银弹**：所有绕过方案都是"猫鼠游戏"，随时可能失效

**关键代码**：

```python
# playwright-stealth 用法
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async with Stealth().use_async(async_playwright()) as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    # navigator.webdriver 将返回 False
```

```python
# undetected-chromedriver 用法
import undetected_chromedriver as uc

driver = uc.Chrome(headless=True, use_subprocess=False)
driver.get('https://nowsecure.nl')  # 测试站点
```

**最终建议**：

- **搜索引擎**：放弃绕过，直接使用官方 API
- **普通网站**：`undetected-chromedriver` + 合理请求频率
- **高防护站点**：stealth 插件 + 住宅代理 + 随机延时（仍不保证成功）

**参考链接**：
- [playwright-stealth PyPI](https://pypi.org/project/playwright-stealth/)
- [undetected-chromedriver PyPI](https://pypi.org/project/undetected-chromedriver/)
- [undetected-chromedriver GitHub](https://github.com/ultrafunkamsterdam/undetected-chromedriver)

**验证记录**：
- [2026-02-01] 调查 PyPI 文档，确认工具定位和局限性
- [2026-02-01] 尝试获取反爬技术博客时遭遇 HTTP 403，证实反爬普遍性

**相关经验**：
- [MCP 协议与搜索引擎限制](#mcp-协议与-agent-服务开发经验)
- [Docker 容器部署经验](../tools/misc.md)
- [Python 自动化爬虫](../python/automation.md)
