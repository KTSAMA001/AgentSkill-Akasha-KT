# 配置表 ID 一键生成枚举

**标签**：#unity #tools #excel #experience
**来源**：实践总结；本地项目实现复核
**收录日期**：2026-03-05
**更新日期**：2026-05-12
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2022.3（项目实测）；Unity 2020.3+ 未在本次复核中确认

### 概要

将导表后生成的 JSON/bytes 配置中的稳定 ID 生成 C# 枚举，供 Unity 编辑器工具通过枚举或 Odin 下拉选择，避免在 GM、音频测试等工具中手动输入裸 ID。

## 内容

### 问题场景

- 在编辑器工具或预制体字段中手动填写配置 ID，容易填错或失去语义。
- 只看到数字 ID 时，不方便从代码或 Inspector 反查用途。
- 配置表新增、改名后，如果没有同步生成枚举，下拉项和运行时配置会脱节。

### 已验证的实现边界

当前项目验证到的链路是：Excel 或配置源先导出为 `Assets/GameRes/BundleRes/Data/Config/*.bytes`，工具再读取这些 JSON/bytes 配置生成 C# 枚举；不是直接读取 `.xlsx` 文件生成枚举。

已复核的实现包括：
- `EnumGeneratorTool.GenerateEnumFromJson<T>`：读取 JSON/bytes 配置，提取名称和 ID，写入枚举脚本。
- `ItemGMSO.GenerateEnumScripts`：从 `ItemConfig.bytes` 生成 `ItemCreateEnum_KT_Tool`。
- `AudioTesterSO.GenerateAudioEnumScripts`：从 `AudioConfig.bytes` 生成 `AudioTestEnum_KT_Tool`。
- 旧项目 `QuicklyGMPanelEditer.GenerateEnumScripts`：从 `MonsterAttibuteDataConfig.bytes` 生成怪物创建枚举。

### 解决方案

**数据结构设计**：
1. 运行时继续使用配置管理器中的 ID 字典做查找。
2. 编辑器工具额外生成一份仅用于选择和调用的 ID 枚举。

**编辑器选择方式**：
- 普通 enum 字段可以避免裸数字输入，但不保证具备搜索能力。
- 需要搜索体验时，应使用 Odin `ValueDropdown` 或自定义下拉，把枚举值转换为可搜索列表项。

### ID 设计规范

**ID 应保持稳定**：
- 一旦进入配置和资源引用链路，尽量不要改已有 ID。
- 需要分段编码时，先明确位数、类别含义和预留区间。
- 若在 C# 源码中使用数字分隔符，例如 `7001_01_01`，它只是源码可读性写法，实际枚举值仍是整数 `70010101`；生成出的枚举文件可以直接写普通整数值。

**已观察到的项目格式示例**：
```csharp
public enum AudioTestEnum_KT_Tool
{
    audio_Item_AppleEat_01_ID_10000102 = 10000102,
    audio_StrikeAxe_01_ID_20000101 = 20000101,
}
```

### 实现思路

1. 从导表后的 JSON/bytes 配置读取数据。
2. 提取 ID 和显示名称/资源路径。
3. 清理名称中的非法字符，必要时补前缀或后缀，避免生成非法 C# 标识符。
4. 生成 C# 枚举代码并刷新 `AssetDatabase`。
5. 在编辑器工具中用枚举字段、Odin `ValueDropdown` 或自定义下拉选择 ID。

### 注意事项

- 不要把“读取 Excel”写成已验证链路；当前证据只验证到读取导表后的 JSON/bytes 配置。
- 生成器必须处理空名称、非法字符、重复名称、C# 关键字和数字开头等边界，否则会生成不可编译的枚举。
- 对中文名称生成的枚举在 C# 中可以编译，但跨工具搜索、代码审查和版本 diff 的可读性较差；更推荐生成稳定英文/拼音/资源路径派生名称。
- 配置表改动后需要重新生成枚举，否则枚举值可能落后于运行时配置字典。

### 验证记录

- [2025-03-07] 实际项目验证。
- [2026-03-05] 从长期记录提取到阿卡西。
- [2026-05-12] 事实复核：原记录将链路表述为“Excel 表格直接导出枚举”不准确；本地项目实现均为读取导表后的 JSON/bytes 配置生成枚举，并将适用版本收窄到 Unity 2022.3 实测。
