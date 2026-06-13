# PBR / BRDF 基本要点

**标签**：#graphics #shader #knowledge #pbr #brdf
**来源**：《Physically Based Rendering》、《Real-Time Rendering》
**收录日期**：2026-02-01
**更新日期**：2026-06-13
**状态**：📘 有效
**可信度**：⭐⭐⭐⭐⭐ (权威著作 + 学术标准)
**适用版本**：通用实时渲染

### 概要

BRDF 描述光从某方向入射后向某方向反射的比例；PBR 则把材质与光照建模约束到更接近物理规律的框架中。

### 内容

#### BRDF

BRDF（Bidirectional Reflectance Distribution Function）描述“光从某方向入射后，向某方向反射的比例”。它是理解现代材质和反射模型的基础概念。

#### PBR

PBR（Physically Based Rendering）是一套更贴近物理规律的材质与光照建模方法，常见关注点包括：

- 能量守恒。
- 菲涅尔效应。
- 粗糙度对高光分布的影响。
- 金属与非金属材质的反射差异。

#### 工程侧记忆

- **金属度/粗糙度工作流**：金属更接近“高反射 + 有色反射”，非金属更接近“漫反射为主 + 无色镜面反射”。
- **粗糙度**：越粗糙，高光越宽、越暗；越光滑，高光越尖锐。
- **Fresnel（菲涅尔）**：掠射角更亮、反射更强；正视角更暗、反射更弱。

### 相关记录

- [基础光照模型](./basic-lighting-models.md) - Lambert / Phong / Blinn-Phong 基础。
- [PBR/BRDF 理论基础](./pbr-cook-torrance-brdf-theory.md) - 更完整的 PBR 理论记录。

### 验证记录

- [2026-04-15] 旧聚合记录结构修复：补齐模板必填章节，未改动原结论。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---
