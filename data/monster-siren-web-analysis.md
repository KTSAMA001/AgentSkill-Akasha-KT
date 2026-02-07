## 塞壬唱片官网 (Monster Siren) 深度技术与设计分析

**分类**：design > web-analysis
**标签**：#web #design #knowledge #arknights #react #cyberpunk
**来源**：https://monster-siren.hypergryph.com
**来源日期**：2026-02-08
**收录日期**：2026-02-08
**可信度**：⭐⭐⭐⭐ (实地分析/逆向研究)
**状态**：📘 有效

### 定义/概念

塞壬唱片 MSR (Monster Siren Records) 是《明日方舟》世界观中虚构的音乐发行商，其官网既是真实的音乐发布平台，又完整还原了泰拉世界的"终端系统"体验。网站由上海鹰角网络科技有限公司运营。网站贯彻了"沉浸式世界观重构"的设计理念，将功能性与叙事性完美结合，是游戏 IP 衍生站点的标杆案例。

### 原理/详解

#### 1. 技术架构
- **前端框架**：React + UmiJS (企业级应用框架)
- **状态管理**：DVA (基于 Redux + Redux-Saga)，用于管理全局播放器状态、播放列表等。
- **渲染策略**：SSR (服务端渲染) + 客户端 Hydration。HTML 中内嵌 `window.g_initialData` 提升首屏速度与 SEO。
- **样式方案**：CSS Modules，类名采用 Hash 形式（如 `.icon___3HqBj`）实现样式隔离，避免冲突。
- **API 设计**：RESTful JSON API，统一响应结构 `{code, msg, data}`。
- **资源分发**：自建 CDN (`web.hycdn.cn`) 托管图片、音频与静态资源。

#### 2. 视觉设计系统
- **配色体系**：
  - **基底**：`#09090b` ~ `#141516` (极暗灰黑)，模拟未点亮的屏幕或深邃背景。
  - **强调**：青白色系 / 高亮白，模拟终端屏幕的发光字符。
  - **层级**：通过透明度 (`rgba`) 区分主次信息，而非灰度。
- **字体排印**：
  - **Bender**：主西文字体，方形无衬线，棱角分明，提供极强的工业/军工氛围。
  - **Geometos**：用于特殊标题的装饰性几何字体。
  - **SourceHanSansCN** (思源黑体)：中文正文，中性且易读。
- **材质与纹理**：
  - **毛玻璃 (Frosted Glass)**：`backdrop-filter: blur(7px) brightness(55%)`。降低背景亮度是关键，使前景文字在模糊背景上依然清晰锐利。
  - **扫描线/噪点**：全局叠加纹理图层，模拟信号干扰和 CRT 显示器质感。
  - **暗角 (Vignette)**：模拟老式显示屏边缘的光线衰减。

#### 3. 页面结构与叙事
- **首页 (Home)**：全屏 Hero Banner，打字机效果 Slogan ("a world familiarly unknown")。Canvas 绘制的 Logo Loading 动画将等待时间转化为仪式感。
- **音乐页 (Music)**：左侧专辑瀑布流/网格，右侧常驻播放列表抽屉。
- **动向页 (Info)**：顶部 `BREAKING NEWS` 无限循环跑马灯，图文混排新闻卡片。
- **联系页 (Contact)**：彻底的角色扮演 (RP)。电话栏显示 "We do not use that"，地址为 "#Middle of nowhere, Terra"。拒绝打破第四面墙。
- **关于页 (About)**：中英双语平行排版，严谨的企业介绍口吻，增强虚构机构的真实感。

#### 4. 交互与动效
- **自定义光标**：全站替换原生光标，使用 SVG 精灵图，包含默认、指针(Hover)、播放等状态，强化操作系统的代入感。
- **Glitch 故障效果**：Logo 和关键元素使用 SVG Clip-path 裁剪多份，配合 CSS 动画进行随机位移和错位，模拟数字信号故障。
- **微交互**：Hover 效果多为亮度提升、缩放或边框发光，过渡时长通常为 `.3s`，手感顺滑且有机械阻尼感。
- **无缝滚动**：用于公告跑马灯，通过 DOM 复制实现视觉上的无限循环。

### 关键点

- **沉浸式重构**：完全摒弃浏览器原生 UI（滚动条、按钮、光标），重构所有交互元素，让用户感觉在使用一个独立的"泰拉终端"而非网页。
- **叙事即界面**：文案、报错、空白页（Empty State）都是世界观的一部分。
- **工业美学一致性**：字体是氛围的核心。Bender 等工业字体的运用瞬间确立了硬核科幻基调。
- **功能服务于体验**：音乐播放是核心功能，但被包裹在极具仪式感的设计中。固定底部播放器与右侧抽屉的设计既实用又符合"控制台"的直觉。

### 示例

**1. CSS 无缝跑马灯 (Ticker)**
```css
@keyframes breakingLoop {
  0% { transform: translateX(0); }
  to { transform: translateX(-100%); }
}
/* 容器宽度足够大，内部包含两组相同的文本内容 */
.ticker-content {
  display: flex;
  animation: breakingLoop 20s linear infinite;
}
```

**2. SVG Glitch 故障遮罩原理**
```html
<defs>
  <!-- 定义不规则裁剪区域 -->
  <clipPath id="mask-glitch-1">
    <polygon points="-41,103 546,103 587,0 0,0"></polygon>
  </clipPath>
</defs>
<!-- 应用裁剪并位移 -->
<g clip-path="url(#mask-glitch-1)" class="glitch-layer-1">...</g>
<g clip-path="url(#mask-glitch-2)" class="glitch-layer-2">...</g>
```

### 相关知识

- [明日方舟工业风 UI](./arknights-ui-industrial-style.md)
- Web Audio API 与流式播放
- UmiJS 框架应用架构
- CSS `backdrop-filter` 兼容性与性能
