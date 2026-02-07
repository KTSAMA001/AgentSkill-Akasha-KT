# CI/CD 经验

> 持续集成/持续部署相关经验
> 
> 包含：GitHub Actions、Jenkins、自动化测试、部署流程等

---

## VitePress（静态站）在宝塔 Nginx 部署：403/404、路径迁移、Webhook 自动更新踩坑记录

**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-02-07
**标签**：#vitepress #nginx #宝塔 #alicloud #alinux3 #webhook #git #部署 #mermaid #pm2
**状态**：✅ 已验证
**适用版本**：VitePress 1.x + Nginx 1.26 + 宝塔面板 9.x + Alibaba Cloud Linux 3

**问题/场景**：

- 将 VitePress 项目（AkashaRecord-Web）部署到阿里云服务器，站点 `akasha.ktsama.top` 通过宝塔面板管理 Nginx
- 初期出现 404/403：
	- 站点根目录路径从 `/root/...` 迁移到 `/www/wwwroot/...` 后仍然异常
	- 某些路径（如 `/experiences/ai/`、`/experiences/anthropic/`）访问返回 403
- 后续又遇到：
	- `dnf` 被错误的 Nginx 官方源干扰（把系统识别成“centos/3”，repodata 404）
	- `git` 报 `detected dubious ownership`（安全策略）
	- VitePress 配置启用 Mermaid 时因括号缺失导致构建失败

**解决方案/结论**：

1) **确保 Nginx `root` 指向 VitePress 构建产物目录**

Nginx 配置核心点：

- `root` 必须指向 `.vitepress/dist`
- `index index.html;`

2) **403 的根因：目录存在但没有 index.html，Nginx 禁止目录列表**

错误日志典型表现：

- `directory index of ".../dist/experiences/ai/" is forbidden`

这表示 Nginx 命中了一个真实目录（`/experiences/ai/`），但目录下缺少 `index.html`。

**推荐修复（更稳定）**：在内容同步阶段自动补齐每个分类目录的 `index.md`，让 VitePress 自动生成对应目录的 `index.html`。

实现方式：修改站点工程的同步脚本，在同步完 `experiences/knowledge/ideas` 后，递归检查子目录：

- 如果某目录没有 `index.md`，则自动生成一个“目录页”，列出该目录下的所有 `.md` 文件链接

这样无需污染原始笔记仓库，也能保证 Web 访问 `/xxx/` 永远有落地页。

3) **目录权限修复**（常规但必要）

```bash
chmod -R 755 /www/wwwroot/AkashaRecord-Web
chown -R www:www /www/wwwroot/AkashaRecord-Web
/www/server/nginx/sbin/nginx -s reload
```

4) **Git `dubious ownership`（安全策略）**

当使用 `root` 操作、但仓库目录属主是 `www`（或反过来）时，Git 会拒绝执行（防止目录劫持）。

解决：将目录加入 Git 信任列表

```bash
git config --global --add safe.directory /www/wwwroot/AkashaRecord-Web
git config --global --add safe.directory /www/wwwroot/AkashaRecord-Web/.akasha-repo
```

5) **Alibaba Cloud Linux 3 上 dnf 被错误 repo 搞坏**

现象：源地址类似 `http://nginx.org/packages/centos/3/x86_64/...` 返回 404，导致 `dnf makecache` 失败。

处理：禁用错误 repo（改名为 `.bak`），再清缓存：

```bash
dnf clean all
dnf makecache
```

6) **Mermaid 支持**

~~VitePress 默认不渲染 Mermaid，需要引入 `vitepress-plugin-mermaid`。~~

**更正（2026-02-07）**：`vitepress-plugin-mermaid@2.0.17` 与 VitePress 1.6.4 存在严重兼容性问题，会导致：

- 启动时报 `Failed to resolve dependency: vitepress > @vue/devtools-api, present in 'optimizeDeps.include'`
- 页面白屏（JS 无法加载）
- 即使手动安装 `@vue/devtools-api` 和 `@vueuse/core` 也无法解决

**最终方案**：卸载 `vitepress-plugin-mermaid`，改用客户端 Mermaid 组件（自定义 Vue 组件 + `mermaid` npm 包），在 VitePress 主题中注册为全局组件。

7) **`npx` 缓存陷阱导致白屏**

