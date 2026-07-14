# 法线空间变换矩阵（Normal Space Transformation Matrix）

**标签**：#graphics #shader #math #knowledge
**来源**：图形学通用原理 / 实践总结
**收录日期**：2026-03-25
**更新日期**：2026-07-14
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐
**适用版本**：通用（GLSL / HLSL / Unity Shader）

### 概要
法线在代码中通常用三维向量存储，但它表达的是“与表面切平面垂直”这一约束，在线性变换下应按余向量（co-vector）的规则处理。模型矩阵含非均匀缩放或剪切时，法线必须使用**逆转置矩阵**（inverse transpose），否则会失去与变换后表面的垂直关系。

### 内容

#### 一、阅读约定：先认清每个符号

本文统一采用数学中常见的**列向量**约定：

| 符号 | 含义 |
|------|------|
| `T` | 对象空间中的表面切线（Tangent） |
| `N` | 对象空间中的表面法线（Normal） |
| `M` | 对象到世界的模型矩阵；推导中只使用其可逆的 3×3 线性部分 |
| `T'`、`N'` | 变换到世界空间后的切线与法线；右上角 `'` 表示“变换后” |
| `A^T` | 矩阵 `A` 的转置；这里的 `T` 表示 transpose，不是切线变量 |
| `A^-1` | 矩阵 `A` 的逆矩阵 |
| `A^-T` | 逆转置，等于 `(A^-1)^T`，也等于 `(A^T)^-1` |
| `I` | 单位矩阵，相当于矩阵运算中的 `1` |

推导中的 `M` 不包含平移。平移会改变位置，但不会改变切线和法线方向；在 4×4 齐次矩阵里，这相当于只取左上角 3×3 部分。

#### 二、线性代数基础：从零开始

##### 2.1 标量、向量与矩阵

- **标量**：单个数字，例如亮度 `0.8`、缩放值 `2`。
- **向量**：一组有顺序的数字，例如三维方向 `[x, y, z]^T`。
- **矩阵**：按行列排列的数字，用于表达旋转、缩放、剪切和坐标空间转换等线性变换。

若 `v` 是列向量，`v' = Mv` 表示矩阵 `M` 对向量 `v` 执行一次线性变换。

以二维非均匀缩放为例：

```text
M = [ 2  0 ]
    [ 0  1 ]
```

它把 X 放大两倍，Y 保持不变。

##### 2.2 点积与垂直

两个向量的点积为：

```text
T · N = tx*nx + ty*ny + tz*nz
```

点积等于零，表示二者垂直：

```text
T · N = 0
```

当 `T`、`N` 都写成列向量时，也可以把点积改写成矩阵乘法：

```text
T · N = T^T N
```

这里左边的 `·` 是向量点积符号；右边的相邻书写表示矩阵乘法。`T^T` 是 `1×3` 行向量，`N` 是 `3×1` 列向量，因此结果是 `1×1`，其唯一元素正好等于点积。

```text
T   = [ tx  ty  tz ]^T
T^T = [ tx  ty  tz ]

T^T N = [ tx  ty  tz ] [ nx ] = tx*nx + ty*ny + tz*nz
                        [ ny ]
                        [ nz ]
```

相邻书写并不总等于点积。例如 `TN^T` 是 `3×1` 乘 `1×3`，结果为 `3×3` 矩阵，称为外积。

##### 2.3 矩阵尺寸与“行乘列”

矩阵乘法的尺寸规则是：

```text
(m×n)(n×p) = (m×p)
```

中间两个尺寸必须相等，结果保留外侧尺寸。若 `C = AB`，则 `C` 的第 `i` 行、第 `j` 列元素，是 `A` 的第 `i` 行与 `B` 的第 `j` 列做点积。

```text
A = [ a  b ]    B = [ e  f ]
    [ c  d ]        [ g  h ]

AB = [ ae+bg  af+bh ]
     [ ce+dg  cf+dh ]
```

矩阵乘法通常不能交换顺序：

```text
AB != BA
```

但可以改变括号位置：

```text
(AB)C = A(BC)
```

##### 2.4 常见的“乘法”不是同一种运算

