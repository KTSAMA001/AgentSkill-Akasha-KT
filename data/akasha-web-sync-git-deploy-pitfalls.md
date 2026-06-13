# Akasha Web 同步脚本与 Git 部署坑

**标签**：#web #tools #git #experience #deployment #cicd #github-actions #troubleshooting
**来源**：KTSAMA 实践经验
**收录日期**：2026-02-07
**来源日期**：2026-02-07
**更新日期**：2026-06-13
**状态**：✅ 已验证
**可信度**：⭐⭐⭐⭐ (实践验证)
**适用版本**：VitePress 1.x + Git + Alibaba Cloud Linux 3

### 概要

Akasha Web 部署时，Git `dubious ownership`、国内服务器拉取 GitHub 不稳定、`.akasha-repo` 本地残留修改、`npx` 缓存版本不一致，都会导致同步或构建异常。同步脚本应内置 safe.directory、清理本地修改、镜像 URL 和本地 VitePress 调用策略。

### 内容

#### Git dubious ownership

当使用 `root` 操作、但仓库目录属主是 `www`（或反过来）时，Git 会拒绝执行，防止目录劫持。

处理方式是将目录加入 Git 信任列表：

```bash
git config --global --add safe.directory /www/wwwroot/AkashaRecord-Web
git config --global --add safe.directory /www/wwwroot/AkashaRecord-Web/.akasha-repo
```

`.akasha-repo` 由 sync 脚本克隆，也会被 Git 安全策略拦截。手动配置容易遗漏，最终方案是在 sync 脚本中，git pull 前自动执行：

```javascript
execSync(`git config --global --add safe.directory "${AKASHA_LOCAL}"`, { stdio: 'pipe' })
```

#### sync 脚本 pull 时的本地修改冲突

现象：

```text
error: Your local changes to the following files would be overwritten by merge
```

根因是 `.akasha-repo` 中存在未提交的本地修改，可能来自上一次构建残留。

最终方案：pull 前先丢弃所有本地修改。

```javascript
execSync('git checkout . && git clean -fd', { cwd: AKASHA_LOCAL, stdio: 'pipe' })
execSync('git pull --ff-only', { cwd: AKASHA_LOCAL, stdio: 'pipe', timeout: 60000 })
```

#### 国内服务器访问 GitHub 不稳定

阿里云等国内服务器拉取 GitHub 仓库经常超时或失败。

方案之一是配置 GitHub 镜像加速：

```bash
git config --global url."https://mirror.ghproxy.com/https://github.com/".insteadOf "https://github.com/"
```

同步脚本也应添加容错逻辑：git pull 失败时不要中断流程，使用本地缓存继续构建。

#### GITHUB_MIRROR 环境变量支持

直接硬编码 GitHub URL 在国内服务器上容易失败。sync 脚本可支持 `GITHUB_MIRROR` 环境变量，自动替换 URL 前缀：

```javascript
const GITHUB_MIRROR = process.env.GITHUB_MIRROR || ''
const AKASHA_REPO = GITHUB_MIRROR
  ? ORIGIN.replace('https://github.com/', GITHUB_MIRROR)
  : ORIGIN
```

每次同步前还应自动更新 remote URL，避免 `.akasha-repo` 中缓存旧地址。

服务器使用示例：

```bash
GITHUB_MIRROR="https://ghfast.top/" npm run build
```

#### npx 缓存陷阱导致白屏

直接运行 `npx vitepress dev` 时，npx 可能使用全局缓存中的旧版或残缺 VitePress，其 `optimizeDeps` 配置与本地 `node_modules` 不匹配，导致客户端 JS 无法加载。

诊断方法：

- 查看页面 HTML 中的 `<script>` 路径。
- 如果指向用户目录下的 npm npx 缓存，说明用的是 npx 缓存版本。

解决：

- 使用 `npm run dev`，通过 package.json scripts 调用本地版本。
- 或直接 `./node_modules/.bin/vitepress dev`。
- 不要单独用 `npx vitepress dev`。

### 关键代码

见“内容”中的 `safe.directory`、pull 前清理、`GITHUB_MIRROR` 和本地 VitePress 调用策略。

### 相关记录

- [VitePress 宝塔 Nginx 部署 403/404 与 cleanUrls 刷新修复](./vitepress-nginx-deploy-403-cleanurls.md) - Nginx 静态站层部署问题。
- [Akasha Webhook PM2 守护与 HTTPS 反向代理](./akasha-webhook-pm2-https-proxy.md) - webhook 自动构建层问题。
- [Alibaba Cloud Linux 3 Nginx 源导致 dnf 404（Legacy）](./alibaba-cloud-linux-nginx-dnf-repo-pitfall-legacy.md) - 原聚合记录中未归入 Git 同步主题的服务器包源残留问题。

### 验证记录

- [2026-02-07] 发现 `npx` 缓存陷阱，改用本地 `node_modules/.bin/vitepress`。
- [2026-02-07] dubious ownership 根因确认：sync 脚本克隆的 `.akasha-repo` 也需要 safe.directory，已在脚本中自动处理。
- [2026-02-07] pull 冲突根因：`.akasha-repo` 有本地残留修改，pull 前加 git checkout + clean 解决。
- [2026-02-07] `GITHUB_MIRROR` 环境变量验证通过，服务器通过镜像成功拉取。
- [2026-06-13] 结构维护：从旧聚合记录拆分，未重新验证原技术结论。

---
