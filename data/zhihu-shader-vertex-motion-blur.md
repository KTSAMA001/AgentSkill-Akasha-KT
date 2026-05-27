# Shader 案例：顶点运动模糊

**标签**：#unity #shader #graphics #hlsl #performance #reference #zhihu
**来源**：[知乎专栏 - Shader案例:顶点运动模糊](https://zhuanlan.zhihu.com/p/99487181)
**收录日期**：2026-05-27
**来源日期**：未知（知乎安全验证页未暴露）
**更新日期**：2026-05-27
**状态**：⚠️ 待验证
**可信度**：⭐⭐（外部社区文章，已抓取到标题与主要前半段思路，未完整复现）
**适用版本**：Unity Built-in / Unlit Shader；Shader Model 2.0 约束场景

### 概要

这篇知乎文章介绍了一种不依赖后处理的运动模糊近似方案：在顶点着色器中沿运动方向拉伸模型顶点，并用噪声和法线方向遮罩控制偏移强度，用较低成本获得带拖影感的顶点运动模糊。

### 内容

#### 记录范围

本文是对外部知乎文章的合规摘要存档，不完整搬运原文。2026-05-27 通过 `opencli-rs zhihu download` 可读取文章标题和前半段正文，但输出在 C# 脚本 `MotionVertexController` 片段处截断；Jina/网页读取返回知乎登录与安全验证页。因此本记录保留可验证的技术思路、关键公式、抓取限制和原文链接，不声称已完成全文转载。

#### 适用场景

文章针对后处理运动模糊成本较高的情况，提出用顶点形变制造“运动拖影”的视觉近似。这个方法不需要采样相机颜色缓冲，也不需要全屏后处理，更适合对象级别的局部效果、移动端或低成本特效。

限制也很明确：它不是基于速度缓冲的真实屏幕空间运动模糊，效果更接近模型沿运动反方向的随机拉伸。透明、细长、拓扑稀疏或顶点密度不足的模型上可能出现明显形变感。

#### 核心思路

1. 在顶点本地空间做偏移，而不是在片元阶段做屏幕空间模糊。
2. 用 `_Direction.xyz` 表示运动方向，用 `_Direction.w` 表示整体偏移强度。
3. 用 UV 驱动的 hash noise 让每个顶点偏移量不同，避免整体平移。
4. 用法线与运动方向的点积生成遮罩，让背向运动方向的一侧更容易被拉伸。
5. 在 C# 中比较当前帧与上一帧位置，计算运动方向和速度，再实时写入材质参数。

#### 顶点偏移参数

文章先从默认 Unlit Shader 的顶点函数出发，在 `UnityObjectToClipPos(v.vertex)` 前修改模型本地顶点坐标。偏移参数设计为一个四维向量：

```hlsl
_Direction("Direction", vector) = (0, 0, 0, 1)
```

其中 `xyz` 是方向，`w` 是偏移强度。基础偏移形式是：

```hlsl
v.vertex.xyz += _Direction.xyz * _Direction.w;
```

这一步只能让模型整体沿方向移动，还没有拖影效果。

#### 随机偏移

为了让不同顶点的偏移不同，文章提到两种方法：采样噪声贴图，或在 shader 中直接计算噪声。由于文章考虑 Shader Model 2.0 下顶点着色器采样贴图的兼容问题，选择了 hash noise：

```hlsl
float noise = frac(sin(dot(v.uv.xy, float2(12.9898, 78.233))) * 43758.5453);
v.vertex.xyz += _Direction.xyz * _Direction.w * noise;
```

这种写法成本低、实现简单，但噪声和 UV 强绑定；如果模型 UV 分布不均、镜像或重叠，随机拉伸分布也会受到影响。实际项目中可以改用顶点色、额外 UV、对象空间位置 hash 或预烘噪声属性来控制。

#### 局部拉伸遮罩

文章希望物体运动时“正面不拉伸，背部拉伸”。为此使用类似 Lambert 光照的方向遮罩，用顶点法线和运动方向点积区分表面朝向：

```hlsl
fixed NdotD = max(0, dot(v.normal, _Direction));
v.vertex.xyz += _Direction.xyz * _Direction.w * noise * NdotD;
```

这个遮罩的意义是：只有法线与方向满足一定关系的表面才产生偏移。实际使用时需要注意方向定义。如果 `_Direction` 传入的是运动方向，拖影通常应沿反方向偏移；如果传入的是拖影方向，则脚本端应直接传入负速度方向，避免 shader 中含义混乱。

#### C# 驱动逻辑

文章后半段进入 `MotionVertexController` 脚本，用对象当前帧位置与上一帧位置计算运动方向和速度，再把结果写入材质。可验证抓取内容在脚本成员字段处截断，未拿到完整脚本，因此这里不复原完整代码。

项目实现时可以按以下逻辑补齐：

```csharp
Vector3 velocity = (currentPosition - lastPosition) / Mathf.Max(Time.deltaTime, 0.0001f);
Vector3 blurDirection = -velocity.normalized;
float blurStrength = Mathf.Clamp(velocity.magnitude * strengthScale, 0f, maxStrength);
material.SetVector("_Direction", new Vector4(blurDirection.x, blurDirection.y, blurDirection.z, blurStrength));
lastPosition = currentPosition;
```

如果对象有多个材质，需要遍历材质数组或使用 `MaterialPropertyBlock`。在大量对象上使用时，优先考虑 `MaterialPropertyBlock`，避免实例化材质造成额外内存和批处理问题。

#### 实现注意事项

- 法线空间要一致：文章片段直接使用 `v.normal` 与 `_Direction` 点积，意味着 `_Direction` 应处于对象本地空间；如果脚本计算的是世界空间速度，需要转到对象本地空间再传入。
- 拖影方向要一致：视觉上通常沿运动反方向拉伸，脚本端应传入负速度方向，或 shader 中显式取反。
- 顶点密度决定效果细腻程度：低模网格的拉伸会更块状，高顶点密度模型更平滑。
- UV hash 噪声不稳定时，可以改用对象空间位置 hash 或顶点色通道。
- 这类效果是对象级顶点形变，不能替代相机快速移动、遮挡关系和屏幕空间速度带来的真实运动模糊。
- 若对象使用 SRP Batcher 或 GPU Instancing，需要确认材质参数更新方式不会破坏批处理收益。

#### 抓取与版权说明

原流程中的“完整转载保存”与外部版权内容存在冲突。本记录只保留技术摘要、短代码片段、来源链接和可验证抓取状态，不完整复制知乎原文。后续若需要严格保留全文，应改为保存合法授权副本或仅保存私有离线阅读材料，不进入会推送的阿卡西数据层。

### 关键代码

```hlsl
// 顶点本地空间沿方向拉伸，并用噪声与朝向遮罩控制强度。
float noise = frac(sin(dot(v.uv.xy, float2(12.9898, 78.233))) * 43758.5453);
fixed NdotD = max(0, dot(v.normal, _Direction.xyz));
v.vertex.xyz += _Direction.xyz * _Direction.w * noise * NdotD;
o.vertex = UnityObjectToClipPos(v.vertex);
```

```csharp
// 脚本侧思路：由帧间位置差计算拖影方向和强度。
Vector3 velocity = (currentPosition - lastPosition) / Mathf.Max(Time.deltaTime, 0.0001f);
Vector3 blurDirection = -velocity.normalized;
float blurStrength = Mathf.Clamp(velocity.magnitude * strengthScale, 0f, maxStrength);
material.SetVector("_Direction", new Vector4(blurDirection.x, blurDirection.y, blurDirection.z, blurStrength));
```

### 参考链接

- [Shader案例:顶点运动模糊 - 知乎](https://zhuanlan.zhihu.com/p/99487181) - 原始文章

### 相关记录

- [VR 相机壳层特效替代后处理](./vr-camera-shell-effects-without-post-processing.md) - 同样关注用几何/材质方案替代昂贵后处理
- [渲染管线概览](./rendering-pipeline-overview.md) - Lambert 光照、顶点/片元阶段等基础概念

### 验证记录

- [2026-05-27] 初次记录。已执行 `git pull origin main`；重复检测未发现 `99487181` 或同题记录。`opencli-rs zhihu download https://zhuanlan.zhihu.com/p/99487181` 可读取标题和前半段正文，但在 C# 脚本处截断；Jina/网页读取遇到知乎登录/安全验证。本文按合规摘要方式入库，未完整搬运原文，未实测 shader 效果。