直接运行 `npx vitepress dev` 时，npx 可能使用全局缓存中的旧版/残缺 VitePress（路径指向 `~/.npm/_npx/...`），其 `optimizeDeps` 配置与本地 `node_modules` 不匹配，导致客户端 JS 无法加载（白屏）。

诊断方法：`curl -6 http://localhost:<port>/` 查看 HTML 中的 `<script>` 路径，如果指向 `/@fs/Users/.../.npm/_npx/...` 就说明用的是 npx 缓存版本。

**解决**：
- 使用 `npm run dev`（通过 package.json scripts 调用，自动用本地版本）
- 或直接 `./node_modules/.bin/vitepress dev`
- **不要**单独用 `npx vitepress dev`

8) **国内服务器访问 GitHub 不稳定**

阿里云等国内服务器拉取 GitHub 仓库经常超时或失败。

解决方案之一——配置 GitHub 镜像加速：

```bash
git config --global url."https://mirror.ghproxy.com/https://github.com/".insteadOf "https://github.com/"
```

同步脚本中也应添加容错逻辑：git pull 失败时不要中断流程，使用本地缓存继续构建。

9) **sync 脚本的 `dubious ownership` 问题**

`.akasha-repo`（由 sync 脚本克隆的阿卡西记录仓库缓存）同样会被 Git 安全策略拦截。每次手动 `git config --global --add safe.directory` 太麻烦。

**最终方案**：在 sync 脚本中，git pull 之前自动执行：

```javascript
execSync(`git config --global --add safe.directory "${AKASHA_LOCAL}"`, { stdio: 'pipe' })
```

这样无论在哪台服务器部署，都不需要手动处理。

10) **sync 脚本 pull 时的本地修改冲突**

现象：`.akasha-repo` 中存在未提交的本地修改（可能是上一次构建过程中的残留），导致 `git pull` 报错：
```
error: Your local changes to the following files would be overwritten by merge
```

虽然 fallback 到 `git fetch + reset --hard` 可以解决，但每次都走 fallback 不优雅。

**最终方案**：pull 前先丢弃所有本地修改：

```javascript
execSync('git checkout . && git clean -fd', { cwd: AKASHA_LOCAL, stdio: 'pipe' })
execSync('git pull --ff-only', { cwd: AKASHA_LOCAL, stdio: 'pipe', timeout: 60000 })
```

11) **GITHUB_MIRROR 环境变量支持**

直接硬编码 `https://github.com/...` 在国内服务器必定失败。

**方案**：sync 脚本支持 `GITHUB_MIRROR` 环境变量，自动替换 URL 前缀：

```javascript
const GITHUB_MIRROR = process.env.GITHUB_MIRROR || ''
const AKASHA_REPO = GITHUB_MIRROR
  ? ORIGIN.replace('https://github.com/', GITHUB_MIRROR)
  : ORIGIN
```

每次同步前还自动更新 remote URL（`git remote set-url origin`），避免 `.akasha-repo` 中缓存旧地址。

服务器使用：`GITHUB_MIRROR="https://ghfast.top/" npm run build`

12) **Mermaid 代码块自动渲染**

