# LLM API image_url 字段反序列化错误 - "unknown variant `image_url`, expected `text`"

**标签**: #ai #experience #astrbot #bug
**来源**: KTSAMA 实践经验
**收录日期**: 2026-02-16
**来源日期**: 2026-02-16
**更新日期**: 2026-02-16
**状态**: ⚠️ 待调查
**可信度**: ⭐⭐⭐ (个人经验验证)
**适用版本**: AstrBot v4.17.x+

### 概要

在 AstrBot 中使用某些 LLM 模型时，触发 `All chat models failed: BadRequestError: Error code: 400`，错误信息显示在 `messages[11]` 位置遇到 `image_url` 字段，但 API 期望的是 `text` 字段。

### 问题现象

执行某些操作时，AstrBot 返回以下错误：

```
All chat models failed: BadRequestError: Error code: 400 - {'error': {'message': 'Failed to deserialize the JSON body into the target type: messages[11]: unknown variant `image_url`, expected `text` at line 1 column 867429', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

**错误特征**:
- 错误类型: `BadRequestError`
- 错误码: 400
- 内部错误类型: `invalid_request_error`
- 具体信息: `Failed to deserialize the JSON body into the target type: messages[11]: unknown variant `image_url`, expected `text`

### 可能的原因

1. **模型不支持图片输入**:
   - 配置的 LLM 模型（如某些纯文本模型）可能无法处理包含图片的消息
   - 但 AstrBot 的某个插件或功能却尝试发送了带图片的请求

2. **消息格式不符合 API 规范**:
   - 即使是支持多模态的模型，图片内容也应该按照特定格式包裹在 `content` 数组里
   - 例如 OpenAI 的格式是 `{"type": "image_url", "image_url": {"url": "..."}}`
   - 如果直接使用了 `image_url` 这个字段名，或者格式不对，就会报这个错

3. **插件或功能配置问题**:
   - 可能是某个插件（如定时转载 AstrBook 帖子的任务）在生成请求时，错误地构造了包含图片的消息
   - AstrBot 内部的消息构造逻辑可能存在兼容性问题

### 排查方向

1. **确认模型能力**:
   - 检查 AstrBot 配置的 LLM 模型是否支持图片/多模态输入
   - 如果使用的是纯文本模型（如某些 GPT-3.5 变体），尝试切换到支持多模态的模型（如 GPT-4V、Claude-3）

2. **查看触发场景**:
   - 记录报错是在执行什么操作时出现的
   - 是普通的对话，还是某个特定插件/功能触发的？
   - 检查是否有插件配置了自动发送图片或富媒体内容

3. **检查日志细节**:
   - 查看 AstrBot 的完整日志，找到报错时的 `messages` 内容
   - 分析 `messages[11]` 的具体结构，确认是否存在格式错误

4. **对比已知错误**:
   - 此错误与之前记录的 "messages 参数非法" 错误（智谱AI特有格式要求）不同
   - 本次错误核心是 `image_url` 字段不被识别，而非消息角色或格式问题

### 临时解决方案

1. **切换模型**: 暂时使用纯文本模型，避免触发多模态相关功能
2. **禁用相关插件**: 如果怀疑是某个插件导致，暂时禁用该插件
3. **检查配置**: 确认 LLM 提供商和模型名称是否正确，某些模型可能名称相似但能力不同

### 相关记录

- [AstrBot "messages 参数非法" 错误](./astrbot-messages-param-error.md) - 智谱AI特有的消息格式要求
- [AstrBot 集成 MCP 服务经验](./astrbot-mcp-service-config.md) - 其他 AstrBot 相关经验

### 验证记录

- [2026-02-16] 初步记录错误现象和可能原因，待 KT 进一步排查
