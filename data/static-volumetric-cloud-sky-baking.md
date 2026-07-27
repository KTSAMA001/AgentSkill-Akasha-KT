# 静态体积云天空的高质量离线烘焙

**标签**：#unity #graphics #shader #rendering #experience
**来源**：项目实践总结；Guerrilla Games Nubis/Horizon 与 EA Frostbite 公开技术资料
**收录日期**：2026-07-27
**来源日期**：2015-08 / 2016-07 / 2026-07-27（实践验证）
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐（公开技术资料 + Unity 编辑器内多视角实践验证）
**适用版本**：Unity 2021.3+；Built-in/URP 天空盒路径

### 概要

当云层、天气和时间段不需要运行时更新时，可以把高成本体积云积分完全移到 Editor：以球壳云层、Perlin–Worley 密度、Beer–Lambert 消光和光线积分生成高质量静态天空，Player 只保留一次二维天空纹理采样。高分辨率烘焙应分瓦片执行，以规避单次超长 GPU Draw 导致的 Windows TDR。

### 内容

#### 适用边界

该方案适合以下目标：

- 云形、天气状态与时间段是离散预设，不要求连续实时演化。
- 太阳可以作为静态天空的一部分；闪电等瞬态发光单独叠加。
- 离线烘焙优先追求画质，运行时优先追求低采样和低带宽。

如果运行时需要连续改变云量、太阳高度、风场或云层自阴影，应改用实时/半实时体积云，而不是把大量状态硬烘焙成纹理集合。

#### 云层几何：使用球壳而不是平面层

以行星半径、相机海拔、云底和云顶定义两个同心球。视线分别与球壳求交，得到进入/离开云层的距离。

球壳的主要收益：

- 地平线附近不会像无限平面层那样出现不受控的超长行程。
- 云层厚度随观察方向自然变化，地平线尺度更可信。
- 与全天空方向编码配合时没有六个面各自建模造成的边界差异。

#### 密度建模

一套可维护的密度函数可拆成四层：

1. 垂直剖面：云底淡入、主体保持、云顶淡出。
2. 基础形状：Perlin/FBM 提供连续大尺度结构，Worley 提供团块与空腔特征。
3. 天气覆盖率：低频二维天气噪声调制局部云量阈值，形成晴区和阴区。
4. 细节侵蚀：高频 FBM 主要从云边扣除密度，避免把整个云体变成均匀噪声。

“总体云量”和“密度倍率”不可混为一谈：总体云量决定某处是否生成云，密度倍率决定已有云体的光学厚度。

#### 光照模型

离线画质可使用以下组合：

- Beer–Lambert：`T = exp(-sigmaT * distance)`，计算视线和太阳方向的透射率。
- Light March：从每个有效云样本朝太阳方向积分遮光。
- 双叶 Henyey–Greenstein：分别近似前向与后向散射。
- Powder Effect：加强受光云边和蓬松感。
- 多重散射近似：抬亮厚云内部，避免单次散射造成死黑。

这些近似并非严格路径追踪，但在静态天空烘焙中能以可控成本提供明显优于单层噪声贴图的体积感。

#### 瓦片化避免 TDR

高分辨率下，“视线步数 × 光照步数 × 每像素子样本 × 像素数”会迅速放大。把整张目标纹理一次 Draw 完成，可能让 Windows 判断 GPU 无响应并触发 TDR。

工程上可使用固定小瓦片（例如 128×128）逐块渲染，再写入同一 HDR CPU 纹理。关键约束是：

- 每块仍使用整张纹理的全局 UV，而不是局部 0～1 UV。
- 抖动种子使用全局像素坐标，避免瓦片边界改变采样序列。
- 所有瓦片使用完全一致的云、太阳和曝光参数。

#### 推荐调参顺序

1. 先调总体云量和区域变化，确定晴/阴分布。
2. 调基础噪声频率，确定大云团尺寸。
3. 调细节频率与侵蚀，确定云边形状。
4. 调密度倍率、云底和云顶，确定厚度与压迫感。
5. 调太阳方向、颜色、视半径和相位函数。
6. 最后才提高视线步数、光照步数和每像素子样本。

预览阶段可从 `512 / 96 / 10 / 1~2`（分辨率 / 视线步数 / 光照步数 / 子样本）开始；确认构图后再提高到 `1024+ / 192+ / 24+ / 4+`。

#### 验证方式

静态天空不能只看一个镜头。至少检查：

- 迎光：太阳圆盘、高光肩部、云边剪白。
- 侧光：云体结构和中间调层次。
- 背光：环境光是否过灰或暗部死黑。
- 天顶：平滑渐变、量化色带和噪声。

### 关键代码

```hlsl
// 视线和光照步进共同决定主要离线成本。
float stepLength = (endDistance - startDistance) / max((float)viewSteps, 1.0);
float transmittance = 1.0;

for (int i = 0; i < viewSteps && transmittance > 0.002; i++)
{
    float density = SampleCloudDensity(samplePosition);
    float sigmaT = density * densityMultiplier;
    float stepT = exp(-sigmaT * stepLength);
    // LightTransmittance 内部沿太阳方向执行 lightSteps 次积分。
    accumulatedLight += transmittance * (1.0 - stepT) * LightTransmittance(samplePosition);
    transmittance *= stepT;
    samplePosition += rayDirection * stepLength;
}
```

### 参考链接

- [The Real-time Volumetric Cloudscapes of Horizon: Zero Dawn](https://advances.realtimerendering.com/s2015/The%20Real-time%20Volumetric%20Cloudscapes%20of%20Horizon%20-%20Zero%20Dawn%20-%20ARTR.pdf) - Perlin–Worley 云密度与实时体积云基础。
- [Nubis: Authoring Real-Time Volumetric Cloudscapes with the Decima Engine](https://www.guerrilla-games.com/read/nubis-authoring-real-time-volumetric-cloudscapes-with-the-decima-engine) - 云层创作与天气控制。
- [Physically Based Sky, Atmosphere and Cloud Rendering in Frostbite](https://media.contentapi.ea.com/content/dam/eacom/frostbite/files/s2016-pbs-frostbite-sky-clouds-new.pdf) - 天空、云层散射与光照思路。

### 相关记录

- [色带（Color Banding）与抖动（Dithering）知识](./color-banding-dither.md) - 静态天空平滑渐变的输出量化问题。
- [URP 天空盒 Shader 机制与常见问题](./urp-skybox-notes.md) - Unity 天空盒渲染路径注意事项。

### 验证记录

- [2026-07-27] 在 Unity 编辑器中完成 512×512、192 视线步、24 光照步、4 子样本的瓦片化烘焙，并从迎光、侧光、背光、天顶四个方向检查；高负载单 Draw 曾触发编辑器/GPU 故障，改为 128×128 瓦片后稳定完成。

---
