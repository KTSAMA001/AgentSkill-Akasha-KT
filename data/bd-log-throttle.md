# BD 节点日志频率控制 {#bd-log-throttle}

**收录日期**：2026-02-03
**标签**：#unity #experience #editor #behavior-designer
**来源**：KTSAMA 实践经验
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)

### 问题/场景

行为树节点的 `OnUpdate` 可能每帧执行，如果在其中打印日志会导致：
- Console 刷屏
- 性能下降
- 难以定位关键信息

### 解决方案

添加日志频率控制，限制同一消息最多每秒输出一次：

```csharp
public class MyConditional : ProfilingConditional
{
    // 日志频率控制
    private float _lastLogTime = 0f;
    private const float LOG_INTERVAL = 1f; // 秒

    private bool CanLog()
    {
        float currentTime = Time.time;
        if (currentTime - _lastLogTime >= LOG_INTERVAL)
        {
            _lastLogTime = currentTime;
            return true;
        }
        return false;
    }

    public override TaskStatus OnUpdate_Profiler()
    {
        if (someConditionFailed)
        {
            if (CanLog())
                Debug.LogWarning($"KT---{GetType().Name}---失败原因---{DateTime.Now:HH:mm:ss}");
            return TaskStatus.Failure;
        }
        return TaskStatus.Success;
    }
}
```

### 关键代码

- 使用 `Time.time` 而非 `DateTime.Now` 比较（性能更好）
- 每个节点实例独立计时
- 日志格式遵循项目规范：`KT---类名---信息---时间`

### 验证记录

| 日期 | 验证者 | 结果 |
|------|--------|------|
| 2026-02-03 | KT | ✅ 日志频率正常控制，不再刷屏 |
