---

## 网页抓取与反爬虫绕过

**收录日期**：2026-02-01
**来源日期**：2026-02-01
**标签**：#python #experience #playwright #selenium #anti-bot
**状态**：✅ 已验证
**适用版本**：nodriver 0.48+ / playwright-stealth 2.0.1 / undetected-chromedriver 3.5.5

**问题/场景**：

本地脚本/控制台实现自动化搜索或网页抓取时，被反爬虫机制检测并拦截。

**解决方案/结论**：

### 反爬虫绕过工具对比

| 工具 | 特点 | 有效性 |
|---|---|---|
| **nodriver** ⭐ | **undetected-chromedriver 继任者**，纯 CDP 直连，无 Selenium/WebDriver | ✅ 绕过能力最强，完全异步，内置 `cf_verify()` 自动点击 Cloudflare 验证 |
| **undetected-chromedriver** | Selenium 补丁，绕过 Cloudflare/Imperva/DataDome | ⚠️ 普通网站有效，**不隐藏 IP**，数据中心 IP 大概率失败 |
| **playwright-stealth** | Playwright 隐身插件，伪装浏览器指纹 | ⚠️ 仅对简单反爬有效，作者明确声明"proof-of-concept"不保证效果 |
| **住宅代理 (Residential Proxy)** | 从数据中心 IP 切换为住宅 IP | ✅ 解决 IP 信誉问题，但需付费 |
| **官方 Search API** | Serper.dev / SerpAPI / Brave Search API | ✅ **最可靠**，推荐用于搜索引擎 |

### nodriver vs undetected-chromedriver

| 对比项 | undetected-chromedriver | nodriver |
|---|---|---|
| 架构 | Selenium + WebDriver 补丁 | **纯 CDP 直连**，无 Selenium |
| 性能 | 同步为主 | **完全异步** |
| 检测绕过 | 好（移除/伪装 webdriver 痕迹） | **更好**（根本无 webdriver） |
| 状态 | 仍维护（2024.02 最后更新） | **推荐新项目使用** |
| Stars | 12.3k | 3.5k |
| 特色功能 | CDP 事件监听 | `cf_verify()` 自动 Cloudflare 验证、xpath 支持 |

### 关键发现

1. **搜索引擎反爬最严格**：Google/Bing/Baidu 有最强的检测机制，stealth 类工具不保证有效
2. **IP 是关键因素**：`undetected-chromedriver` 明确说明数据中心 IP 大概率失败
3. **没有银弹**：所有绕过方案都是"猫鼠游戏"，随时可能失效
4. **Docker 环境更严格**：容器 IP 通常被标记为数据中心，反爬检测更敏感

### 网站分类与对策

| 网站类型 | 反爬强度 | 推荐方案 |
|---|---|---|
| 搜索引擎（Google/Bing/Baidu） | 🔴 极高 | 放弃绕过，使用官方 API |
| CDN 防护站点（Cloudflare/DataDome） | 🟠 高 | **nodriver** + `cf_verify()` 或住宅代理 |
| 普通商业网站 | 🟡 中等 | nodriver / playwright-stealth + 合理频率 |
| 静态内容站点 | 🟢 低 | requests + 随机 User-Agent |

**关键代码**：

```python
# nodriver 用法（推荐，无 Selenium 依赖）
import nodriver as uc

async def main():
    browser = await uc.start()
    page = await browser.get('https://www.nowsecure.nl')
    
    # 自动点击 Cloudflare 验证（需 opencv-python）
    await page.cf_verify()
    
    await page.save_screenshot()
    content = await page.get_content()

if __name__ == '__main__':
    uc.loop().run_until_complete(main())
```

