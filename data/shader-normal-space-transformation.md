# 法线空间变换矩阵（Normal Space Transformation Matrix）

**标签**：#graphics #shader #math #knowledge
**来源**：图形学通用原理 / 实践总结
**收录日期**：2026-03-25
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐
**适用版本**：通用（GLSL / HLSL / Unity Shader）

### 概要
法线（Normal）是方向向量（co-vector），不能直接用模型矩阵变换，必须使用**逆转置矩阵**（inverse transpose）。位置和方向向量则直接使用模型矩阵或其逆矩阵。

### 内容

#### 为什么法线需要逆转置矩阵

法线是垂直于表面的方向向量，本质上是一个 **co-vector**（余向量/对偶向量），而非普通的方向向量。当模型矩阵包含**非均匀缩放**时，直接用模型矩阵变换法线会导致：

1. 法线不再垂直于变换后的表面
2. 光照计算出现明显的明暗错误

**逆转置矩阵的作用**：
- **逆矩阵**：抵消模型矩阵的缩放效果
- **转置**：将 co-vector 从余切空间映射回正确的方向

#### 变换公式速查

| 变换类型 | 位置（Position） | 方向（Direction） | 法线（Normal） |
|---------|-----------------|------------------|---------------|
| 对象 → 世界 | `M * vec4(p, 1.0)` | `mat3(M) * d` | `mat3(transpose(inverse(M))) * n` |
| 世界 → 对象 | `inverse(M) * vec4(p, 1.0)` | `mat3(inverse(M)) * d` | `mat3(transpose(M)) * n` |

> - `M` = 模型矩阵（Model Matrix）
> - 对象→世界的法线矩阵 = `(M^-1)^T`
> - 世界→对象的法线矩阵 = `(M^-1)^T^-1 = M^T`（逆转置的逆就是转置本身）

#### 均匀缩放简化

当模型矩阵**仅包含均匀缩放、旋转和平移**时（无非均匀缩放），可以省略逆转置：

```glsl
// 均匀缩放 + 旋转：直接用 mat3(M) 即可
vec3 worldNormal = normalize(mat3(modelMatrix) * objectNormal);

// 对应的，世界→对象：直接用 mat3(inverse(M))
vec3 objectNormal = normalize(mat3(inverse(modelMatrix)) * worldNormal);
```

> 实际开发中，如果无法确定是否有非均匀缩放，始终使用逆转置矩阵是最安全的做法。

#### 预计算 normalMatrix

每帧在 shader 中计算 `inverse` + `transpose` 开销较大，通常在 CPU 端预计算：

```glsl
// CPU 端计算
Matrix4x4 normalMatrix = modelMatrix.inverse.transpose;

// 传给 shader（Unity 内置变量）
// unity_WorldToObject = 模型矩阵的逆（左上 3x3）
// 用法：WorldToObject 法线 = transpose(modelMatrix) 的 3x3
```

Unity 内置矩阵：
- `_Object2World` / `unity_ObjectToWorld`：对象→世界模型矩阵
- `_World2Object` / `unity_WorldToObject`：世界→对象（模型矩阵的逆）
- `unity_WorldToObject` 对方向向量取 `mat3` 部分即可

### 关键代码

#### GLSL 完整示例

```glsl
// 对象空间法线 → 世界空间（通用，含非均匀缩放）
vec3 objectToWorldNormal(vec3 objectNormal, mat4 modelMatrix) {
    return normalize(mat3(transpose(inverse(modelMatrix))) * objectNormal);
}

// 世界空间法线 → 对象空间
vec3 worldToObjectNormal(vec3 worldNormal, mat4 modelMatrix) {
    return normalize(mat3(transpose(modelMatrix)) * worldNormal);
}

// 对象空间方向 → 世界空间
vec3 objectToWorldDir(vec3 objectDir, mat4 modelMatrix) {
    return normalize(mat3(modelMatrix) * objectDir);
}

// 世界空间方向 → 对象空间
vec3 worldToObjectDir(vec3 worldDir, mat4 modelMatrix) {
    return normalize(mat3(inverse(modelMatrix)) * worldDir);
}
```

#### Unity ASE（Amplify Shader Editor）节点用法

**世界空间 → 对象空间**：

1. `Vertex Tangent` 节点 → 输出切线向量
2. `World To Object Matrix` 节点 → 输出变换矩阵
3. `Multiply` 节点：切线接 **A**（向量），矩阵接 **B**（矩阵）

```
Vertex Tangent ──→ Multiply.A
World To Object Matrix ──→ Multiply.B
Multiply.Out ──→ 对象空间切线
```

> ⚠️ Multiply 节点做矩阵×向量乘法时，**向量必须在左（A）、矩阵在右（B）**，顺序反了会得到错误结果。

**对象空间 → 世界空间**：使用 `Object To World Matrix` 节点或 `Transform Direction` 节点（模式选 `Object → World`）。

### 参考链接

- [OpenGL Normal Transformation (Lighthouse3D)](https://www.lighthouse3d.com/tutorials/glsl-tutorial/the-normal-matrix/) - 逆转置矩阵原理
- [The Normal Matrix (Scratchapixel)](https://www.scratchapixel.com/lessons/mathematics-physics-for-computer-graphics/geometry/transforming-normals) - 法线变换数学推导

### 相关记录

- [Unity Shader / HLSL 基础知识](./hlsl-syntax-semantics.md) - Shader 语义与语法
- [Amplify Shader Editor 架构解析](./amplify-shader-editor-architecture.md) - ASE 节点系统详解

### 验证记录
- [2026-03-25] 初次记录，来源：图形学通用原理 + ASE 实践验证
