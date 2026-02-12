# Web Archive MCP — 实现蓝图

**标签**：#mcp #python #playwright #architecture #web #tools
**来源**：实践总结 — `d:\AI\MCPs\web_archive_mcp`
**收录日期**：2025-02-12
**更新日期**：2025-02-12
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（自有项目，源码可查）
**适用版本**：Python 3.10+ / MCP SDK 1.22.0 / Playwright latest

### 概要

基于 FastMCP + Playwright (Edge) 的网页归档 MCP 服务，提供 4 个工具：`save_as_markdown`、`archive_web_page`（兼容别名）、`save_as_mhtml`、`save_as_zip`。支持反爬（stealth 模式）、站点弹窗处理、CDP 协议抓取 MHTML，输出 HTML 源码 / Markdown / MHTML / 全页截图 / ZIP 打包。

### 内容

---

## 一、项目结构

```
web_archive_mcp/
├── server.py             # 主服务 — 所有核心逻辑
├── call_tool.py          # CLI 客户端（调试用）
├── requirements.txt      # 依赖清单
├── mcp.json              # MCP 客户端配置（VS Code / Cursor）
├── archives/             # 归档输出目录（自动创建）
│   └── {slug}_{timestamp}/
│       ├── page_source.txt   # HTML 源码（.txt 避免 SafeNet 加密）
│       ├── page.md           # Markdown 转换
│       ├── page.mhtml        # MHTML 快照（含样式 / 图片）
│       └── page.png          # 全页截图
└── .venv/                # Python 虚拟环境
```

---

## 二、依赖清单

| 包名 | 版本 | 用途 |
|------|------|------|
| `mcp` | 1.22.0 | MCP SDK / FastMCP 服务框架 |
| `httpx` | 0.28.1 | HTTP 客户端（预留，当前未实际调用） |
| `beautifulsoup4` | latest | HTML 解析 / 标题提取 |
| `markdownify` | latest | HTML → Markdown |
| `playwright` | latest | 浏览器自动化（Edge） |
| `playwright-stealth` | latest | 反反爬隐身模式 |

> **部署提示**：安装依赖后还需执行 `playwright install msedge` 安装 Edge 浏览器内核。

---

## 三、MCP 服务配置

- **框架**：`FastMCP("web-archive-mcp")`
- **传输方式**：STDIO
- **入口**：`server.py` → `mcp.run(transport="stdio")`

**客户端配置（mcp.json）**：

```json
{
  "servers": {
    "web_archive_mcp": {
      "command": "<venv>/Scripts/python.exe",
      "args": ["server.py"],
      "transport": "stdio",
      "workingDirectory": "<项目路径>"
    }
  }
}
```

---

## 四、暴露的 4 个工具

| 工具名 | 默认 headless | 生成 ZIP | 说明 |
|--------|:------------:|:--------:|------|
| `save_as_markdown` | `True` | ❌ | 主力工具 — 抓取并保存 Markdown + 源码 |
| `archive_web_page` | `True` | ❌ | 兼容旧版别名 → 内部调用 `save_as_markdown` |
| `save_as_mhtml` | `False` | ❌ | 以 MHTML 单文件保存（保留布局） |
| `save_as_zip` | `False` | ✅ | 全部产物打包 ZIP（防加密策略影响） |

**共享参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | str | 必填 | 目标网页地址 |
| `wait_seconds` | int | 10 | 页面加载后额外等待秒数 |
| `headless` | bool | 因工具而异 | 是否无头模式 |

---

## 五、核心架构与数据流

```
用户调用 Tool
      │
      ▼
  _capture_with_edge(url, wait_seconds, headless)
      │
      ├─ 1. Playwright 启动 Edge（channel="msedge"）
      ├─ 2. 创建 context（自定义 User-Agent）
      ├─ 3. 新建 page + 注入 stealth 脚本
      ├─ 4. page.goto(url, wait_until="load", timeout=120s)
      ├─ 5. wait_for_load_state("networkidle")
      ├─ 6. _handle_popups(page, url)  ← 弹窗处理
      ├─ 7. asyncio.sleep(wait_seconds)
      ├─ 8. html = page.content()
      ├─ 9. screenshot = page.screenshot(full_page=True)
      ├─ 10. CDP: Page.captureSnapshot → MHTML
      └─ 11. browser.close()
      │
      ▼
  返回 (html, final_url, screenshot_bytes, mhtml_content)
      │
      ▼
  _persist_archive(html, final_url, screenshot, mhtml, create_zip)
      │
      ├─ 1. _extract_title(html) → 标题提取
      ├─ 2. _slugify(title) → 文件名安全化
      ├─ 3. 创建 archives/{slug}_{timestamp}/ 目录
      ├─ 4. 写入 page_source.txt（原始 HTML）
      ├─ 5. 写入 page.mhtml（如有）
      ├─ 6. markdownify(html) → page.md
      ├─ 7. 写入 page.png（截图）
      ├─ 8. 若 create_zip → ZIP 打包所有文件
      └─ 9. 返回结果字典
```

---

## 六、关键实现细节

### 6.1 反爬策略

```python
from playwright_stealth.stealth import Stealth

await Stealth().apply_stealth_async(page)
```

- 使用 `playwright-stealth` 注入 stealth 脚本，隐藏 WebDriver 特征
- 自定义 User-Agent 模拟真实 Edge 浏览器

### 6.2 弹窗处理机制

采用 **通用策略 + 站点特定策略** 的分层设计：

