# 场景引用资源加载机制

**标签**：#unity #performance #scene #experience
**来源**：实践总结
**收录日期**：2026-03-05
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐
**适用版本**：Unity 2020.3+

### 概要
不要在场景中提前引用后续游戏过程中才需要的资源，Unity 场景加载机制会在运行时加载场景中引用的全部资源。

## 内容

### Unity 场景加载机制

- 场景加载时，会自动加载场景中所有被引用的资源
- 无论资源是否在当前视野内或后续才会用到

### 问题场景

```
场景中直接引用了：
- Boss 战的特效（但 Boss 在关卡末尾）
- 结局 CG 的视频（但玩家还没通关）
- 所有技能的音效（但角色只有几个技能）
```

### 解决方案

**延迟加载策略**：
1. 使用 Addressables 或 AssetBundle
2. 运行时按需加载资源
3. 使用完后释放

**代码示例**：
```csharp
// ❌ 错误：场景直接引用
public GameObject bossPrefab; // 场景加载时就加载

// ✅ 正确：按需加载
public string bossAddress;
async void LoadBoss()
{
    var handle = Addressables.LoadAssetAsync<GameObject>(bossAddress);
    await handle.Task;
    Instantiate(handle.Result);
}
```

### 注意事项

- 检查场景中的隐藏引用（如 Animator 中的 Animation Clip）
- 音效、特效等资源建议使用 Addressables 管理
- 预加载也要有选择性，不要全量加载

### 验证记录
- [2026-03-05] 从长期记录提取到阿卡西，为 Unity 基础机制