| 写法 | 名称 | 规则 | 典型结果 |
|------|------|------|----------|
| `kA` | 标量乘矩阵 | 每个元素乘 `k` | 矩阵 |
| `A ⊙ B` | Hadamard 积 | 对应元素相乘，尺寸必须相同 | 矩阵 |
| `AB` | 矩阵乘法 | 行乘列 | 矩阵或向量 |
| `T · N` | 向量点积 | 对应分量乘积求和 | 标量 |
| `TN^T` | 向量外积 | 列向量乘行向量 | 矩阵 |

在数学推导里，`AB` 默认表示矩阵乘法。HLSL 中应使用 `mul(A, B)` 明确表达线性代数乘法，不要把数学里的相邻书写机械替换成逐元素运算。

##### 2.5 转置、单位矩阵与逆矩阵

转置会交换矩阵的行和列：

```text
A   = [ a  b ]    A^T = [ a  c ]
      [ c  d ]          [ b  d ]
```

乘积转置时顺序会反过来：

```text
(AB)^T = B^T A^T
```

单位矩阵 `I` 不改变向量：

```text
Iv = v
```

逆矩阵负责撤销变换：

```text
A^-1 A = A A^-1 = I
```

不是所有矩阵都有逆矩阵。例如某个缩放轴为零时，空间被压扁，原始信息无法恢复，矩阵不可逆。

逆转置有三种等价写法：

```text
A^-T = (A^-1)^T = (A^T)^-1
```

因此真正能相互抵消的是：

```text
A^T A^-T = I
```

而不是一般意义上的 `A A^-T = I`。

#### 三、为什么法线需要逆转置矩阵

法线的关键职责不是“像普通箭头一样跟着模型移动”，而是始终垂直于表面切平面。当模型矩阵包含**非均匀缩放或剪切**时，直接用模型矩阵变换法线会导致：

1. 法线不再垂直于变换后的表面
2. 光照计算出现明显的明暗错误

##### 3.1 完整推导

对象空间中，切线与法线垂直：

```text
T · N = T^T N = 0
```

表面经过模型矩阵 `M` 变换后，切线按普通方向变换：

```text
T' = MT
```

我们要寻找 `N'`，使变换后仍满足：

```text
T' · N' = 0
```

把点积改写成矩阵乘法，并代入 `T' = MT`：

```text
(T')^T N' = 0
(MT)^T N' = 0
T^T M^T N' = 0
```

最后一步使用了 `(AB)^T = B^T A^T`。原始条件是 `T^T N = 0`，为了让变换后的表达式还原成原始表达式，可以令：

```text
M^T N' = N
```

在两边左乘 `(M^T)^-1`：

```text
(M^T)^-1 M^T N' = (M^T)^-1 N
N' = (M^T)^-1 N
```

由于 `(M^T)^-1 = (M^-1)^T = M^-T`，得到：

```text
N' = M^-T N
```

代回验证：

```text
T' · N'
= (MT)^T (M^-T N)
= T^T M^T M^-T N
= T^T I N
= T^T N
= 0
```

这说明逆转置的本质作用是：让切线经历的 `M` 能在点积中被法线一侧的 `M^-T` 抵消，从而保留“点积为零”的垂直关系。

严格来说，垂直条件只决定法线方向，不限制长度，因此任意非零倍数 `cM^-T N` 也保持垂直。渲染中通常取 `c = 1`，并在变换后归一化。

##### 3.2 用未知矩阵验证唯一的标准线性变换（进阶，可跳过）

假设法线使用未知矩阵 `A` 变换，即 `N' = AN`。若要求变换前后的点积对所有 `T`、`N` 都保持一致：

```text
(MT)^T (AN) = T^T N
T^T (M^T A) N = T^T I N
```

要让它对所有向量成立，必须有：

```text
M^T A = I
A = (M^T)^-1 = M^-T
```

因此逆转置是保持该约束的标准线性变换；若只关心归一化后的方向，则还允许整体乘一个非零标量。

##### 3.3 二维数值例子

取一组互相垂直的切线和法线：

```text
T = [ 1,  1 ]^T
N = [ 1, -1 ]^T
T · N = 1*1 + 1*(-1) = 0
```

模型矩阵把 X 放大两倍：

```text
M = [ 2  0 ]
    [ 0  1 ]
```

切线正常变换：

```text
T' = MT = [ 2, 1 ]^T
```

如果法线也错误地直接乘 `M`：