```python
POPUP_STRATEGIES = {
    "zhihu.com": _close_zhihu_popup,
    "bilibili.com": _close_bilibili_popup,
}

async def _handle_popups(page, url: str):
    # 1. 通用：按 ESC
    await page.keyboard.press("Escape")
    await asyncio.sleep(0.5)
    # 2. 匹配域名 → 执行专用策略
    for domain, handler in POPUP_STRATEGIES.items():
        if domain in url:
            await handler(page)
```

**知乎**：点击 `.Modal-closeButton` 关闭登录弹窗。

**Bilibili**：
- 注入 CSS 强制隐藏 `.bili-mini-mask`、`.login-tip-mask` 等遮罩
- 依次尝试点击 `.bili-mini-close-icon`、`.login-tip-close` 等关闭按钮

> **扩展方式**：在 `POPUP_STRATEGIES` 字典中添加新域名和对应处理函数即可。

### 6.3 MHTML 抓取 — CDP 协议

```python
cdp = await context.new_cdp_session(page)
result = await cdp.send("Page.captureSnapshot", {"format": "mhtml"})
mhtml_content = result.get("data")
```

- 通过 Playwright 的 CDP Session 调用 Chrome DevTools Protocol
- `Page.captureSnapshot` 可将完整页面（含内联资源）保存为 MHTML 单文件
- Windows 下写入时使用 `newline=""` 防止 `\r\n → \r\r\n` 双回车

### 6.4 标题提取优先级

```python
def _extract_title(html: str) -> str:
    # 优先级: <title> > <h1> > <h2> > og:title > meta[name=title] > "Untitled Page"
```

### 6.5 文件名安全化

```python
def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9-_]+", "_", text).strip("_")
    return slug or "page"
```

保留字母、数字、连字符、下划线，其余替换为 `_`。

### 6.6 归档目录命名

```
archives/{slug}_{YYYYMMDD-HHMMSS}/
```

每次归档创建独立目录，以标题 slug + 时间戳命名，避免冲突。

### 6.7 HTML 源码保存为 .txt

```python
raw_html_path = archive_dir / "page_source.txt"
```

> 使用 `.txt` 而非 `.html` — 避免企业环境下 SafeNet 等加密软件对 `.html` 文件自动加密/锁定。

---

## 七、CLI 调试客户端 (call_tool.py)

```bash
python call_tool.py --url "https://example.com" --tool save_as_zip --headless
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--url` | 必填 | 目标 URL |
| `--tool` | `save_as_zip` | 要调用的工具名 |
| `--headless` | `False` | 无头模式 |

实现原理：通过 `mcp.client.stdio.stdio_client` 以 STDIO 方式连接 server.py，然后调用 `session.call_tool()`。

---

## 八、复现步骤

```bash
# 1. 创建项目目录
mkdir web_archive_mcp && cd web_archive_mcp

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. 安装依赖
pip install mcp==1.22.0 httpx==0.28.1 beautifulsoup4 markdownify playwright playwright-stealth

# 4. 安装 Edge 浏览器内核
playwright install msedge

# 5. 创建 server.py（主服务，见第六节完整实现）
# 6. 创建 mcp.json（配置客户端连接）
# 7. 在 IDE 中配置 MCP 服务指向 server.py
```

---

## 九、设计决策与注意事项

| 决策 | 原因 |
|------|------|
| 使用 Edge 而非 Chromium | 企业环境通常已安装 Edge，无需额外下载 |
| HTML 保存为 .txt | 规避 SafeNet 等文件加密策略 |
| MHTML 通过 CDP 抓取 | Playwright 原生不支持 MHTML，需走 DevTools Protocol |
| 默认 headless 因工具而异 | markdown 可无头高效抓取；mhtml/zip 非无头更稳定 |
| ZIP 打包选项 | ZIP 通常不受加密策略影响，便于传输 |
| `_fetch_html` 函数保留但未使用 | 历史遗留，原计划做无浏览器的轻量抓取，后全面转向 Edge |
| `archive_web_page` 兼容别名 | 旧版接口，内部直接调用 `save_as_markdown` |

### 关键代码

完整服务端源码见 `server.py`（约 303 行），核心函数：

| 函数 | 行数 | 职责 |
|------|------|------|
| `_slugify` | L29-31 | 文件名安全化 |
| `_fetch_html` | L34-42 | HTTP 直接获取（未使用） |
| `_extract_title` | L45-54 | HTML 标题提取 |
| `_persist_archive` | L57-115 | 文件持久化 + ZIP |
| `_close_zhihu_popup` | L118-123 | 知乎弹窗处理 |
| `_close_bilibili_popup` | L126-172 | B站弹窗处理 |
| `_handle_popups` | L181-194 | 统一弹窗路由 |
| `_capture_with_edge` | L197-233 | Edge 浏览器抓取核心 |
| `save_as_markdown` | L236-249 | 工具：Markdown 保存 |
| `archive_web_page` | L252-261 | 工具：兼容别名 |
| `save_as_mhtml` | L264-277 | 工具：MHTML 保存 |
| `save_as_zip` | L280-294 | 工具：ZIP 打包 |

### 参考链接

- [MCP Python SDK (FastMCP)](https://github.com/modelcontextprotocol/python-sdk) - MCP 服务框架
- [Playwright Python](https://playwright.dev/python/) - 浏览器自动化
- [playwright-stealth](https://github.com/nicedouble/playwright_stealth) - 反检测隐身模式
- [Chrome DevTools Protocol - Page.captureSnapshot](https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-captureSnapshot) - MHTML 抓取

### 验证记录

- [2025-02-12] 初次记录，从 `d:\AI\MCPs\web_archive_mcp` 源码完整分析归档

---
