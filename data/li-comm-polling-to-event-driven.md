# 双璃通信从轮询到事件驱动优化

**标签**：#openclaw #macos #docker #experience #architecture
**来源**：实践总结
**收录日期**：2026-03-26
**来源日期**：2026-03-26
**状态**：✅已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：OpenClaw 2026.3.13, AstrBot openclaw_bridge v3.3

### 概要

将 OpenClaw 与 AstrBot（星璃）之间的双璃通信从高频轮询模式改为 macOS launchd WatchPaths + 文件 mtime watchdog 的事件驱动模式，token 消耗降低约 96%，响应延迟从最长 30 分钟降至约 1 秒。

### 内容

#### 问题背景

双璃通信 v3.2 使用轮询模式：
- **璃侧**：cron 每 2 分钟扫描 inbox（后改为 30 分钟），每次触发完整会话消耗 ~30k tokens
- **星璃侧**：bridge 插件每 3 秒完整扫描收件箱目录（空 30 次后降频到 30s）
- **HTTP 通知**：星璃 POST 到 `/v1/responses`，每次创建完整 agent turn

导致每小时 token 消耗超过 100 万，大部分浪费在空轮询上。

#### 解决方案

**璃侧（macOS 主机）**：

使用 `launchd WatchPaths` 监听 `inbox/openclaw/` 目录，新文件写入时触发 `li-inbox-watcher.sh`，脚本通过 `openclaw system event --mode now` 唤醒主会话处理。launchd 配置文件：

```xml
<!-- ~/Library/LaunchAgents/ai.openclaw.li-inbox-watcher.plist -->
<key>WatchPaths</key>
<array>
    <string>/Users/ktsama/docker/shared/li-comm/inbox/openclaw/</string>
</array>
<key>QueueDirectories</key>
<array>
    <string>/Users/ktsama/docker/shared/li-comm/inbox/openclaw/</string>
</array>
```

> `QueueDirectories` 确保同一目录 30 秒内的多次变化只触发一次，防止突发消息风暴。

**星璃侧（Docker 容器内）**：

将 bridge 插件 v3.2 升级到 v3.3：
- 高频轮询（3s 扫描）→ **watchdog mtime 监听**（2s 检查目录 mtime，不读文件内容，几乎零开销）
- 新增 **5 分钟兜底轮询**（防止 watchdog 丢失事件）
- HTTP 通知从 POST `/v1/responses`（完整 agent turn）→ POST `/v1/system/events`（轻量 system event）

**心跳优化**（附加）：
- `lightContext: true`：心跳只注入 HEARTBEAT.md，不注入全部 bootstrap 文件
- 双璃 inbox 扫描 cron 已禁用（事件驱动替代）

#### 效果对比

| 指标 | v3.2 轮询 | v3.3 事件驱动 |
|------|----------|--------------|
| 璃侧 inbox 扫描频率 | 每 30 分钟（cron） | 仅新消息时触发 |
| 星璃侧扫描频率 | 每 3 秒 | 每 2 秒 mtime 检查（极轻量） |
| HTTP 通知 token 开销 | 完整 agent turn | 轻量 system event |
| 璃侧响应延迟 | 最长 30 分钟 | ~1 秒（实测） |
| 星璃侧兜底 | 无 | 每 5 分钟完整扫描 |
| 预估 token 消耗/小时 | ~100 万+ | ~6-10 万 |

#### 关键文件

| 文件 | 位置 | 作用 |
|------|------|------|
| launchd plist | `~/Library/LaunchAgents/ai.openclaw.li-inbox-watcher.plist` | macOS 文件事件监听 |
| watcher 脚本 | `~/.openclaw/workspace/scripts/li-inbox-watcher.sh` | 事件触发后调用 system event |
| bridge 插件 | `/AstrBot/data/plugins/openclaw_bridge/main.py` | 星璃侧通信插件 v3.3 |
| 心跳配置 | `~/.openclaw/openclaw.json` → `heartbeat.lightContext` | 减少心跳 token |

#### 注意事项

- `launchd WatchPaths` 需要 `QueueDirectories` 配合，否则高并发写入会触发多次
- Docker 容器内无法使用 macOS FSEvents，只能用 Python mtime 轮询（已实现）
- 星璃的兜底轮询（5 分钟）不可省略，防止 watchdog 进程异常退出导致消息丢失
- 星璃 HTTP 通知 API 从 `/v1/responses` 改为 `/v1/system/events`，前者是 OpenAI 兼容 API 会创建完整 agent turn

### 参考链接

- [launchd WatchPaths 文档](https://developer.apple.com/documentation/launchd) - macOS 原生事件监听

### 验证记录

- [2026-03-26] 初次记录，来源：从 v3.2 轮询迁移到 v3.3 事件驱动的完整实践
- [2026-03-26] 端到端测试通过：launchd WatchPaths 触发 → system event 发出 → 璃处理消息 → 星璃 watchdog 检测 → 正常通信
