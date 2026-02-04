---

## AstrBot 集成 MCP 服务经验

**收录日期**：2026-02-01
**来源日期**：2026-01-30 ~ 2026-02-01
**标签**：#AstrBot #MCP #AI #容器 #集成
**状态**：✅ 已验证
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
- [MCP 协议与 Agent 服务开发经验](./mcp.md)
- [Docker 容器部署经验](../tools/misc.md)


---

## AstrBot 插件文件上传到QQ实现

**收录日期**：2026-02-04
**来源日期**：2026-02-04
**标签**：#AstrBot #插件开发 #文件上传 #NapCat #OneBot
**状态**：✅ 已验证
**适用版本**：AstrBot v4.13.2+, OneBot v11 (NapCat)

**问题/场景**：

在 AstrBot 插件中需要将本地文件发送到QQ群聊或私聊，需要通过 NapCat (OneBot v11) 的API接口实现。

**解决方案/结论**：

- 使用 OneBot v11 的 `upload_group_file` 和 `upload_private_file` API
- 通过 `event.bot.api.call_action()` 或 `event.bot.call_api()` 调用API
- 支持三种文件格式（直接路径、file://协议、base64编码）
- 先判断平台类型，确保只在 OneBot v11 环境下执行

**关键代码**：

```python
# 平台判断
platform_name = event.get_platform_name()
if platform_name == "aiocqhttp":  # OneBot v11
    
    # 准备参数
    params = {
        "file": file_path,          # 文件路径
        "name": file_name           # 文件名
    }
    
    # 选择API
    action = ""
    if event.get_group_id():
        params["group_id"] = int(event.get_group_id())
        action = "upload_group_file"      # 群聊上传
    else:
        params["user_id"] = int(event.get_sender_id())
        action = "upload_private_file"     # 私聊上传
    
    # 调用API（两种方式都支持）
    await event.bot.api.call_action(action, **params)
    # 或
    await event.bot.call_api(action, **params)
```

**文件格式Fallback机制**：

```python
try:
    # 方式1：直接路径
    params["file"] = file_path
    await event.bot.api.call_action(action, **params)
except:
    try:
        # 方式2：file:// 协议
        params["file"] = f"file://{file_path}"
        await event.bot.api.call_action(action, **params)
    except:
        # 方式3：base64 编码
        with open(file_path, "rb") as f:
            b64_content = base64.b64encode(f.read()).decode('utf-8')
        params["file"] = f"base64://{b64_content}"
        await event.bot.api.call_action(action, **params)
```

**参考链接**：
- [web_archive_mcp_v2 插件源码](/AstrBot/data/plugins/web_archive_mcp_v2/main.py)
- [OneBot v11 API 文档](https://11.onebot.dev/api/file.html)

**验证记录**：
- [2026-02-04] 通过 web_archive_mcp_v2 插件代码分析，确认文件上传实现方式

**相关经验**：
- [AstrBot 集成 MCP 服务经验](#astrbot-集成-mcp-服务经验)
