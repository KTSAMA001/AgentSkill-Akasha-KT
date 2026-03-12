# 飞书操作技能 (feishu-operations)

**标签**：#tools #feishu #ai #experience #openclaw
**来源**：实践总结
**收录日期**：2026-03-12
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：OpenClaw 2026.3+

### 概要

OpenClaw 的飞书操作技能，提供文档创建、文件发送、权限管理的标准流程。解决文档创建后内容为空、文件发送失败等常见问题。

### 核心功能

| 模块 | 功能 | 关键工具 |
|------|------|----------|
| **文档操作** | 创建/编辑/读取/追加/删除 | `feishu_doc` |
| **文件发送** | 上传文件并发送到私聊/群聊 | `feishu-send-file.sh` |
| **权限管理** | 添加/查看/移除权限 | `feishu_perm` |

### 关键规则

#### 规则 1：文档创建必须连续执行

**错误流程**：
```
1. create → 2. 返回链接 → 3. 用户检查（空白）→ 4. write
```

**正确流程**：
```
1. create → 2. write → 3. read 确认 → 4. 返回链接
```

⚠️ 步骤 1-3 必须连续执行，不要让用户在中间检查！

#### 规则 2：文件发送需要两步

`message` 工具的 `path`/`media` 参数**不会上传文件**。

正确方式：
```bash
# 使用封装脚本（推荐）
~/.openclaw/skills/feishu-operations/scripts/feishu-send-file.sh <文件> <接收者ID>

# 或手动两步：
# 1. POST im/v1/files 上传 → 获取 file_key
# 2. POST im/v1/messages 发送 file 类型消息
```

### 关键代码

```bash
# 发送文件到飞书私聊
~/.openclaw/skills/feishu-operations/scripts/feishu-send-file.sh /tmp/report.xlsx ou_xxx

# 发送到群聊
~/.openclaw/skills/feishu-operations/scripts/feishu-send-file.sh /tmp/report.xlsx oc_xxx chat_id
```

### 常见错误

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 文档空白 | create 和 write 分开执行 | 连续执行 create → write → read |
| 文件没发出去 | 用了 message 的 path 参数 | 用脚本或手动上传 + 发送 |
| 权限添加失败 | token 类型不对 | 确认 type 参数（docx/doc/sheet） |
| 跨通道消息失败 | 当前绑定通道与目标通道不同 | 只在当前通道回复，不要跨通道发 |

### 技能文件结构

```
feishu-operations/
├── SKILL.md                    # 技能定义
└── scripts/
    └── feishu-send-file.sh     # 文件发送脚本
```

### 参考链接

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [feishu-doc 技能](./feishu-doc.md) - 飞书文档操作（系统内置）

### 验证记录

- [2026-03-12] 初次记录，来源：创建技能的实践总结
- [2026-03-12] 测试验证：文档创建（create→write→read）、文件发送均通过
