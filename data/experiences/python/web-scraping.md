---

## 网页抓取与反爬虫绕过

**收录日期**：2026-02-01
**来源日期**：2026-02-01
**标签**：#反爬虫 #Playwright #Selenium #自动化 #Web抓取 #爬虫
**状态**：✅ 已验证
**适用版本**：playwright-stealth 2.0+ / undetected-chromedriver 3.5+

**问题/场景**：

本地脚本/控制台实现自动化搜索或网页抓取时，被反爬虫机制检测并拦截。

**解决方案/结论**：

### 反爬虫绕过工具对比

| 工具 | 特点 | 有效性 |
|---|---|---|
| **undetected-chromedriver** | Selenium 补丁，绕过 Cloudflare/Imperva/DataDome | ⚠️ 普通网站有效，**不隐藏 IP**，数据中心 IP 大概率失败 |
| **playwright-stealth** | Playwright 隐身插件，伪装浏览器指纹 | ⚠️ 仅对简单反爬有效，作者明确声明不保证效果 |
| **住宅代理 (Residential Proxy)** | 从数据中心 IP 切换为住宅 IP | ✅ 解决 IP 信誉问题，但需付费 |
| **官方 Search API** | Serper.dev / SerpAPI / Brave Search API | ✅ **最可靠**，推荐用于搜索引擎 |

### 关键发现

1. **搜索引擎反爬最严格**：Google/Bing/Baidu 有最强的检测机制，stealth 类工具不保证有效
2. **IP 是关键因素**：`undetected-chromedriver` 明确说明数据中心 IP 大概率失败
3. **没有银弹**：所有绕过方案都是"猫鼠游戏"，随时可能失效
4. **Docker 环境更严格**：容器 IP 通常被标记为数据中心，反爬检测更敏感

### 网站分类与对策

| 网站类型 | 反爬强度 | 推荐方案 |
|---|---|---|
| 搜索引擎（Google/Bing/Baidu） | 🔴 极高 | 放弃绕过，使用官方 API |
| CDN 防护站点（Cloudflare/DataDome） | 🟠 高 | undetected-chromedriver + 住宅代理 |
| 普通商业网站 | 🟡 中等 | playwright-stealth + 合理频率 |
| 静态内容站点 | 🟢 低 | requests + 随机 User-Agent |

**关键代码**：

```python
# playwright-stealth 用法
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async with Stealth().use_async(async_playwright()) as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    # navigator.webdriver 将返回 False
    await page.goto('https://example.com')
```

```python
# undetected-chromedriver 用法
import undetected_chromedriver as uc

driver = uc.Chrome(headless=True, use_subprocess=False)
driver.get('https://nowsecure.nl')  # 官方测试站点
driver.save_screenshot('result.png')
```

```python
# 基础反检测配置（requests）
import requests
from fake_useragent import UserAgent

headers = {
    'User-Agent': UserAgent().random,
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}
response = requests.get(url, headers=headers)
```

**最终建议**：

- **搜索引擎**：放弃绕过，直接使用官方 API（Serper.dev、SerpAPI、Brave Search API）
- **普通网站**：`undetected-chromedriver` + 合理请求频率（1-3秒随机延时）
- **高防护站点**：stealth 插件 + 住宅代理 + 随机延时（仍不保证成功）
- **Docker 部署**：优先考虑 API 方案，浏览器自动化在容器内成功率更低

**参考链接**：
- [playwright-stealth PyPI](https://pypi.org/project/playwright-stealth/)
- [undetected-chromedriver PyPI](https://pypi.org/project/undetected-chromedriver/)
- [undetected-chromedriver GitHub](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [fake-useragent PyPI](https://pypi.org/project/fake-useragent/)

**验证记录**：
- [2026-02-01] 调查 PyPI 文档，确认工具定位和局限性
- [2026-02-01] 尝试获取反爬技术博客时遭遇 HTTP 403，证实反爬普遍性
- [2026-02-01] MCP 服务开发中验证：所有主流搜索引擎均检测到自动化

**相关经验**：
- [MCP 协议与 Agent 服务](../ai/mcp.md)
- [Python 自动化](automation.md)

**相关知识**：
- [搜索 API 服务对比](../../knowledge/tools/search-apis.md)
- [自搭建搜索引擎技术](../../knowledge/tools/search-engines.md)