```text
N'wrong = MN = [ 2, -1 ]^T
T' · N'wrong = 2*2 + 1*(-1) = 3
```

点积不再为零。正确的逆转置为：

```text
M^-T = [ 0.5  0 ]
       [ 0    1 ]

N' = M^-T N = [ 0.5, -1 ]^T
T' · N' = 2*0.5 + 1*(-1) = 0
```

法线重新垂直于变换后的表面。

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

从矩阵角度看，若 `M = sR`，其中 `s` 是统一缩放，`R` 是旋转矩阵，则：

```text
M^-T = (1/s)R
```

直接变换得到 `sRN`，逆转置得到 `(1/s)RN`；二者只差整体长度，归一化后方向相同。非均匀缩放时每个轴的比例不同，无法再靠一次归一化修正方向。

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
- 对象→世界法线在非均匀缩放下，可使用行向量右乘 `unity_WorldToObject` 的 3×3 部分，等价于列向量记法的逆转置

#### Unity SRP / URP 中的推荐写法

优先调用 Unity 提供的空间变换函数：

```hlsl
float3 normalWS = TransformObjectToWorldNormal(normalOS);
```

Unity 当前 SRP Core 的一般路径等价于：

```hlsl
float3 normalWS = mul(normalOS, (float3x3)GetWorldToObjectMatrix());
normalWS = SafeNormalize(normalWS);
```

这里看起来是“对象空间法线右乘世界到对象矩阵”，但输出仍然是世界空间法线。原因是 HLSL 的 `mul(vector, matrix)` 把左侧向量视为行向量；行向量右乘 `M^-1`，等价于列向量记法中的 `(M^-1)^T N`。

这只是借用了模型矩阵的逆来实现逆转置，并不是先把法线真的变换到了对象空间。矩阵在内存中按 row-major 还是 column-major 打包，与 `mul` 两个操作数所表达的数学乘法顺序是不同问题，不应混为一谈。

若定义了 `UNITY_ASSUME_UNIFORM_SCALING`，Unity 会走普通方向变换的简化分支。无法保证完整对象到世界矩阵（包括父节点影响）只有均匀缩放时，不应自行启用该假设。

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

> 以上端口顺序是该 ASE 节点场景的实践约定，不应泛化成所有矩阵与方向向量的乘法规则。处理法线时优先使用明确标注 Normal 的空间转换节点，并检查生成的 HLSL 是否使用逆转置路径。

**对象空间 → 世界空间**：使用 `Object To World Matrix` 节点或 `Transform Direction` 节点（模式选 `Object → World`）。

### 参考链接

- [Unity SRP Core - SpaceTransforms.hlsl](https://github.com/Unity-Technologies/Graphics/blob/master/Packages/com.unity.render-pipelines.core/ShaderLibrary/SpaceTransforms.hlsl) - `TransformObjectToWorldNormal` 当前实现与均匀缩放分支
- [Microsoft HLSL mul](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-mul) - `mul(vector, matrix)` 与 `mul(matrix, vector)` 的行列向量语义
- [Unity Built-in Shader 世界空间法线示例](https://docs.unity3d.com/6000.0/Documentation/Manual/built-in-shader-examples-mesh-normals.html) - `UnityObjectToWorldNormal` 的官方使用方式
- [OpenGL Normal Transformation (Lighthouse3D)](https://www.lighthouse3d.com/tutorials/glsl-tutorial/the-normal-matrix/) - 逆转置矩阵原理
- [The Normal Matrix (Scratchapixel)](https://www.scratchapixel.com/lessons/mathematics-physics-for-computer-graphics/geometry/transforming-normals) - 法线变换数学推导

### 相关记录

- [Unity Shader / HLSL 基础知识](./hlsl-semantics-basics.md) - Shader 语义与语法
- [Amplify Shader Editor 架构解析](./amplify-shader-editor-architecture.md) - ASE 节点系统详解

### 验证记录
- [2026-03-25] 初次记录，来源：图形学通用原理 + ASE 实践验证
- [2026-07-14] 扩充：补充面向入门者的线性代数基础、点积与矩阵乘法辨析、逆转置完整推导、二维数值例子及 Unity SRP/HLSL 写法；依据 Unity `SpaceTransforms.hlsl` 与 Microsoft HLSL `mul` 文档复核。
