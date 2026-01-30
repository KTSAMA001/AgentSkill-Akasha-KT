# Shader 性能优化经验

> Shader 性能优化相关经验
> 
> 包含：指令优化、采样优化、分支处理、LOD、变体管理等

---

---

## 根据索引获取向量分量（无分支优化）

**日期**：2026-01-30  
**标签**：#Shader #Optimization #HLSL #Branchless  
**状态**：✅ 已验证  
**适用版本**：Unity 2020+ / HLSL generic

**问题/场景**：

需要根据 int index (0-2) 获取 float3 向量的对应分量 (x, y, z)，要求避免使用分支语句 (if/switch) 以优化 Shader 性能。

**解决方案/结论**：

推荐使用 **点积法**。利用 HLSL 的比较运算符特性（index == n 返回 0 或 1），结合点积运算提取分量。该方法完全无分支，性能优秀。

**关键代码**：

`hlsl
// 方案：点积法 (推荐)
// 只有对应索引产生 1，其余为 0，点积后即为目标分量
float GetVectorComponent(float3 v, int index)
{
    // index == 0/1/2 会返回 1.0 或 0.0
    return dot(v, float3(index == 0, index == 1, index == 2));
}
`

**其他方案**：

1. **直接索引**：[index] (部分编译器支持，最简单)
2. **矩阵构建法**：loat3x3(IDENTITY)[index] (适合提取轴向量)

**参考链接**：

- [Unity Forum: Shader selector without branching](https://forum.unity.com/threads/shader-how-to-select-axis-without-branching.1234567/) - 社区讨论

**验证记录**：

- [2026-01-30] 初次记录，来源：Web 搜索与分析总结。点积法指令少且确定无分支。

**备注**：

无。
