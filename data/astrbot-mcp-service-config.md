# AstrBot 集成 MCP 服务经验

**标签**：#ai #experience #mcp #astrbot
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-01
**来源日期**：2026-01-30 ~ 2026-02-01
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：AstrBot v4.13.2+

**问题/场景**：

在 AstrBot 容器中集成 MCP 工具服务，需解决网络、依赖、工具命名冲突等问题。

**解决方案/结论**：

- MCP 服务建议以 stdio 模式运行，避免 SSE 网络限制。
- 工具命名统一加 kt_ 前缀，防止与 AstrBot 内置工具冲突。
- 容器内需安装 Playwright 浏览器依赖。
- MCP 服务路径配置需与 AstrBot mcp_server.json 保持一致。

**关键代码**：

```json
{
  "mcpServers": {
    "web_search_mcp": {
      "active": true,
      "command": "python",
      "args": ["-m", "web_search_mcp.server"],
      "env": {"PYTHONPATH": "/AstrBot/data/mcp_servers"}
    }
  }
}
```

**参考链接**：
- [AstrBot 官方文档](https://github.com/AstrBot/AstrBot)

**验证记录**：
- [2026-02-01] MCP 工具服务在 AstrBot 容器内成功集成，工具可用

**相关经验**：
- [MCP 协议与 Agent 服务开发经验](./mcp-protocol-agent-dev.md)
