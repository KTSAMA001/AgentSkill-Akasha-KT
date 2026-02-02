## AstrBot "messages 参数非法" 错误
**收录日期**：2026-02-02
**更新日期**：2026-02-02
**标签**：#AstrBot #Bug #工具调用 #上下文截断 #智谱AI #调查中
**状态**：⚠️ 部分解决（v4.13.x 仍有报告）
**适用版本**：AstrBot v3.5.x ~ v4.13.x

### 问题现象
在执行某些操作或生成回复后，AstrBot 返回错误：
```
错误类型: BadRequestError
错误信息: Error code: 400 - {'error': {'code': '1214', 'message': 'messages 参数非法。请检查文档。'}}
```

或者更具体的错误信息：
```
Error code: 400 - {'error': {'message': "Messages with role 'tool' must be a response to a preceding message with 'tool_calls'", 'type': 'invalid_request_error'}}
```

### 触发场景
1. 尝试使用工具调用（如 `/找` 命令搜索、网页搜索等）后继续对话
2. 对话历史较长，触发了上下文截断机制
3. 设置了较短的 `max_context_length` 和 `dequeue_context_length`
4. **使用智谱AI（ZhipuAI）作为 LLM 提供商时**

---

## 可能的原因（多种情况）

### 原因一：工具调用消息链被截断（v3.5.x 已修复，但 v4.13.x 可能仍有边缘情况）

当 AstrBot 调用工具（函数）时，会产生以下消息序列：
1. **User 消息** - 用户输入
2. **Assistant tool_calls 消息** - 模型调用工具
3. **Tool 消息** - 工具返回结果
4. **Assistant 消息** - 模型最终回复

当上下文超出限制触发截断时，如果只删除了 1、2 而保留了 3、4，就会导致：
- `tool` 消息没有对应的 `tool_calls` 前置消息
- API 返回 400 错误："Messages with role 'tool' must be a response to a preceding message with 'tool_calls'"

