# Behavior Designer Task Attributes 系统

**标签**：#unity #ai #knowledge #behavior-designer
**来源**：[Opsive 官方文档](https://opsive.com/support/documentation/behavior-designer/task-attributes/)
**收录日期**：2026-02-03
**来源日期**：2026-02-03
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐(官方)
**适用版本**：Behavior Designer（2026-02-03 官方文档时点）

### 概要

Behavior Designer 提供一组 Task Attribute，用于声明行为树任务的编辑器描述、分类、显示名称、图标、帮助链接和必填字段等元数据。

### 内容

#### 定义/概念

Behavior Designer 的 Task Attributes 用于定义 Task 的元数据和显示行为，让自定义任务在编辑器中更容易被查找、理解和维护。

#### 内置 Task Attributes

| Attribute | 用途 | 示例 |
|-----------|------|------|
| `[TaskDescription("...")]` | 任务描述，显示在编辑器底部 | `[TaskDescription("移动到目标点")]` |
| `[TaskCategory("...")]` | 分类，支持嵌套，用 `/` 分隔 | `[TaskCategory("Custom/Movement")]` |
| `[TaskName("...")]` | 自定义显示名称 | `[TaskName("移动")]` |
| `[TaskIcon("...")]` | 任务图标路径 | `[TaskIcon("Assets/Icons/move.png")]` |
| `[HelpURL("...")]` | 帮助文档链接 | `[HelpURL("http://docs.example.com")]` |
| `[LinkedTask]` | 关联其他 Task | 用于 TaskGuard 等场景 |
| `[RequiredField]` | 必填字段标记 | 编辑器中会特殊提示 |

#### 字段 Attributes

| Attribute | 命名空间 | 说明 |
|-----------|----------|------|
| `[Tooltip]` | `BehaviorDesigner.Runtime.Tasks` | Behavior Designer 专用字段提示 |
| `[Tooltip]` | `UnityEngine` | Unity 原生提示 |
| `[Header]` | `UnityEngine` | 分组标题，Behavior Designer 中可用 |

#### 关键点

- `TaskCategory` 支持多级嵌套，例如 `"RTS/Harvester"` 会创建两层菜单。
- `TaskDescription` 支持换行符 `\n`。
- `TaskIcon` 路径支持 `{SkinColor}` 关键字，用于自动适配 Light/Dark 主题。
- Behavior Designer 有自己的 `TooltipAttribute`，与 `UnityEngine.TooltipAttribute` 同名，使用时需要注意命名空间冲突。

### 参考链接

- [官方文档 - Task Attributes](https://opsive.com/support/documentation/behavior-designer/task-attributes/) - Behavior Designer Task Attribute 官方说明。

### 相关记录

- [Behavior Designer ObjectDrawer 系统](./behavior-designer-object-drawer.md) - 同属 Behavior Designer 编辑器扩展能力。
- [BD 节点 Tooltip 命名空间冲突解决](./bd-tooltip-namespace-conflict.md) - 字段提示 Attribute 的实践问题。

### 验证记录

- [2026-04-15] 结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。
---