```python
# playwright-stealth 用法（2.0.1 新 API）
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
- **新项目首选**：`nodriver`（纯 CDP，绕过能力最强，完全异步）
- **已有 Selenium 项目**：继续使用 `undetected-chromedriver`（API 兼容 Selenium）
- **高防护站点**：`nodriver` + `cf_verify()` + 住宅代理（仍不保证成功）
- **Docker 部署**：优先考虑 API 方案，浏览器自动化在容器内成功率更低

**参考链接**：
- [nodriver GitHub](https://github.com/ultrafunkamsterdam/nodriver) ⭐ **推荐**
- [nodriver PyPI](https://pypi.org/project/nodriver/)
- [nodriver 文档](https://ultrafunkamsterdam.github.io/nodriver)
- [playwright-stealth PyPI](https://pypi.org/project/playwright-stealth/)
- [undetected-chromedriver PyPI](https://pypi.org/project/undetected-chromedriver/)
- [undetected-chromedriver GitHub](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
- [fake-useragent PyPI](https://pypi.org/project/fake-useragent/)

### 实践测试结果（2026-02-01）

在 macOS + Chrome 144 环境下对 [nowsecure.nl](https://nowsecure.nl) 进行实际测试：

| 测试项 | 结果 | 备注 |
|-------|------|------|
| nodriver 启动 | ❌ 失败 | macOS 上 CDP HTTPApi 连接失败 (RemoteDisconnected) |
| undetected-chromedriver | ⚠️ 部分成功 | `navigator.webdriver = False` 成功伪装 |
| Cloudflare Turnstile | ❌ 仍触发 | 即使 webdriver=False，仍显示"确认您是真人" |
| pyautogui 真实鼠标点击 | ❌ 仍触发 | 物理层面的鼠标模拟也未能绕过 |

**关键发现**：
- Cloudflare 的检测**不仅是 `navigator.webdriver`**，还包括更深层的浏览器指纹
- GitHub Issues 中有人指出："If Selenium touches the window in any way it gets detected"
- nodriver 的 `mouse_click` 在 2025.09 也被报告为被检测

### 已知 Workarounds（可能已失效）

以下方案在 2023-2024 年曾有效，但 Cloudflare 持续更新，**不保证当前有效**：

**方法 1：打开 DevTools**
```python
# 曾在 2023.07 有效
chrome_options.add_argument("--auto-open-devtools-for-tabs")
```

**方法 2：JS 打开新标签页绕过**
```python
# 曾在 2023.07-08 有效
driver.execute_script('''window.open("http://nowsecure.nl","_blank");''')
time.sleep(5)
driver.switch_to.window(window_name=driver.window_handles[0])
driver.close()
driver.switch_to.window(window_name=driver.window_handles[0])
time.sleep(2)
driver.get("https://google.com")  # 先访问其他站点
time.sleep(2)
driver.get("https://nowsecure.nl")  # 再访问目标
```

**方法 3：nodriver 的 `tab_new()`**
```python
# nodriver 内置方法，原理同方法 2
driver.tab_new("https://google.com")
```

### 付费解决方案：CAPTCHA Solver API

当上述方法失效时，可考虑付费服务：

| 服务 | 价格 | Turnstile 支持 |
|-----|------|----------------|
| [2Captcha](https://2captcha.com) | ~$2.99/1000 | ✅ 支持 |
| [CapSolver](https://capsolver.com) | ~$3/1000 | ✅ 支持 |
| [Anti-Captcha](https://anti-captcha.com) | ~$2/1000 | ✅ 支持 |

**2Captcha Turnstile 调用示例**：
```python
import requests

# 1. 提交验证任务
response = requests.post('https://2captcha.com/in.php', data={
    'key': 'YOUR_API_KEY',
    'method': 'turnstile',
    'sitekey': '0x4AAAAAAAC...',  # 从页面提取
    'pageurl': 'https://example.com/',
    'json': 1
})
task_id = response.json()['request']

# 2. 轮询获取结果
import time
while True:
    time.sleep(5)
    result = requests.get(f'https://2captcha.com/res.php?key=YOUR_API_KEY&action=get&id={task_id}&json=1')
    if result.json()['status'] == 1:
        token = result.json()['request']
        break

# 3. 将 token 注入页面的 cf-turnstile-response 字段
```

**对于 Cloudflare Challenge 页面**，还需额外参数：
- `data`（cData）
- `pagedata`（chlPageData）  
- `action`
- 必须使用返回的 User-Agent

### 未来可尝试的方向

1. **住宅代理 + nodriver**：数据中心 IP 是主要被检测因素
2. **Cookie 复用**：手动通过验证后保存 cookies，后续请求复用
3. **Puppeteer-extra-plugin-stealth**：Node.js 生态中的隐身插件
4. **浏览器配置文件复用**：使用已有用户数据目录 `--user-data-dir`
5. **等待 nodriver 更新**：作者可能会修复 macOS CDP 连接问题

### 测试网站参考

- [nowsecure.nl](https://nowsecure.nl) - nodriver 作者的官方测试站（Cloudflare Turnstile）
- [bot.sannysoft.com](https://bot.sannysoft.com) - 检测 WebDriver 指纹
- [browserleaks.com](https://browserleaks.com) - 浏览器指纹全面检测

**验证记录**：
- [2026-02-01] 调查 PyPI 文档，确认工具定位和局限性
- [2026-02-01] 尝试获取反爬技术博客时遭遇 HTTP 403，证实反爬普遍性
- [2026-02-01] MCP 服务开发中验证：所有主流搜索引擎均检测到自动化
- [2026-02-01] 二次验证：确认 nodriver 为 undetected-chromedriver 官方继任者
- [2026-02-01] **实践测试**：nodriver macOS 连接失败，UC 成功伪装 webdriver 但仍触发 Cloudflare
- [2026-02-01] GitHub Issues 调研：确认这是持续性的"猫鼠游戏"，所有公开方案随时可能失效

**相关经验**：
- [MCP 协议与 Agent 服务](./mcp-protocol-agent-dev.md)

<!-- 
注：以下引用暂时移除，目标文件为占位符，待补充实际内容后恢复：
- Python 自动化 (automation.md)
-->

**相关知识**：
- [搜索 API 服务对比](./search-api-services.md)
- [自搭建搜索引擎技术](./self-hosted-search-engines.md)

