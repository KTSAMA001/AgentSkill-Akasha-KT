# OpenClaw 插件持久化方案

> 创建时间：2026-03-09
> 标签：#OpenClaw #Docker #插件 #持久化 #运维

## 问题描述

Docker 容器重建后，OpenClaw 插件丢失依赖，导致通道无法加载。

**典型错误**：
```
feishu failed to load: Cannot find module '@larksuiteoapi/node-sdk'
```

## 根因

- `/app/extensions/` 是容器内置路径，容器重建会丢失
- 插件的 `node_modules` 没有持久化

## 完整解决方案

### 步骤 1：复制插件到工作空间

```bash
cp -r /app/extensions/<plugin-name> ~/.openclaw/extensions/
```

### 步骤 2：安装依赖到工作空间

```bash
cd ~/.openclaw/extensions/<plugin-name> && npm install
```

### 步骤 3：配置插件加载路径

**用 config.patch 更新配置**：

```bash
# 方式1：通过工具
gateway action="config.patch" raw='{"plugins":{"load":{"paths":["~/.openclaw/extensions","/app/extensions"]}}}'

# 方式2：手动编辑 openclaw.json
```

**配置示例**：

```json
{
  "plugins": {
    "load": {
      "paths": [
        "~/.openclaw/extensions",  // 工作空间（持久化，优先）
        "/app/extensions"          // 容器内置（回退）
      ]
    }
  }
}
```

## 核心原则

| 原则 | 说明 |
|------|------|
| **工作空间优先** | `~/.openclaw/` 是持久化的，容器重建不丢失 |
| **配置加载路径** | 让 OpenClaw 知道从哪里加载插件 |
| **依赖随插件走** | `node_modules` 和插件放在同一目录 |

## 适用场景

- 任何需要持久化的 OpenClaw 插件
- 自定义插件开发
- 依赖第三方库的插件（如飞书的 `@larksuiteoapi/node-sdk`）

## 注意事项

1. **修改配置前必须检查 schema**：
   ```bash
   gateway action="config.schema.lookup" path="plugins.load"
   ```

2. **不要随意添加已废弃的配置项**：
   - OpenClaw 2026.3.7 已移除 `gateway.channels`
   - 修改前必须确认当前版本支持的配置

3. **config.patch 接收的是对象**，不是数组：
   ```json
   // ✅ 正确
   {"plugins": {"load": {"paths": [...]}}}

   // ❌ 错误
   ["path1", "path2"]
   ```

## 相关记录

- OpenClaw v2026.3.7 升级报告
- 飞书通道配置

---

_来源：2026-03-09 实际问题解决_
