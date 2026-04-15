# 双璃通信架构演进（v3.2 轮询 → v4.0 纯 API）

**标签**：#docker #architecture #astrbot #openclaw
**来源**：实践总结
**收录日期**：2026-03-26
**来源日期**：2026-03-22 ~ 2026-03-26
**更新日期**：2026-03-26
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：OpenClaw 2026.3.13+, AstrBot openclaw_bridge v4.0

### 概要
OpenClaw（璃）与 AstrBot（星璃）之间的双璃通信经过三次架构迭代：v3.2 高频轮询 → v3.3 事件驱动 → v4.0 纯 API 直连。最终方案零文件队列、零 cron 轮询、零 watchdog，双向通过 HTTP API 实时投递。

### 内容

#### 架构演进时间线

| 版本 | 日期 | 方案 | 问题 |
|------|------|------|------|
| v3.2 | 2026-03-22 | 双向写 JSON 文件 + cron 轮询 + ACK 文件确认 | token 消耗极高（~100万+/小时） |
| v3.3 | 2026-03-26 | macOS launchd WatchPaths + watchdog mtime + event_queue 注入 | 文件队列仍是中间层，代码复杂 |
| **v4.0** | **2026-03-26** | **双向 HTTP API 直连，零文件** | **无** ✅ |

#### v4.0 最终架构

```
星璃 → 璃：  send_to_openclaw 工具
              → POST OpenClaw /v1/responses API（HTTP 直连，即时投递）
              → 璃实时收到并处理

璃 → 星璃：   li-inbox.py --send "消息"
              → POST AstrBot /api/v1/chat API（SSE 流式响应）
              → 星璃 LLM 实时处理并回复
```

**核心设计原则**：
- **零中间层**：不经过文件系统，不经过 cron 轮询，不经过 watchdog
- **即时投递**：HTTP 请求发出即投递，无需等待扫描周期
- **极简代码**：bridge 插件 ~100 行，li-inbox.py ~60 行
- **无需确认机制**：API 本身返回成功/失败，不依赖 ACK 文件

#### 关键配置

**OpenClaw 侧**：
- 启用 `/v1/responses` endpoint：`gateway.http.endpoints.responses.enabled: true`
- Gateway 端口：`18789`（默认 WebSocket 端口，同时承载 HTTP API）
- 认证：`Authorization: Bearer <gateway.auth.token>`

**AstrBot 侧**：
- Open API 端点：`/api/v1/chat`（POST，返回 SSE 流）
- 认证：`Authorization: Bearer <open_api_token>`
- 通信 session：`username=openclaw-li`，`session_id=li-comm`

**Docker 网络访问**：
- 容器内访问宿主机 OpenClaw：`http://host.docker.internal:18789`
- 宿主机访问容器内 AstrBot：`http://localhost:6185`（端口映射）

#### 星璃侧 bridge 插件（v4.0）

核心变更：
- `send_to_openclaw` 工具：从「写文件 + HTTP 通知 + ACK」简化为「单次 POST /v1/responses」
- 移除 `_watch_loop`、`_fallback_loop`、`_check_inbox`、`_deliver`（event_queue 注入）
- 移除 `check_openclaw_messages` 工具（不再需要检查文件收件箱）
- 保留 `openclaw_test` 命令（改为 API 连通性测试）

#### 璃侧通信脚本（v4.0）

`li-inbox.py` 简化为两个命令：
- `--send "消息"`：POST AstrBot `/api/v1/chat`，读取 SSE 流提取 message_id
- `--test`：发送测试消息验证连通性

注意：AstrBot `/api/v1/chat` 返回 SSE 流而非 JSON，需要逐行解析 `data: {...}` 行。

#### 已清理的旧组件

| 组件 | 说明 |
|------|------|
| launchd plist | macOS WatchPaths 文件事件监听 |
| watcher 脚本 | 事件触发后的 shell 脚本 |
| inbox 扫描 cron | 璃侧定时检查收件箱 |
| 归档文件 | `/shared/li-comm/archive/` 下的旧 JSON |
| ACK 文件 | `/shared/li-comm/ack/` 下的确认记录 |
| 旧 inbox 文件 | `inbox-openclaw.md`、`inbox-astrbot.md` |

### 关键代码

**星璃 send_to_openclaw 核心逻辑**：
```python
async with aiohttp.ClientSession() as session:
    async with session.post(
        "http://host.docker.internal:18789/v1/responses",
        json={"model": "<model>", "input": content},
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer <token>"
        },
        timeout=aiohttp.ClientTimeout(total=15)
    ) as resp:
        if resp.status == 200:
            return "✅ 消息已通过API发送"
```

**璃→星璃 SSE 流解析**：
```python
# AstrBot 返回 SSE 流，提取 message_id 后退出
with urllib.request.urlopen(req, timeout=60) as resp:
    for line in resp:
        line = line.decode("utf-8").strip()
        if line.startswith("data: ") and '"type": "complete"' in line:
            break
```

### 参考链接

- [OpenAI Responses API 规范](https://www.open-responses.com/) - OpenClaw /v1/responses 兼容此规范

### 相关记录

- 无

### 验证记录
- [2026-03-22] 初次记录：v3.2 轮询模式建立
- [2026-03-26] 更新 v3.3：事件驱动优化，launchd WatchPaths + watchdog mtime
- [2026-03-26] 重大更新 v4.0：纯 API 直连，移除全部文件队列机制。双向端到端测试通过（Docker 内 → 宿主机 OpenClaw /v1/responses 返回 200，宿主机 → AstrBot /api/v1/chat SSE 流正常）

---
