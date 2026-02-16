# LLM API image_url 字段反序列化错误 - "unknown variant `image_url`, expected `text`"

**标签**: #ai #experience #astrbot #bug
**来源**: KTSAMA 实践经验
**收录日期**: 2026-02-16
**来源日期**: 2026-02-16
**更新日期**: 2026-02-16
**状态**: ✅ 已解决
**可信度**: ⭐⭐⭐⭐⭐ (实践验证)
**适用版本**: AstrBot v4.17.x+
**解决日期**: 2026-02-16

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

### 根本原因

**已废弃的"通晓前文"插件导致**：该插件已不再维护，但在 v4.17.x 版本中仍被使用，导致图片消息被错误地传递给不支持视觉的模型。

### 解决方案

**禁用或移除"通晓前文"插件**即可解决问题。

### 历史分析（供参考）

此问题在早期版本中也曾存在，官方已在 v4.11.4 通过以下 PR 修复：
- PR #4367: `sanitize_context_by_modalities`
- PR #4411: 图片占位符支持

但在 v4.17.x 中，由于使用了已废弃的"通晓前文"插件，绕过了这些修复机制。

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

### 官方解决方案

**已在 v4.11.4 版本修复**，相关 PR：

1. **PR #4367 - `sanitize_context_by_modalities`** (2026-01-11 合并)
   - 新增配置项 `sanitize_context_by_modalities`（默认开启）
   - 根据模型的 `modalities` 配置自动过滤不支持的模态内容
   - 模型不支持图片时：自动移除历史消息中的 `image_url` 块
   - 模型不支持工具调用时：移除 tool 角色消息及 tool_calls 字段

2. **PR #4411 - 图片占位符** (2026-01-11 合并)
   - 修复私聊中单独发送图片时 bot 无响应的问题
   - 非视觉模型将图片转换为 `[图片]` 文本占位符，而非静默丢弃

### 解决步骤

1. **升级 AstrBot 到 v4.11.4 或更高版本**

2. **确保 Provider 配置正确**：
   ```yaml
   # 对于不支持图片的模型（如 deepseek-chat）
   modalities: ['text', 'tool_use']

   # 对于支持图片的模型（如 gpt-4-vision）
   modalities: ['text', 'image', 'tool_use']
   ```

3. **确认 `sanitize_context_by_modalities` 已启用**（默认开启）

4. **重启 AstrBot 使配置生效**

### 临时解决方案（旧版本）

1. **切换模型**: 使用支持视觉的模型（如 GPT-4V、Claude-3）
2. **禁用相关插件**: 暂时禁用可能发送图片的插件
3. **检查配置**: 确认 LLM 提供商和模型名称配置正确

### 相关记录

- [AstrBot "messages 参数非法" 错误](./astrbot-messages-param-error.md) - 智谱AI特有的消息格式要求
- [AstrBot 集成 MCP 服务经验](./astrbot-mcp-service-config.md) - 其他 AstrBot 相关经验

### 验证记录

- [2026-02-16] 初步记录错误现象和可能原因
- [2026-02-16] 查阅 AstrBot GitHub 仓库，确认官方已在 v4.11.4 通过 PR #4367 和 #4411 修复此问题
- [2026-02-16] **确认根本原因**：已废弃的"通晓前文"插件导致，禁用后问题解决

### 相关 GitHub Issues / PRs

- [Issue #2894](https://github.com/AstrBotDevs/AstrBot/issues/2894) - 最早报告此问题
- [Issue #4465](https://github.com/AstrBotDevs/AstrBot/issues/4465) - 最新报告，问题偶发
- [PR #4367](https://github.com/AstrBotDevs/AstrBot/pull/4367) - 核心修复：sanitize_context_by_modalities
- [PR #4411](https://github.com/AstrBotDevs/AstrBot/pull/4411) - 图片占位符支持