这是一个已知的 Bug，详见 [GitHub Issue #1243](https://github.com/AstrBotDevs/AstrBot/issues/1243)。

> ⚠️ **注意**：虽然官方声称在 v3.5.3.2+ 已修复，但用户反馈在 v4.13.x 仍然遇到此问题，可能存在其他触发路径或边缘情况。

### 原因二：智谱AI（ZhipuAI）特有的消息格式要求 🆕

**智谱AI 对 messages 参数有严格的格式要求**，这与 OpenAI 兼容 API 存在差异：

#### ❌ 不支持只有 system 消息
智谱AI **不允许 messages 列表中只有 `role: system` 的消息**：
```json
// ❌ 错误：会触发 1214 错误
{
  "messages": [
    {"role": "system", "content": "你是一个助手。"}
  ]
}
```

#### ✅ 必须包含 user 消息
```json
// ✅ 正确：必须有 user 消息
{
  "messages": [
    {"role": "system", "content": "你是一个助手。"},
    {"role": "user", "content": "你好"}
  ]
}
```

**触发场景**：
- 会话刚开始，只配置了 system prompt 但用户还未发送消息
- 某些插件或工作流在初始化时只构造了 system 消息
- 上下文压缩后意外删除了所有 user 消息

### 原因三：消息格式结构错误

其他可能导致 1214 错误的消息格式问题：
- `role` 字段缺失或值不正确
- `content` 字段为空字符串或缺失
- 消息数组为空 `[]`
- 使用了智谱AI不支持的 role 类型
- JSON 格式错误或类型不匹配

### 原因四：中转层（One-API）兼容性问题

如果使用 One-API 或其他 API 中转服务连接智谱AI：
- 中转层可能在转换参数时引入格式问题
- 不同版本的中转层对智谱AI的兼容性不同
- 建议直接用 curl 测试智谱AI直连，排除中转层问题

---

## 解决方案

### 方案一：检查 LLM 提供商配置（智谱AI 用户必看）⭐

如果你使用的是**智谱AI（ZhipuAI/GLM）**：

1. **确保消息列表中始终有 user 消息**
2. 检查 AstrBot 配置中的 system prompt 设置，确保不会在没有 user 消息时发送请求
3. 如果问题持续，尝试切换到其他 LLM 提供商（如 DeepSeek、OpenAI）验证是否为智谱AI特有问题

### 方案二：调整上下文配置

增大上下文相关配置，减少截断触发：

```yaml
# astrbot.yaml 或通过 Web UI 配置
llm:
  max_context_length: 8000   # 增大上下文长度
  dequeue_context_length: 4  # 增大每次丢弃的轮数
```

### 方案三：清空会话历史

出现错误后，尝试：
1. 清空当前会话的历史消息
2. 重新开始对话
3. 观察是否在特定操作（如工具调用）后复现

### 方案四：查看详细日志排查

1. 查看 AstrBot 日志文件 (`platform.log` 或容器日志)
2. 找到请求失败时的完整 messages 内容
3. 检查是否存在：
   - 只有 system 消息
   - tool 消息缺少前置 tool_calls
   - 其他格式问题

```bash
# Docker 查看日志
docker logs astrbot --tail 500 | grep -A 20 "1214"
```

### 方案五：向官方反馈（如果以上方案都无法解决）

如果问题仍然存在，建议：
1. 收集完整的错误日志和触发步骤
2. 在 [AstrBot GitHub Issues](https://github.com/AstrBotDevs/AstrBot/issues) 提交新的 Bug 报告
3. 说明你的版本号（v4.13.x）、LLM 提供商、部署方式等信息

---

## 相关错误码说明

| 错误码 | 含义 | 常见原因 |
|--------|------|----------|
| 1214 | messages 参数非法 | 格式错误、只有system消息、工具调用链断裂 |
| 400 + tool role error | tool 消息缺少前置 tool_calls | 上下文截断问题 |
| 400 + invalid_request_error | 请求格式非法 | 消息结构不符合 API 要求 |

---

## 参考链接与信息来源

### 📌 关于工具调用截断问题（原因一）的来源
- [GitHub Issue #1243 - 调用函数工具可能导致400错误](https://github.com/AstrBotDevs/AstrBot/issues/1243)
  - 这是 AstrBot 官方 GitHub 上的 Bug 报告，详细描述了工具调用消息链截断导致 400 错误的问题
- [AstrBot 官方文档 - 上下文压缩](https://docs.astrbot.app/en/use/context-compress.html)
- [DeepWiki - Tool Call Message Format](https://deepwiki.com/AstrBotDevs/AstrBot/6.2-tool-call-message-format)

### 📌 关于智谱AI消息格式要求（原因二）的来源
- [智谱AI SDK Issues #14 - messages参数非法](https://github.com/MetaGLM/zhipuai-sdk-python-v4/issues/14)
  - 这是智谱AI官方 Python SDK 的 GitHub Issues，用户报告只有 system 消息会导致 1214 错误
- [智谱 AI API 错误码文档](https://docs.bigmodel.cn/cn/faq/api-code)
  - 智谱AI官方错误码说明文档，1214 表示"参数非法"
- [Cangjie Magic Issue #24](https://gitcode.com/Cangjie-TPC/CangjieMagic/issues/24)
  - 社区用户报告调用智谱AI接口时的 messages 参数非法错误
- [AgentScope Issue #258 - 智谱 prompt 参数非法](https://github.com/agentscope-ai/agentscope/issues/258)
  - AgentScope 项目中报告的智谱AI参数问题
- [Dify Discussions #3579](https://github.com/langgenius/dify/discussions/3579)
  - Dify 社区讨论：messages 必须添加 user 角色

### 📌 其他参考
- [AstrBot 配置文件说明](https://docs.astrbot.app/config/astrbot-config.html)
- [AstrBot FAQ](https://docs.astrbot.app/faq.html)

> **注意**：以上关于"智谱AI不支持只有system消息"的结论主要来自社区 Issues 和用户报告，尚未在智谱AI官方文档中找到明确说明。如果您的场景不符合，请以实际测试结果为准。

---

## 验证记录
- [x] 2026-02-02 通过官方文档和 GitHub Issues 确认工具调用截断问题
- [x] 2026-02-02 确认智谱AI对消息格式有特殊要求（必须包含user消息）
- [ ] v4.13.x 版本问题待进一步验证（用户反馈仍存在问题）
- [ ] 需要收集更多日志信息确定具体触发原因

---

## 排查建议（给 v4.13.x 用户）

如果你在 v4.13.x 仍然遇到此问题，请：

1. **确认你使用的 LLM 提供商**
   - 如果是智谱AI → 检查原因二
   - 如果是 DeepSeek/OpenAI → 检查原因一

2. **记录触发时机**
   - 新会话第一条消息就报错？→ 可能是只有 system 消息
   - 工具调用后报错？→ 可能是上下文截断
   - 长对话后报错？→ 可能是截断或格式累积错误

3. **提供日志信息**
   - 如果方便，请在 Issue 中提供触发时的完整 messages 内容

---

## 相关经验
- [AstrBot 集成 MCP 服务经验](../../ai/astrbot.md)
- [MCP 协议与 Agent 服务开发经验](../../ai/mcp.md)
