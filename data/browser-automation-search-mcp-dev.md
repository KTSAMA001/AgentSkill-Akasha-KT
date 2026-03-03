# 浏览器自动化搜索 MCP 开发记录

**标签**：#python #playwright #mcp #experience #web #tools
**来源**：实践总结
**收录日期**：2026-03-04
**来源日期**：2026-03-04
**状态**：⚠️ 待验证（MCP部分未完成）
**可信度**：⭐⭐⭐（个人实践验证）
**适用版本**：Python 3.12+ / Playwright 1.58+

### 概要

开发浏览器自动化搜索工具，目标是替代智谱MCP的搜索功能。实现了基于 Playwright 的搜索功能，可打开浏览器、执行搜索并获取结果。MCP封装部分因Python版本问题暂停。

### 内容

#### 项目结构

```
/Users/ktsama/KT_Labs/MCP/BrowserAutomation/
├── venv/                    # 虚拟环境（Python 3.12）
├── browser_search.py        # Playwright版本主程序
├── real_browser_search.py   # 真实浏览器操作版本
├── quick_test.py            # 快速测试脚本
├── requirements.txt         # 依赖
└── README.md                # 说明文档
```

#### 关键经验

1. **虚拟环境必须**：任何Python项目必须先创建虚拟环境隔离
   ```bash
   /opt/homebrew/bin/python3.12 -m venv venv
   source venv/bin/activate
   ```

2. **pip镜像加速**：使用清华镜像
   ```bash
   pip install xxx -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. **Shadowrocket代理配置**：
   - 端口：1082
   - 协议：SOCKS5（不是HTTP）
   ```python
   proxy={'server': 'socks5://127.0.0.1:1082'}
   ```

4. **搜索引擎选择**：
   - Google：被代理IP异常流量检测拦截，需要验证
   - Bing：可正常使用，推荐
   - 百度：可正常使用

5. **MCP依赖要求**：
   - Python 3.10+（3.9不支持）
   - 安装命令：`pip install mcp fastmcp`

6. **真实浏览器操作**：
   - 打开浏览器：`subprocess.run(['open', '-a', 'Google Chrome', url])`
   - 模拟键盘：pyautogui + pyperclip
   - URL直接搜索比操作页面元素更可靠

#### Bing搜索实现（已验证可用）

```python
import asyncio
from playwright.async_api import async_playwright

async def search_bing(query: str, max_results: int = 8):
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        proxy={'server': 'socks5://127.0.0.1:1082'}
    )
    page = await browser.new_page()

    url = f'https://www.bing.com/search?q={query}'
    await page.goto(url, timeout=60000)
    await asyncio.sleep(3)

    results = await page.query_selector_all('#b_results .b_algo')

    for element in results[:max_results]:
        title_elem = await element.query_selector('h2 a')
        title = await title_elem.inner_text() if title_elem else ''
        link = await title_elem.get_attribute('href') if title_elem else ''
        # ... 获取描述等

    await browser.close()
    await playwright.stop()
```

### 待完成

- [ ] MCP服务封装（需要Python 3.12环境重新安装依赖）
- [ ] 添加更多搜索引擎支持
- [ ] 结果缓存机制
- [ ] 错误重试机制

### 参考链接

- [Python构建MCP服务器 - 阿里云](https://developer.aliyun.com/article/1678471)
- [Playwright官方文档](https://playwright.dev/python/)

### 相关记录

- [python-web-scraping-antibot.md](./python-web-scraping-antibot.md) - 网页抓取与反爬虫绕过
- [mcp-protocol-agent-dev.md](./mcp-protocol-agent-dev.md) - MCP协议与Agent服务开发经验
- [web-archive-mcp-blueprint.md](./web-archive-mcp-blueprint.md) - Web Archive MCP实现蓝图

### 验证记录

- [2026-03-04] 初次记录，Bing搜索功能已验证可用，MCP封装待完成