单独注册 `<Mermaid code="...">` 全局组件不够——标准的 ` ```mermaid ` 代码块不会被拦截。

**方案**：在 VitePress `markdown.config` 中重写 `fence` 规则，拦截 `info === 'mermaid'` 的代码块，将内容 Base64 编码后传给 `<MermaidRenderer>` 组件。

注意 `atob()` 不支持 UTF-8 多字节字符（中文），解码时必须用 `TextDecoder`：

```javascript
const binary = atob(encoded)
const bytes = Uint8Array.from(binary, c => c.charCodeAt(0))
const code = new TextDecoder('utf-8').decode(bytes)
```

13) **Webhook 自动构建（pm2 守护）**

webhook 服务使用 express 监听 3721 端口，接收 GitHub push 事件后自动执行 sync + build。

要点：
- 使用 `pm2 start server/webhook.mjs --name akasha-webhook` 守护运行
- `pm2 save && pm2 startup` 实现开机自启
- Nginx 已配置 `/webhook` 路径代理到 `127.0.0.1:3721`
- webhook 脚本中使用 `./node_modules/.bin/vitepress build` 而非 `npx`（避免缓存陷阱）
- 需在 GitHub 两个仓库（AkashaRecord-Web、AgentSkill-Akasha-KT）都配 webhook

**验证记录**：

- 2026-02-07 通过 Nginx error.log 定位 403 根因（目录缺 index）
- 2026-02-07 通过同步脚本自动生成目录 index.md 的策略稳定解决
- 2026-02-07 `vitepress-plugin-mermaid` 导致白屏，已移除并改用客户端组件方案
- 2026-02-07 发现 `npx` 缓存陷阱，改用本地 `node_modules/.bin/vitepress`
- 2026-02-07 服务器端 GitHub 拉取失败属于网络问题，脚本容错逻辑生效
- 2026-02-07 dubious ownership 根因确认：sync 脚本克隆的 .akasha-repo 也需要 safe.directory，已在脚本中自动处理
- 2026-02-07 pull 冲突根因：.akasha-repo 有本地残留修改，pull 前加 git checkout + clean 彻底解决
- 2026-02-07 GITHUB_MIRROR 环境变量验证通过，服务器通过 gh-proxy.com 镜像成功拉取
- 2026-02-07 Mermaid 代码块渲染：markdown-it fence 拦截 + Base64 传参 + TextDecoder 解码，中文流程图正常显示
- 2026-02-07 pm2 启动 webhook 服务成功，GitHub webhook 配置待完成
- 2026-02-07 GitHub webhook 两个仓库均配置完成（HTTP、JSON、push only），delivery 返回 200
- 2026-02-07 发现 webhook.mjs 没有 git pull 自身代码（鸡蛋问题），已修复并手动首次部署
- 2026-02-07 VPBackdrop 遮罩残留问题确认为 VitePress 断点不匹配 bug，已添加 CSS 修复

**备注**：

- 诊断 403/404 时，优先看：
	- `/www/wwwlogs/<domain>.error.log`
	- `ls -l` 验证 dist 内是否存在 `index.html`
- 如果某路径既可能是“目录”也可能是“同名 html”（cleanUrls 场景），`try_files` 顺序会影响行为；但最稳妥还是让目录真实存在 `index.html`。

14) **Webhook "鸡蛋问题"：自更新 git pull**

webhook.mjs 接收 push event 后执行 sync + build，但脚本**自身的更新**也需要 git pull。如果 webhook.mjs 代码有变更，旧版本不会自动拉取新代码。

**方案**：在 webhook.mjs 的 runBuild() 开头加 Step 0：

```javascript
// Step 0: 更新 Web 仓库自身代码
execSync('git checkout . && git clean -fd', { cwd: PROJECT_ROOT })
execSync('git pull --ff-only', { cwd: PROJECT_ROOT, timeout: 60000 })
```

**鸡蛋问题**：首次部署这个修改时，服务器上运行的是旧版 webhook.mjs（没有 Step 0），push 触发的 webhook 用的还是旧代码。必须**手动**在服务器执行一次 `git pull && pm2 restart akasha-webhook`，之后就能自举了。

15) **VitePress VPBackdrop 遮罩断点不匹配（已知 Bug）**

窄屏时点开 sidebar，???屏时点开 sidebar，???屏时点开 sidebarＺ???屏时点开 sidebar，???屏时点开 sidebar?960px** 切换为桌面常驻模式，但 `.VPBackdrop` 的 CSS `display: none` 设在 **1280px**。且 sidebar 的 JS（`useSidebarControl`）没有 resize 监听来自动关闭状态（对比 `useNav` 有 `closeScreenOnTabletWindow`）。

**修复**：自定义 CSS 将 VPBackdrop 隐藏断点对齐到 960px：

```css
@media (min-width: 960px) {
  .VPBackdrop {
    display: none !important;
  }
}
```

**状态**：✅ 已验证

16) **Safari position:fixed 元素在窗口 resize 时重绘延迟**

VPBackdrop 使用 `position: fixed; inset: 0` 覆盖视口。Safari 拉伸窗口时 fixed 元素的尺寸重绘跟不上窗口变化速度，导致遮罩右下角边缘短暂漏出内容。

**方案**：用 `box-shadow` 超大扩展替代依赖元素尺寸的覆盖：

```css
.VPBackdrop {
  box-shadow: 0 0 0 200vmax var(--vp-backdrop-bg-color) !important;
}
```

200vmax = 视口最大维度的200倍，无论窗口多大拉多快都不可能露出。`box-shadow` 是渲染层效果，不依赖元素 inset 尺寸的重绘。

**状态**：⚠️ 待验证
